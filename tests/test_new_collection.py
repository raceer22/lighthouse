import textwrap

from blender_runner import run_in_blender

HELPERS = """
import lighthouse
from lighthouse.lights import GroupEntry, SceneEntry, list_entries
lighthouse.register()

def new_collection(name, parent=None):
    collection = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(collection)
    return collection

def active_collection():
    return bpy.context.view_layer.active_layer_collection.collection

empty_scene()
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
layer = bpy.context.view_layer
set_ = new_collection("Set")
key = add_light("Key")
"""


def run(snippet):
    return run_in_blender(HELPERS + textwrap.dedent(snippet))


def test_new_collection_goes_inside_the_active_collection_and_becomes_active():
    result = run("""
        bpy.ops.lighthouse.set_active_collection(name="Set")
        before = set(bpy.data.collections)
        bpy.ops.lighthouse.new_collection()
        new = set(bpy.data.collections) - before
        report({
            "new": [c.name for c in new],
            "children of Set": [c.name for c in set_.children],
            "active": active_collection().name,
        })
    """)

    assert result == {"new": ["Collection"], "children of Set": ["Collection"], "active": "Collection"}


def test_with_the_scene_collection_active_the_new_collection_is_top_level():
    result = run("""
        bpy.ops.lighthouse.set_active_collection(name="")
        bpy.ops.lighthouse.new_collection()
        report([c.name for c in bpy.context.scene.collection.children])
    """)

    assert result == ["Set", "Collection"]


def test_a_library_parent_is_refused_without_creating_anything():
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
        bpy.ops.lighthouse.set_active_collection(name="Linked", library=target.collections[0].library.filepath)
        before = sorted(c.name for c in bpy.data.collections)
        try:
            bpy.ops.lighthouse.new_collection()
            error = None
        except RuntimeError as e:
            error = str(e)
        report({"error": error, "unchanged": sorted(c.name for c in bpy.data.collections) == before})
    """)

    assert "Linked is read-only" in result["error"]
    assert result["unchanged"] is True


def test_new_collection_leaves_the_selection_alone():
    result = run("""
        key.select_set(True)
        layer.objects.active = key
        bpy.ops.lighthouse.new_collection()
        report({
            "selected": sorted(o.name for o in layer.objects if o.select_get()),
            "active object": layer.objects.active.name,
        })
    """)

    assert result == {"selected": ["Key"], "active object": "Key"}


def test_the_new_collection_is_listed_at_zero_under_its_parent():
    result = run("""
        bpy.ops.lighthouse.set_active_collection(name="Set")
        bpy.ops.lighthouse.new_collection()
        report([
            [e.collection.name, e.depth, e.count]
            for e in list_entries(layer, show_empty=True) if isinstance(e, GroupEntry)
        ])
    """)

    assert result == [["Set", 0, 0], ["Collection", 1, 0]]


def test_new_collection_takes_the_given_name_and_falls_back_when_blank():
    result = run("""
        bpy.ops.lighthouse.new_collection(name="  Props ")
        bpy.ops.lighthouse.set_active_collection(name="")
        bpy.ops.lighthouse.new_collection(name="   ")
        report([c.name for c in bpy.context.scene.collection.children])
    """)

    assert result == ["Set", "Props", "Collection"]
