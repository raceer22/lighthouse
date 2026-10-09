from blender_runner import run_in_blender

FLAGS = """
        def flags():
            return {
                o.name: {"render": o.hide_render, "viewport": o.hide_viewport}
                for o in bpy.context.view_layer.objects
            }
"""


def test_mute_hides_only_that_light_and_pressing_again_unhides_it():
    states = run_in_blender(FLAGS + """
        import lighthouse
        lighthouse.register()
        empty_scene()
        add_light("Key")
        add_light("Fill")

        bpy.ops.lighthouse.mute_light(name="Key")
        muted = flags()
        bpy.ops.lighthouse.mute_light(name="Key")
        report({"muted": muted, "unmuted": flags()})
    """)

    hidden = {"render": True, "viewport": True}
    shown = {"render": False, "viewport": False}
    assert states == {
        "muted": {"Key": hidden, "Fill": shown},
        "unmuted": {"Key": shown, "Fill": shown},
    }


SCENE_ABC = """
        import lighthouse
        lighthouse.register()
        empty_scene()
        add_light("A")
        add_light("B").hide_render = True
        add_light("C").hide_viewport = True
        add_light("D")
"""

ORIGINAL = {
    "A": {"render": False, "viewport": False},
    "B": {"render": True, "viewport": False},
    "C": {"render": False, "viewport": True},
    "D": {"render": False, "viewport": False},
}


def test_solo_hides_every_other_light_and_unsolo_restores_their_exact_flags():
    states = run_in_blender(FLAGS + SCENE_ABC + """
        bpy.ops.lighthouse.solo_light(name="A")
        soloed = flags()
        bpy.ops.lighthouse.solo_light(name="A")
        report({"soloed": soloed, "unsoloed": flags()})
    """)

    hidden = {"render": True, "viewport": True}
    assert states == {
        "soloed": {"A": {"render": False, "viewport": False}, "B": hidden, "C": hidden, "D": hidden},
        "unsoloed": ORIGINAL,
    }


def test_switching_solo_then_unsoloing_restores_the_original_flags_not_the_intermediate_ones():
    states = run_in_blender(FLAGS + SCENE_ABC + """
        bpy.ops.lighthouse.solo_light(name="A")
        bpy.ops.lighthouse.solo_light(name="B")
        switched = flags()
        bpy.ops.lighthouse.solo_light(name="B")
        report({"switched": switched, "unsoloed": flags()})
    """)

    hidden = {"render": True, "viewport": True}
    assert states == {
        "switched": {"A": hidden, "B": {"render": False, "viewport": False}, "C": hidden, "D": hidden},
        "unsoloed": ORIGINAL,
    }


def test_deleting_lights_during_solo_does_not_break_unsolo_and_the_rest_are_restored():
    states = run_in_blender(FLAGS + SCENE_ABC + """
        bpy.ops.lighthouse.solo_light(name="A")
        bpy.data.objects.remove(bpy.data.objects["C"])
        bpy.ops.lighthouse.solo_light(name="B")
        bpy.data.objects.remove(bpy.data.objects["B"])
        bpy.context.view_layer.update()
        bpy.ops.lighthouse.solo_light(name="D")
        bpy.ops.lighthouse.solo_light(name="D")
        report(flags())
    """)

    assert states == {name: ORIGINAL[name] for name in ("A", "D")}


def test_light_added_during_solo_gets_its_own_flags_back_after_switching_and_unsoloing():
    states = run_in_blender(FLAGS + SCENE_ABC + """
        bpy.ops.lighthouse.solo_light(name="A")
        add_light("E").hide_render = True
        bpy.ops.lighthouse.solo_light(name="B")
        switched = flags()["E"]
        bpy.ops.lighthouse.solo_light(name="B")
        report({"switched": switched, "unsoloed": flags()})
    """)

    assert states == {
        "switched": {"render": True, "viewport": True},
        "unsoloed": {**ORIGINAL, "E": {"render": True, "viewport": False}},
    }


GROUPS = """
        def new_collection(name, parent=None):
            collection = bpy.data.collections.new(name)
            (parent or bpy.context.scene.collection).children.link(collection)
            return collection

        def move_to(obj, collection):
            for owner in list(obj.users_collection):
                owner.objects.unlink(obj)
            collection.objects.link(obj)
            bpy.context.view_layer.update()
            return obj

        def collection_flags():
            return {
                c.name: {"render": c.hide_render, "viewport": c.hide_viewport}
                for c in bpy.data.collections
            }

        def state():
            return {"objects": flags(), "collections": collection_flags()}

        def visible():
            layer = bpy.context.view_layer
            return sorted(o.name for o in layer.objects if o.visible_get(view_layer=layer) and not o.hide_render)
"""

# Studio (render hidden) / Lamps (both hidden) / Inner (viewport hidden) holds Bulb;
# Lamps holds Lantern; Key is in the Scene Collection, Fill is render hidden.
NESTED = """
        import lighthouse
        lighthouse.register()
        empty_scene()
        for collection in list(bpy.data.collections):
            bpy.data.collections.remove(collection)
        studio = new_collection("Studio")
        studio.hide_render = True
        lamps = new_collection("Lamps", studio)
        lamps.hide_render = lamps.hide_viewport = True
        inner = new_collection("Inner", lamps)
        inner.hide_viewport = True
        props = new_collection("Props")
        props.hide_viewport = True
        move_to(add_light("Bulb"), inner).hide_viewport = True
        move_to(add_light("Lantern"), lamps)
        move_to(add_light("Prop"), props)
        add_light("Key")
        add_light("Fill").hide_render = True
"""

SHOWN = {"render": False, "viewport": False}
HIDDEN = {"render": True, "viewport": True}
NESTED_ORIGINAL = {
    "objects": {
        "Bulb": {"render": False, "viewport": True},
        "Lantern": SHOWN,
        "Prop": SHOWN,
        "Key": SHOWN,
        "Fill": {"render": True, "viewport": False},
    },
    "collections": {
        "Studio": {"render": True, "viewport": False},
        "Lamps": HIDDEN,
        "Inner": {"render": False, "viewport": True},
        "Props": {"render": False, "viewport": True},
    },
}


def test_soloing_a_light_in_a_hidden_group_shows_it_and_unsolo_restores_every_flag():
    states = run_in_blender(FLAGS + GROUPS + NESTED + """
        bpy.ops.lighthouse.solo_light(name="Bulb")
        soloed = {"visible": visible(), **state()}
        bpy.ops.lighthouse.solo_light(name="Bulb")
        report({"soloed": soloed, "unsoloed": state()})
    """)

    assert states["soloed"]["visible"] == ["Bulb"]
    assert states["soloed"]["collections"] == {
        "Studio": SHOWN, "Lamps": SHOWN, "Inner": SHOWN, "Props": {"render": False, "viewport": True},
    }
    assert states["unsoloed"] == NESTED_ORIGINAL


def test_group_solo_shows_only_its_lights_sub_collections_included_and_unsolo_restores():
    states = run_in_blender(FLAGS + GROUPS + NESTED + """
        bpy.ops.lighthouse.solo_group(name="Lamps")
        soloed = {"visible": visible(), **state()}
        bpy.ops.lighthouse.solo_group(name="Lamps")
        report({"soloed": soloed, "unsoloed": state()})
    """)

    assert states["soloed"]["visible"] == ["Bulb", "Lantern"]
    assert states["soloed"]["objects"]["Bulb"] == SHOWN
    assert states["soloed"]["collections"]["Inner"] == SHOWN
    assert states["unsoloed"] == NESTED_ORIGINAL


def test_switching_light_to_group_to_light_keeps_earlier_groups_unhidden_and_unsolo_restores_the_start():
    states = run_in_blender(FLAGS + GROUPS + NESTED + """
        bpy.ops.lighthouse.solo_light(name="Key")
        bpy.ops.lighthouse.solo_group(name="Lamps")
        bpy.ops.lighthouse.solo_light(name="Prop")
        switched = {"visible": visible(), **state()}
        bpy.ops.lighthouse.solo_light(name="Prop")
        report({"switched": switched, "unsoloed": state()})
    """)

    assert states["switched"]["visible"] == ["Prop"]
    assert states["switched"]["collections"] == {"Studio": SHOWN, "Lamps": SHOWN, "Inner": SHOWN, "Props": SHOWN}
    assert states["unsoloed"] == NESTED_ORIGINAL


def test_renaming_the_soloed_light_another_light_and_a_hidden_collection_during_solo_still_restores_them():
    states = run_in_blender(FLAGS + GROUPS + NESTED + """
        bpy.ops.lighthouse.solo_light(name="Bulb")
        bpy.data.objects["Bulb"].name = "Bulb.renamed"
        bpy.data.objects["Fill"].name = "Fill.renamed"
        bpy.data.collections["Lamps"].name = "Lamps.renamed"
        bpy.ops.lighthouse.solo_light(name="Bulb.renamed")
        report(state())
    """)

    assert states["objects"]["Bulb.renamed"] == NESTED_ORIGINAL["objects"]["Bulb"]
    assert states["objects"]["Fill.renamed"] == NESTED_ORIGINAL["objects"]["Fill"]
    assert states["collections"]["Lamps.renamed"] == NESTED_ORIGINAL["collections"]["Lamps"]


def test_deleting_a_snapshotted_light_and_collection_during_solo_does_not_break_unsolo():
    states = run_in_blender(FLAGS + GROUPS + NESTED + """
        bpy.ops.lighthouse.solo_light(name="Bulb")
        bpy.ops.lighthouse.solo_light(name="Prop")
        bpy.data.objects.remove(bpy.data.objects["Fill"])
        bpy.data.collections.remove(bpy.data.collections["Props"])
        bpy.context.view_layer.update()
        bpy.ops.lighthouse.solo_light(name="Lantern")
        bpy.ops.lighthouse.solo_light(name="Lantern")
        report(state())
    """)

    assert states == {
        "objects": {name: f for name, f in NESTED_ORIGINAL["objects"].items() if name not in ("Fill", "Prop")},
        "collections": {name: f for name, f in NESTED_ORIGINAL["collections"].items() if name != "Props"},
    }


def test_unsolo_after_saving_and_reopening_mid_solo_restores_the_original_state(tmp_path):
    states = run_in_blender(FLAGS + GROUPS + NESTED + f"""
        bpy.ops.lighthouse.solo_light(name="Key")
        bpy.ops.lighthouse.solo_group(name="Lamps")
        path = {str(tmp_path / "scene.blend")!r}
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.read_homefile(use_factory_startup=True)
        bpy.ops.wm.open_mainfile(filepath=path)
        bpy.ops.lighthouse.solo_group(name="Lamps")
        report(state())
    """)

    assert states == NESTED_ORIGINAL


def test_row_state_reports_which_light_is_muted_and_which_is_soloed():
    states = run_in_blender("""
        import lighthouse
        from lighthouse.lights import row_state
        lighthouse.register()
        empty_scene()
        add_light("Key")
        add_light("Fill")
        add_light("Rim")
        bpy.ops.lighthouse.mute_light(name="Rim")
        bpy.ops.lighthouse.solo_light(name="Key")
        scene, layer = bpy.context.scene, bpy.context.view_layer
        key = row_state(layer.objects["Key"], layer, scene)
        rim = row_state(layer.objects["Rim"], layer, scene)
        bpy.ops.lighthouse.solo_light(name="Key")
        unsoloed = row_state(layer.objects["Key"], layer, scene)
        report({
            "key": [key.muted, key.soloed],
            "rim": [rim.muted, rim.soloed],
            "key_unsoloed": [unsoloed.muted, unsoloed.soloed],
        })
    """)

    assert states == {
        "key": [False, True],
        "rim": [True, False],
        "key_unsoloed": [False, False],
    }


def test_only_the_soloed_target_reports_itself_soloed_whether_light_or_group():
    states = run_in_blender(FLAGS + GROUPS + NESTED + """
        from lighthouse.lights import group_soloed, row_state
        scene, layer = bpy.context.scene, bpy.context.view_layer

        def soloed():
            return {
                "Lamps": group_soloed(scene, bpy.data.collections["Lamps"]),
                "Inner": group_soloed(scene, bpy.data.collections["Inner"]),
                "Bulb": row_state(layer.objects["Bulb"], layer, scene).soloed,
            }

        bpy.ops.lighthouse.solo_group(name="Lamps")
        group = soloed()
        bpy.ops.lighthouse.solo_light(name="Bulb")
        light = soloed()
        bpy.ops.lighthouse.solo_light(name="Bulb")
        report({"group": group, "light": light, "unsoloed": soloed()})
    """)

    assert states == {
        "group": {"Lamps": True, "Inner": False, "Bulb": False},
        "light": {"Lamps": False, "Inner": False, "Bulb": True},
        "unsoloed": {"Lamps": False, "Inner": False, "Bulb": False},
    }
