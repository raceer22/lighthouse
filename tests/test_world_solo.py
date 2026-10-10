import textwrap

from blender_runner import RECORDER, run_in_blender

SETUP = """
    import lighthouse
    lighthouse.register()
    from lighthouse.lights import world_setup
    empty_scene()
    key = add_light("Key")
    fill = add_light("Fill")
    fill.hide_render = fill.hide_viewport = True
    solo = bpy.context.scene.lighthouse_solo
    background = world_setup(bpy.context.scene).background

    def flags():
        return {o.name: [o.hide_render, o.hide_viewport] for o in (key, fill)}
"""

ORIGINAL = {"Key": [False, False], "Fill": [True, True]}
DARK = {"Key": [True, True], "Fill": [True, True]}


def run(snippet):
    return run_in_blender(textwrap.dedent(SETUP) + textwrap.dedent(snippet))


def test_lamp_solo_leaves_the_world_mute_alone():
    result = run("""
        out = []
        for muted in (False, True):
            background.mute = muted
            bpy.ops.lighthouse.solo_light(name="Key")
            during = background.mute
            bpy.ops.lighthouse.solo_light(name="Key")
            out.append([during, background.mute])
        report(out)
    """)

    assert result == [[False, False], [True, True]]


def test_solo_world_darkens_every_lamp_unmutes_the_world_and_a_second_press_restores():
    result = run("""
        out = []
        for muted in (False, True):
            background.mute = muted
            first = sorted(bpy.ops.lighthouse.solo_world())
            during = [flags(), background.mute, solo.active, solo.world_soloed]
            bpy.ops.lighthouse.solo_world()
            out.append([first, during, flags(), background.mute, solo.active])
        report(out)
    """)

    assert result == [
        [["FINISHED"], [DARK, False, True, True], ORIGINAL, False, False],
        [["FINISHED"], [DARK, False, True, True], ORIGINAL, True, False],
    ]


def test_switching_from_world_solo_to_a_lamp_remutes_the_world_and_exit_restores_lights():
    result = run("""
        background.mute = True
        bpy.ops.lighthouse.solo_world()
        bpy.ops.lighthouse.solo_light(name="Key")
        switched = [background.mute, solo.world_soloed, solo.light.name]
        bpy.ops.lighthouse.exit_solo()
        report([switched, flags(), background.mute, solo.active])
    """)

    assert result == [[True, False, "Key"], ORIGINAL, True, False]


def test_mute_world_during_world_solo_survives_unsolo():
    result = run("""
        bpy.ops.lighthouse.solo_world()
        bpy.ops.lighthouse.mute_world()
        during = background.mute
        bpy.ops.lighthouse.exit_solo()
        report([during, background.mute, flags()])
    """)

    assert result == [True, True, ORIGINAL]


def test_mute_world_during_lamp_solo_is_a_plain_mute_kept_after_unsolo():
    result = run("""
        bpy.ops.lighthouse.solo_light(name="Key")
        bpy.ops.lighthouse.mute_world()
        bpy.ops.lighthouse.solo_light(name="Key")
        report([background.mute, flags()])
    """)

    assert result == [True, ORIGINAL]


def test_solo_world_without_a_world_only_hides_the_lights():
    result = run("""
        bpy.context.scene.world = None
        first = sorted(bpy.ops.lighthouse.solo_world())
        during = flags()
        bpy.ops.lighthouse.solo_world()
        report([first, during, flags(), solo.active])
    """)

    assert result == [["FINISHED"], DARK, ORIGINAL, False]


def test_unsolo_restores_lights_after_the_world_node_is_deleted():
    result = run("""
        bpy.ops.lighthouse.solo_world()
        tree = bpy.context.scene.world.node_tree
        tree.nodes.remove(background)
        outcome = sorted(bpy.ops.lighthouse.exit_solo())
        report([outcome, flags(), solo.active])
    """)

    assert result == [["FINISHED"], ORIGINAL, False]


def test_label_and_exit_description_name_the_world():
    result = run("""
        from lighthouse.lights import solo_label
        bpy.ops.lighthouse.solo_world()
        op = bpy.types.LIGHTHOUSE_OT_exit_solo
        report([solo_label(solo), op.description(bpy.context, None)])
    """)

    assert result[0] == "World"
    assert result[1].startswith("Exit Solo (World)")


def test_panel_draws_solo_next_to_mute_pressed_during_world_solo():
    log = run_in_blender(RECORDER + textwrap.dedent(SETUP) + textwrap.dedent("""
        before = drawn(bpy.types.LIGHTHOUSE_PT_world.draw)
        bpy.ops.lighthouse.solo_world()
        report([before, drawn(bpy.types.LIGHTHOUSE_PT_world.draw)])
    """))

    names = [entry[1] for entry in log[1] if entry[0] == "operator"]
    assert names[:2] == ["lighthouse.mute_world", "lighthouse.solo_world"]
    assert ["operator", "lighthouse.solo_world", "", "pressed"] in log[1]
    assert ["operator", "lighthouse.solo_world", ""] in log[0]
