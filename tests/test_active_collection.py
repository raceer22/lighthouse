import textwrap

from blender_runner import run_in_blender

HELPERS = """
import lighthouse
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

def active_collection():
    return bpy.context.view_layer.active_layer_collection.collection.name

empty_scene()
layer = bpy.context.view_layer
set_ = new_collection("Set")
lamps = new_collection("Lamps", set_)
move_to(add_light("Bulb"), lamps)
key = add_light("Key")
"""


def run(snippet):
    return run_in_blender(HELPERS + textwrap.dedent(snippet))


def test_set_active_collection_makes_it_active_and_leaves_the_selection_alone():
    result = run("""
        key.select_set(True)
        layer.objects.active = key
        bpy.ops.lighthouse.set_active_collection(name="Lamps")
        report({
            "active collection": active_collection(),
            "selected": sorted(o.name for o in layer.objects if o.select_get()),
            "active object": layer.objects.active.name,
        })
    """)

    assert result == {"active collection": "Lamps", "selected": ["Key"], "active object": "Key"}


def test_a_light_added_after_choosing_a_collection_lands_only_there():
    collections = run("""
        bpy.ops.lighthouse.set_active_collection(name="Lamps")
        bpy.ops.lighthouse.add_light(type='SPOT')
        report([c.name for c in layer.objects.active.users_collection])
    """)

    assert collections == ["Lamps"]


def test_a_library_collection_can_be_made_active_but_adding_a_light_there_is_refused():
    result = run("""
        import os, tempfile
        library = os.path.join(tempfile.mkdtemp(), "library.blend")
        linked = bpy.data.collections.new("Linked")
        bpy.data.libraries.write(library, {linked})
        bpy.data.collections.remove(linked)
        with bpy.data.libraries.load(library, link=True) as (source, target):
            target.collections = ["Linked"]
        bpy.context.scene.collection.children.link(target.collections[0])
        layer.update()
        path = target.collections[0].library.filepath

        made_active = bpy.ops.lighthouse.set_active_collection(name="Linked", library=path)
        objects = len(bpy.data.objects)
        try:
            bpy.ops.lighthouse.add_light(type='POINT')
            error = None
        except RuntimeError as e:
            error = str(e)
        report({
            "made active": sorted(made_active),
            "active collection": active_collection(),
            "error": error,
            "new objects": len(bpy.data.objects) - objects,
        })
    """)

    assert result["made active"] == ["FINISHED"]
    assert result["active collection"] == "Linked"
    assert "Linked is read-only" in result["error"]
    assert result["new objects"] == 0


def test_an_unknown_or_excluded_collection_is_cancelled_and_the_active_one_kept():
    result = run("""
        excluded = new_collection("Excluded")
        move_to(add_light("Hidden"), excluded)
        layer.layer_collection.children["Excluded"].exclude = True
        layer.active_layer_collection = layer.layer_collection.children["Set"]
        report({
            "unknown": sorted(bpy.ops.lighthouse.set_active_collection(name="Nope")),
            "excluded": sorted(bpy.ops.lighthouse.set_active_collection(name="Excluded")),
            "active collection": active_collection(),
        })
    """)

    assert result == {"unknown": ["CANCELLED"], "excluded": ["CANCELLED"], "active collection": "Set"}


def test_an_empty_name_makes_the_scene_collection_active_and_new_lights_land_there():
    result = run("""
        layer.active_layer_collection = layer.layer_collection.children["Set"]
        finished = sorted(bpy.ops.lighthouse.set_active_collection(name=""))
        bpy.ops.lighthouse.add_light(type='POINT')
        report({
            "finished": finished,
            "master active": layer.active_layer_collection == layer.layer_collection,
            "collections": [c.name for c in layer.objects.active.users_collection],
        })
    """)

    assert result == {"finished": ["FINISHED"], "master active": True, "collections": ["Scene Collection"]}


def test_move_to_an_empty_name_moves_selected_lights_into_the_scene_collection():
    result = run("""
        bulb = bpy.data.objects["Bulb"]
        bulb.select_set(True)
        layer.objects.active = bulb
        finished = sorted(bpy.ops.lighthouse.move_to_group(name=""))
        report({"finished": finished, "collections": [c.name for c in bulb.users_collection]})
    """)

    assert result == {"finished": ["FINISHED"], "collections": ["Scene Collection"]}
