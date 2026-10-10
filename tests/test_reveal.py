import textwrap

from blender_runner import run_in_blender

HELPERS = """
import lighthouse
from lighthouse.lights import LightEntry, list_entries
lighthouse.register()

def new_collection(name, parent=None):
    collection = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(collection)
    return collection

def move_to(obj, *collections):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    for collection in collections:
        collection.objects.link(obj)
    bpy.context.view_layer.update()

def make_active(obj):
    for other in bpy.context.view_layer.objects:
        other.select_set(False)
    if obj is not None:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def listed_lights():
    return [e.obj.name for e in list_entries(bpy.context.view_layer) if isinstance(e, LightEntry)]

def fold_everything():
    for collection in bpy.data.collections:
        collection.lighthouse_collapsed = True
        collection.lighthouse_lights_collapsed = True
    bpy.context.scene.collection.lighthouse_lights_collapsed = True

empty_scene()
set_ = new_collection("Set")
interior = new_collection("Interior", set_)
lamps = new_collection("Lamps", interior)
new_collection("Shades", lamps)
move_to(add_light("Shade"), bpy.data.collections["Shades"])
bulb = add_light("Bulb")
move_to(bulb, lamps)
props = new_collection("Props", set_)
move_to(add_light("Prop"), props)
"""


def run(snippet):
    return run_in_blender(HELPERS + textwrap.dedent(snippet))


def test_reveal_expands_the_path_and_opens_the_lights_row():
    result = run("""
        fold_everything()
        make_active(bulb)
        before = "Bulb" in listed_lights()
        bpy.ops.lighthouse.reveal_active_light()
        report({
            "before": before,
            "expanded": {c.name: not c.lighthouse_collapsed for c in (set_, interior, lamps)},
            "lights_row_open": not lamps.lighthouse_lights_collapsed,
            "listed": "Bulb" in listed_lights(),
        })
    """)

    assert result == {
        "before": False,
        "expanded": {"Set": True, "Interior": True, "Lamps": True},
        "lights_row_open": True,
        "listed": True,
    }


def test_reveal_leaves_a_sibling_collection_collapsed():
    collapsed = run("""
        fold_everything()
        make_active(bulb)
        bpy.ops.lighthouse.reveal_active_light()
        report(props.lighthouse_collapsed)
    """)

    assert collapsed is True


def test_a_light_in_two_collections_is_revealed_in_both():
    result = run("""
        move_to(bulb, lamps, props)
        fold_everything()
        make_active(bulb)
        bpy.ops.lighthouse.reveal_active_light()
        report({c.name: not c.lighthouse_collapsed for c in (set_, interior, lamps, props)})
    """)

    assert result == {"Set": True, "Interior": True, "Lamps": True, "Props": True}


def test_a_scene_collection_light_behind_the_folded_scene_collection_is_revealed():
    result = run("""
        sun = add_light("Sun", "SUN")
        fold_everything()
        make_active(sun)
        before = "Sun" in listed_lights()
        bpy.ops.lighthouse.reveal_active_light()
        report({"before": before, "after": "Sun" in listed_lights(), "set": set_.lighthouse_collapsed})
    """)

    assert result == {"before": False, "after": True, "set": True}


def test_reveal_is_unavailable_without_an_active_light():
    result = run("""
        make_active(add_mesh("Cube"))
        with_mesh = bpy.ops.lighthouse.reveal_active_light.poll()
        make_active(None)
        report([with_mesh, bpy.ops.lighthouse.reveal_active_light.poll()])
    """)

    assert result == [False, False]


def test_add_light_into_a_collapsed_active_collection_reveals_it():
    result = run("""
        fold_everything()
        layer = bpy.context.view_layer
        layer.active_layer_collection = lighthouse.lights.find_layer_collection(layer.layer_collection, lamps)
        bpy.ops.lighthouse.add_light(type='SPOT')
        report({
            "expanded": {c.name: not c.lighthouse_collapsed for c in (set_, interior, lamps)},
            "listed": layer.objects.active.name in listed_lights(),
        })
    """)

    assert result == {"expanded": {"Set": True, "Interior": True, "Lamps": True}, "listed": True}
