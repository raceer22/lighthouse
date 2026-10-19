import textwrap
from pathlib import Path

from blender_runner import run_in_blender

FIXTURES = Path(__file__).parent / "fixtures"

HELPERS = """
import lighthouse
lighthouse.register()
empty_scene()
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
group = bpy.data.collections.new("Group")
bpy.context.scene.collection.children.link(group)
key = add_light("Key")
fill = add_light("Fill")
lamp = bpy.data.objects.new("Lamp", bpy.data.lights.new("Lamp", "POINT"))
group.objects.link(lamp)
bpy.context.view_layer.update()
solo = bpy.context.scene.lighthouse_solo

def targets():
    return [[t.object.name if t.object else None, t.collection.name if t.collection else None]
            for t in solo.targets]
"""


def run(snippet):
    return run_in_blender(HELPERS + textwrap.dedent(snippet))


def test_soloing_a_light_or_a_group_stores_one_target():
    result = run("""
        bpy.ops.lighthouse.solo_light(name="Key", library="")
        light = targets()
        bpy.ops.lighthouse.solo_group(name="Group", library="")
        report({"light": light, "group": targets()})
    """)

    assert result == {"light": [["Key", None]], "group": [[None, "Group"]]}


def test_soloing_a_second_light_replaces_the_target():
    result = run("""
        bpy.ops.lighthouse.solo_light(name="Key", library="")
        bpy.ops.lighthouse.solo_light(name="Fill", library="")
        report(targets())
    """)

    assert result == [["Fill", None]]


def test_ending_solo_clears_the_targets():
    result = run("""
        bpy.ops.lighthouse.solo_light(name="Key", library="")
        bpy.ops.lighthouse.solo_light(name="Key", library="")
        report([solo.active, targets()])
    """)

    assert result == [False, []]


def open_old_file(name, snippet):
    """Open a file saved mid-solo by Lighthouse 1.3 (solo.light / solo.group pointers) on Blender 4.2."""
    return run_in_blender(textwrap.dedent(f"""
        import lighthouse
        lighthouse.register()
        bpy.ops.wm.open_mainfile(filepath={str(FIXTURES / name)!r})
        solo = bpy.context.scene.lighthouse_solo
        def hidden():
            return sorted(o.name for o in bpy.data.objects if o.hide_viewport or o.hide_render)
    """) + textwrap.dedent(snippet))


def test_an_old_mid_solo_file_moves_its_target_into_the_list_and_exits_cleanly():
    result = {
        name: open_old_file(name, """
            loaded = {"targets": [[t.object.name if t.object else None, t.collection.name if t.collection else None]
                                  for t in solo.targets],
                      "label": lighthouse.solo_label(solo), "hidden": hidden()}
            bpy.ops.lighthouse.exit_solo()
            report(loaded | {"after exit": hidden()})
        """)
        for name in ("solo_light_1_3.blend", "solo_group_1_3.blend")
    }

    assert result == {
        "solo_light_1_3.blend": {"targets": [["Key", None]], "label": "Key", "hidden": ["Fill", "Lamp"],
                                 "after exit": []},
        "solo_group_1_3.blend": {"targets": [[None, "Group"]], "label": "Group", "hidden": ["Fill", "Key"],
                                 "after exit": []},
    }
