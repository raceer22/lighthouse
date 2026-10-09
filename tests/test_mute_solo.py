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
