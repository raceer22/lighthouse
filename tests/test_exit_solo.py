from blender_runner import run_in_blender
from test_mute_solo import FLAGS, GROUPS, NESTED, NESTED_ORIGINAL, SHOWN, HIDDEN


def test_exit_solo_after_deleting_the_soloed_light_restores_everything_else_and_label_reads_deleted():
    states = run_in_blender(FLAGS + GROUPS + NESTED + """
        from lighthouse.lights import solo_label
        solo = bpy.context.scene.lighthouse_solo
        bpy.ops.lighthouse.solo_light(name="Bulb")
        named = solo_label(solo)
        bpy.data.objects.remove(bpy.data.objects["Bulb"])
        bpy.context.view_layer.update()
        deleted = solo_label(solo)
        result = bpy.ops.lighthouse.exit_solo()
        report({"named": named, "deleted": deleted, "result": sorted(result),
                "active": solo.active, **state()})
    """)

    expected_objects = {k: v for k, v in NESTED_ORIGINAL["objects"].items() if k != "Bulb"}
    assert states == {
        "named": "Bulb",
        "deleted": "deleted",
        "result": ["FINISHED"],
        "active": False,
        "objects": expected_objects,
        "collections": NESTED_ORIGINAL["collections"],
    }


def test_exit_solo_is_unavailable_when_solo_is_off():
    polls = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        add_light("Key")
        before = bpy.ops.lighthouse.exit_solo.poll()
        bpy.ops.lighthouse.solo_light(name="Key")
        during = bpy.ops.lighthouse.exit_solo.poll()
        bpy.ops.lighthouse.solo_light(name="Key")
        report({"before": before, "during": during, "after": bpy.ops.lighthouse.exit_solo.poll()})
    """)

    assert polls == {"before": False, "during": True, "after": False}


MUTE_SCENE = """
        import lighthouse
        lighthouse.register()
        empty_scene()
        add_light("Key")
        fill = add_light("Fill")
        fill.hide_render = fill.hide_viewport = True
"""


def test_unmuting_a_light_during_solo_keeps_it_visible_after_unsolo():
    states = run_in_blender(FLAGS + MUTE_SCENE + """
        bpy.ops.lighthouse.solo_light(name="Key")
        bpy.ops.lighthouse.mute_light(name="Fill")
        bpy.ops.lighthouse.solo_light(name="Key")
        report(flags())
    """)

    assert states == {"Key": SHOWN, "Fill": SHOWN}


def test_muting_the_soloed_light_keeps_it_muted_after_unsolo():
    states = run_in_blender(FLAGS + MUTE_SCENE + """
        bpy.ops.lighthouse.solo_light(name="Key")
        bpy.ops.lighthouse.mute_light(name="Key")
        bpy.ops.lighthouse.exit_solo()
        report(flags())
    """)

    assert states == {"Key": HIDDEN, "Fill": HIDDEN}


def test_hiding_a_group_during_solo_keeps_it_hidden_and_untouched_groups_are_left_alone():
    states = run_in_blender(FLAGS + GROUPS + """
        import lighthouse
        lighthouse.register()
        empty_scene()
        for collection in list(bpy.data.collections):
            bpy.data.collections.remove(collection)
        interior = new_collection("Interior")
        interior.hide_render = True
        props = new_collection("Props")
        move_to(add_light("Lamp"), interior)
        move_to(add_light("Prop"), props)

        bpy.ops.lighthouse.solo_light(name="Lamp")
        soloed = collection_flags()
        bpy.ops.lighthouse.hide_group(name="Interior")
        bpy.ops.lighthouse.hide_group(name="Props")
        bpy.ops.lighthouse.exit_solo()
        report({"soloed": soloed, "unsoloed": collection_flags()})
    """)

    assert states == {
        "soloed": {"Interior": SHOWN, "Props": SHOWN},
        "unsoloed": {"Interior": HIDDEN, "Props": HIDDEN},
    }
