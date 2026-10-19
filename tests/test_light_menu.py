import textwrap

from blender_runner import RECORDER, run_in_blender

HELPERS = """
import lighthouse
lighthouse.register()
empty_scene()
layer = bpy.context.view_layer

def new_light(name, data=None):
    obj = bpy.data.objects.new(name, data or bpy.data.lights.new(name, "POINT"))
    bpy.context.scene.collection.objects.link(obj)
    return obj

key = new_light("Key")
fill = new_light("Fill")
layer.update()
"""


LINKED = """
import os, tempfile
library = os.path.join(tempfile.mkdtemp(), "library.blend")
rim = bpy.data.objects.new("Rim", bpy.data.lights.new("Rim", "POINT"))
bpy.data.libraries.write(library, {rim})
bpy.data.objects.remove(rim)
with bpy.data.libraries.load(library, link=True) as (source, target):
    target.objects = ["Rim"]
rim = target.objects[0]
bpy.context.scene.collection.objects.link(rim)
layer.update()
"""


# A light row's name button as context.button_operator sees it in the right-click menu.
BUTTON = """
def button(identifier, **props):
    return type("Props", (), {"bl_rna": type("RNA", (), {"identifier": identifier})(), **props})()

def row(name, library=""):
    return button("LIGHTHOUSE_OT_select_light", name=name, library=library)

def menu_for(button_operator):
    return drawn(lighthouse.draw_light_menu, FakeContext(button_operator=button_operator))
"""


def run(snippet, setup=""):
    return run_in_blender(HELPERS + setup + textwrap.dedent(snippet))


def test_a_light_name_button_gets_rename_frame_and_solo_above_a_separator():
    result = run("""
        before = menu_for(row("Key"))
        bpy.ops.lighthouse.solo_light(name="Key", library="")
        report({"Key": before, "Key soloed": menu_for(row("Key"))[2]})
    """, RECORDER + BUTTON)

    assert result == {
        "Key": [
            ["operator", "lighthouse.rename_light", "Rename", {"name": "Key", "library": ""}],
            ["operator", "lighthouse.select_light", "Frame", {"name": "Key", "library": "", "action": "FRAME"}],
            ["operator", "lighthouse.solo_light", "Solo", {"name": "Key", "library": ""}],
            ["separator"],
        ],
        "Key soloed": ["operator", "lighthouse.solo_light", "Exit Solo", {"name": "Key", "library": ""}],
    }


def test_other_buttons_get_no_light_entries_and_the_group_menu_still_works():
    result = run("""
        header = button("LIGHTHOUSE_OT_set_active_collection", name="", library="")
        report({
            "header": menu_for(header),
            "no operator": menu_for(None),
            "missing light": menu_for(row("Nope")),
            "group menu": len(drawn(lighthouse.draw_group_menu, FakeContext(button_operator=header))),
        })
    """, RECORDER + BUTTON)

    assert result == {"header": [], "no operator": [], "missing light": [], "group menu": 4}


def test_rename_changes_only_the_object_name_even_with_shared_light_data():
    result = run("""
        twin = new_light("Twin", key.data)
        bpy.ops.lighthouse.rename_light(name="Key", library="", new_name="Hero")
        report({"objects": sorted(o.name for o in bpy.data.objects), "data": key.data.name,
                "twin data": twin.data.name})
    """)

    assert result == {"objects": ["Fill", "Hero", "Twin"], "data": "Key", "twin data": "Key"}


def test_solo_from_the_menu_solos_the_clicked_light_and_again_ends_it():
    result = run("""
        bpy.ops.lighthouse.solo_light(name="Fill", library="")
        soloed = [key.hide_viewport, fill.hide_viewport]
        bpy.ops.lighthouse.solo_light(name="Fill", library="")
        report([soloed, [key.hide_viewport, fill.hide_viewport]])
    """)

    assert result == [[True, False], [False, False]]


def test_a_library_light_gets_rename_disabled_but_frame_and_solo_enabled():
    result = run("""
        report([[entry[2], entry[-1] == "disabled"] for entry in menu_for(row("Rim", rim.library.filepath))[:3]])
    """, LINKED + RECORDER + BUTTON)

    assert result == [["Rename", True], ["Frame", False], ["Solo", False]]
