import textwrap

from blender_runner import run_in_blender

HELPERS = """
import lighthouse
from lighthouse.lights import GroupEntry, SceneEntry, LightsEntry, list_entries, listed_groups
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

def entries(**options):
    return [
        ["scene", e.count] if isinstance(e, SceneEntry)
        else ["group", e.collection.name, e.depth, e.count] if isinstance(e, GroupEntry)
        else ["lights", e.collection.name, e.depth, e.count] if isinstance(e, LightsEntry)
        else ["light", e.obj.name, e.depth]
        for e in list_entries(bpy.context.view_layer, **options)
    ]

def foldable(**options):
    return {e.collection.name: e.foldable for e in list_entries(bpy.context.view_layer, **options)
            if isinstance(e, GroupEntry)}

empty_scene()
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
set_ = new_collection("Set")
move_to(add_light("Key"), set_)
"""


def run(snippet):
    return run_in_blender(HELPERS + textwrap.dedent(snippet))


def test_show_empty_lists_empty_and_nested_empty_collections_but_not_excluded_ones():
    result = run("""
        new_collection("Props")
        new_collection("B", new_collection("A"))
        new_collection("Hidden")
        bpy.context.view_layer.layer_collection.children["Hidden"].exclude = True
        report(entries(show_empty=True))
    """)

    assert result == [
        ["scene", 0],
        ["group", "Set", 0, 1],
        ["light", "Key", 1],
        ["group", "Props", 0, 0],
        ["group", "A", 0, 0],
        ["group", "B", 1, 0],
    ]


def test_type_filter_lists_a_collection_without_matching_lights_only_with_show_empty():
    result = run("""
        report({
            "on": entries(type_filter='SUN', show_empty=True),
            "off": entries(type_filter='SUN'),
        })
    """)

    assert result == {
        "on": [["scene", 0], ["group", "Set", 0, 0]],
        "off": [["scene", 0]],
    }


def test_foldable_means_something_is_under_the_collection():
    result = run("""
        new_collection("Leaf")
        new_collection("Inner", new_collection("Outer"))
        report(foldable(show_empty=True))
    """)

    assert result == {"Set": True, "Leaf": False, "Outer": True, "Inner": False}


def test_an_empty_sub_collection_gives_a_lights_row_only_while_shown():
    result = run("""
        new_collection("Empty", set_)
        report({
            "on": entries(show_empty=True),
            "off": entries(),
        })
    """)

    assert result == {
        "on": [
            ["scene", 0],
            ["group", "Set", 0, 1],
            ["lights", "Set", 1, 1],
            ["light", "Key", 2],
            ["group", "Empty", 1, 0],
        ],
        "off": [["scene", 0], ["group", "Set", 0, 1], ["light", "Key", 1]],
    }


def test_listed_groups_includes_empty_collections_with_show_empty():
    result = run("""
        new_collection("Props")
        report({
            "on": [c.name for c in listed_groups(bpy.context.view_layer, show_empty=True)],
            "off": [c.name for c in listed_groups(bpy.context.view_layer)],
        })
    """)

    assert result == {"on": ["Set", "Props"], "off": ["Set"]}


def test_expand_all_ignores_empty_collections_that_have_no_triangle():
    result = run("""
        new_collection("Props")
        set_.lighthouse_collapsed = True
        bpy.ops.lighthouse.toggle_all_groups()
        report(set_.lighthouse_collapsed)
    """)

    assert result is False


def test_show_empty_defaults_on_and_survives_clear_filters():
    result = run("""
        settings = bpy.context.window_manager.lighthouse
        default = settings.show_empty
        settings.show_empty = False
        bpy.ops.lighthouse.clear_filters()
        report([default, settings.show_empty])
    """)

    assert result == [True, False]
