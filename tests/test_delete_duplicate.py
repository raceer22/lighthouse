import textwrap

from blender_runner import RECORDER, run_in_blender, run_in_blender_with_reports
from test_light_menu import BUTTON, HELPERS, LINKED

SELECTION = """
spot = new_light("Spot")
lights = bpy.data.collections.new("Lights")
bpy.context.scene.collection.children.link(lights)
lamp = bpy.data.objects.new("Lamp", bpy.data.lights.new("Lamp", "POINT"))
lights.objects.link(lamp)
layer.update()

def select(*objs):
    for obj in layer.objects:
        obj.select_set(obj in objs)

def names():
    return sorted(o.name for o in bpy.data.objects)
"""


def run(snippet, setup=""):
    return run_in_blender(HELPERS + SELECTION + setup + textwrap.dedent(snippet))


def test_delete_on_a_selected_light_removes_the_whole_selection_and_says_how_many():
    result = run("""
        select(key, fill, spot)
        label = [entry[2] for entry in menu_for(row("Fill"))[:-1] if entry[1] == "lighthouse.delete_lights"]
        outcome = bpy.ops.lighthouse.delete_lights(name="Fill", library="")
        report({"label": label, "outcome": sorted(outcome), "left": names()})
    """, RECORDER + BUTTON)

    assert result == {"label": ["Delete 3 Lights"], "outcome": ["FINISHED"], "left": ["Lamp"]}


def test_delete_on_an_unselected_light_removes_only_that_light():
    result = run("""
        select(key, fill, spot)
        label = [entry[2] for entry in menu_for(row("Lamp"))[:-1] if entry[1] == "lighthouse.delete_lights"]
        bpy.ops.lighthouse.delete_lights(name="Lamp", library="")
        report({"label": label, "left": names()})
    """, RECORDER + BUTTON)

    assert result == {"label": ["Delete"], "left": ["Fill", "Key", "Spot"]}


def test_duplicate_copies_the_light_data_and_duplicate_linked_shares_it_in_the_same_collection():
    result = run("""
        select()
        bpy.ops.lighthouse.duplicate_lights(name="Lamp", library="")
        copy = layer.objects.active
        full = {"name": copy.name, "in": [c.name for c in copy.users_collection],
                "new data": copy.data != lamp.data, "selected": [o.name for o in layer.objects if o.select_get()]}
        bpy.ops.lighthouse.duplicate_lights(name="Lamp", library="", linked=True)
        twin = layer.objects.active
        report({"full": full, "linked": {"in": [c.name for c in twin.users_collection],
                                         "same data": twin.data == lamp.data}})
    """)

    assert result == {
        "full": {"name": "Lamp.001", "in": ["Lights"], "new data": True, "selected": ["Lamp.001"]},
        "linked": {"in": ["Lights"], "same data": True},
    }


def test_duplicating_the_selection_selects_the_copies_with_the_clicked_lights_copy_active():
    result = run("""
        select(key, fill)
        bpy.ops.lighthouse.duplicate_lights(name="Fill", library="")
        report({"selected": sorted(o.name for o in layer.objects if o.select_get()),
                "active": layer.objects.active.name})
    """)

    assert result == {"selected": ["Fill.001", "Key.001"], "active": "Fill.001"}


def test_deleting_a_light_with_shared_data_leaves_the_other_object_and_the_data():
    result = run("""
        twin = new_light("Twin", key.data)
        select()
        bpy.ops.lighthouse.delete_lights(name="Key", library="")
        report({"twin": twin.name, "data": twin.data.name, "data users": twin.data.users})
    """)

    assert result == {"twin": "Twin", "data": "Key", "data users": 1}


def test_deleting_a_soloed_light_then_exiting_solo_restores_the_others():
    result = run("""
        select()
        bpy.ops.lighthouse.solo_light(name="Key", library="")
        bpy.ops.lighthouse.delete_lights(name="Key", library="")
        outcome = bpy.ops.lighthouse.exit_solo()
        report({"outcome": sorted(outcome), "hidden": [o.hide_viewport for o in (fill, spot, lamp)]})
    """)

    assert result == {"outcome": ["FINISHED"], "hidden": [False, False, False]}


def test_a_duplicate_made_during_solo_is_shown():
    result = run("""
        select()
        bpy.ops.lighthouse.solo_light(name="Key", library="")
        bpy.ops.lighthouse.duplicate_lights(name="Fill", library="")
        report(layer.objects.active.hide_viewport)
    """)

    assert result is False


def test_a_library_light_in_the_selection_is_skipped_and_reported():
    value, warnings = run_in_blender_with_reports(HELPERS + SELECTION + LINKED + textwrap.dedent("""
        select(key, rim)
        bpy.ops.lighthouse.delete_lights(name="Key", library="")
        deleted = names()
        select(rim)
        outcome = bpy.ops.lighthouse.delete_lights(name="Rim", library=rim.library.filepath)
        report({"left": deleted, "all read-only": sorted(outcome)})
    """), level="Info")
    _, warning = run_in_blender_with_reports(HELPERS + SELECTION + LINKED + textwrap.dedent("""
        select(rim)
        bpy.ops.lighthouse.delete_lights(name="Rim", library=rim.library.filepath)
        report(None)
    """), level="Warning")

    assert value == {"left": ["Fill", "Lamp", "Rim", "Spot"], "all read-only": ["CANCELLED"]}
    assert warnings == ["Deleted 1 light, skipped 1 read-only"]
    assert warning == ["Rim is read-only (linked from a library)"]
