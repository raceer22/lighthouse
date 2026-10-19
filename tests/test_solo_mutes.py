import textwrap

from blender_runner import run_in_blender
from test_additive_solo import HELPERS


def run(snippet):
    return run_in_blender(HELPERS + textwrap.dedent("""
        def mute(name):
            bpy.ops.lighthouse.mute_light(name=name, library="")

        def solo_group(extend=False):
            bpy.ops.lighthouse.solo_group(name="Group", library="", extend=extend)
    """) + textwrap.dedent(snippet))


def test_a_light_muted_during_solo_stays_hidden_when_another_target_is_added():
    result = run("""
        solo_group()
        mute("G1")
        solo_light("B", extend=True)
        report(shown())
    """)

    assert result == ["B", "G2"]


def test_unmuting_it_again_shows_it_and_later_adds_keep_it_shown():
    result = run("""
        solo_group()
        mute("G1")
        solo_light("B", extend=True)
        mute("G1")
        unmuted = shown()
        solo_light("A", extend=True)
        report([unmuted, shown()])
    """)

    assert result == [["B", "G1", "G2"], ["A", "B", "G1", "G2"]]


def test_a_mute_survives_replacing_the_targets_and_adding_its_group_back():
    result = run("""
        solo_group()
        mute("G1")
        solo_light("B")
        solo_group(extend=True)
        report(shown())
    """)

    assert result == ["B", "G2"]


def test_exit_solo_keeps_the_mute_and_a_new_solo_starts_with_the_flag_cleared():
    result = run("""
        solo_group()
        mute("G1")
        bpy.ops.lighthouse.exit_solo()
        after_exit = g1.hide_viewport and g1.hide_render
        solo_group()
        report([after_exit, shown()])
    """)

    assert result == [True, ["G1", "G2"]]
