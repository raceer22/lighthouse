import textwrap

from blender_runner import RECORDER, run_in_blender, run_installed
from test_light_menu import BUTTON, HELPERS

THREE = """
spot = new_light("Spot")
for obj in (key, fill, spot):
    obj.select_set(True)

def mute(obj, hide=True):
    obj.hide_render = obj.hide_viewport = hide

def muted():
    return [obj.hide_viewport and obj.hide_render for obj in (key, fill, spot)]

def mute_label(name):
    return [entry[2] for entry in menu_for(row(name))[:-1] if entry[1] == "lighthouse.mute_lights"]
"""


def run(snippet):
    return run_in_blender(HELPERS + RECORDER + BUTTON + THREE + textwrap.dedent(snippet))


def test_mute_on_a_selected_light_mutes_the_selection_and_its_label_says_how_many():
    result = run("""
        label = mute_label("Spot")
        bpy.ops.lighthouse.mute_lights(name="Spot", library="")
        report({"label": label, "muted": muted()})
    """)

    assert result == {"label": ["Mute 3 Lights"], "muted": [True, True, True]}


def test_a_muted_light_is_never_selected_so_unmute_acts_on_it_alone():
    # Blender deselects a light as soon as hide_viewport is set, so a mixed selection never holds a
    # muted light: right-clicking one gets plain "Unmute" for that light only.
    result = run("""
        mute(key)
        label = mute_label("Key")
        mute(fill)
        bpy.ops.lighthouse.mute_lights(name="Key", library="")
        report({"label": label, "key selected": key.select_get(), "muted": muted()})
    """)

    assert result == {"label": ["Unmute"], "key selected": False, "muted": [False, True, False]}


def test_mute_on_one_unselected_light_says_plain_mute():
    result = run("""
        key.select_set(False)
        report(mute_label("Key"))
    """)

    assert result == ["Mute"]


def test_mute_from_the_menu_during_solo_survives_exit_solo():
    result = run("""
        bpy.ops.lighthouse.solo_light(name="Key", library="")
        bpy.ops.lighthouse.mute_lights(name="Key", library="")
        bpy.ops.lighthouse.exit_solo()
        report(muted())
    """)

    assert result == [True, False, False]


PRESETS = """
empty_scene()
point = add_light("Point")
other = add_light("Other")
third = add_light("Third")
for obj in (point, other, third):
    obj.data.energy = 7
other.select_set(True)
third.select_set(True)

def powers():
    return [obj.data.energy for obj in (point, other, third)]
"""


def run_presets(snippet, user_dir, setup=""):
    return run_installed(setup + PRESETS + textwrap.dedent(snippet), user_dir)[0]


def test_apply_preset_from_the_menu_follows_the_selection_rule(tmp_path):
    result = run_presets("""
        bpy.ops.lighthouse.apply_preset(preset='USER:60W Bulb', name="Point", library="")
        unselected = powers()
        for obj in (point, other, third):
            obj.data.energy = 7
        bpy.ops.lighthouse.apply_preset(preset='USER:60W Bulb', name="Other", library="")
        report({"unselected": unselected, "selected": powers()})
    """, tmp_path)

    assert result == {"unselected": [60, 7, 7], "selected": [7, 60, 60]}


def test_the_presets_panel_apply_still_acts_on_the_selection(tmp_path):
    result = run_presets("""
        bpy.ops.lighthouse.apply_preset(preset='USER:60W Bulb')
        report(powers())
    """, tmp_path)

    assert result == [7, 60, 60]


def test_the_apply_preset_submenu_lists_presets_aimed_at_the_clicked_light(tmp_path):
    result = run_presets("""
        import sys
        lighthouse = sys.modules["bl_ext.user_default.lighthouse"]
        entries = drawn(lighthouse.LIGHTHOUSE_MT_apply_preset.draw, FakeContext(lighthouse_light=point))
        report([entry for entry in entries if entry[2] == "60W Bulb"])
    """, tmp_path, RECORDER)

    assert result == [["operator", "lighthouse.apply_preset", "60W Bulb",
                       {"preset": "USER:60W Bulb", "name": "Point", "library": ""}]]
