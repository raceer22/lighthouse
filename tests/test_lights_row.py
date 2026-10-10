import textwrap

from blender_runner import run_in_blender

HELPERS = """
import lighthouse
from lighthouse.lights import GroupEntry, SceneEntry, LightsEntry, group_lights, list_entries
lighthouse.register()
# These tests predate show_empty; the default "Collection" is empty and would join toggle-all.
bpy.context.window_manager.lighthouse.show_empty = False

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

empty_scene()
sun = add_light("Sun", "SUN")
set_ = new_collection("Set")
move_to(add_light("Key"), set_)
move_to(add_light("Fill"), set_)
lamps = new_collection("Lamps", set_)
move_to(add_light("Bulb"), lamps)
"""


def run(snippet):
    return run_in_blender(HELPERS + textwrap.dedent(snippet))


def test_folding_the_lights_row_hides_own_lights_but_keeps_sub_collections_and_counts():
    result = run("""
        bpy.ops.lighthouse.toggle_lights_row(name="Set")
        report({
            "rows": entries(),
            "group_lights": [o.name for o in group_lights(bpy.context.view_layer, set_)],
        })
    """)

    assert result == {
        "rows": [
            ["scene", 1],
            ["light", "Sun", 0],
            ["group", "Set", 0, 3],
            ["lights", "Set", 1, 2],
            ["group", "Lamps", 1, 1],
            ["light", "Bulb", 2],
        ],
        "group_lights": ["Fill", "Key", "Bulb"],
    }


def test_collapsing_and_expanding_the_collection_leaves_its_lights_row_folded():
    rows = run("""
        bpy.ops.lighthouse.toggle_lights_row(name="Set")
        bpy.ops.lighthouse.toggle_group(name="Set")
        bpy.ops.lighthouse.toggle_group(name="Set")
        report(entries())
    """)

    assert ["lights", "Set", 1, 2] in rows
    assert ["light", "Key", 2] not in rows


def test_lights_row_starts_open_folds_without_undo_and_stays_folded_after_reopening(tmp_path):
    result = run(f"""
        default = set_.lighthouse_lights_collapsed
        bpy.ops.lighthouse.toggle_lights_row(name="Set")
        path = {str(tmp_path / "scene.blend")!r}
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.read_homefile(use_factory_startup=True)
        bpy.ops.wm.open_mainfile(filepath=path)
        report({{
            "default": default,
            "reopened": bpy.data.collections["Set"].lighthouse_lights_collapsed,
            "undo": "UNDO" in bpy.types.LIGHTHOUSE_OT_toggle_lights_row.bl_options,
        }})
    """)

    assert result == {"default": False, "reopened": True, "undo": False}


def test_range_select_across_a_folded_lights_row_skips_the_hidden_lights():
    selected = run("""
        bpy.ops.lighthouse.toggle_lights_row(name="Set")
        bpy.ops.lighthouse.select_light(name="Sun")
        bpy.ops.lighthouse.select_light(name="Bulb", action='RANGE')
        report(sorted(o.name for o in bpy.context.view_layer.objects if o.select_get()))
    """)

    assert selected == ["Bulb", "Sun"]


TOGGLE_ALL = """
        props = new_collection("Props")
        move_to(add_light("Desk"), props)

        def state():
            return {
                "collapsed": sorted(c.name for c in bpy.data.collections if c.lighthouse_collapsed),
                "folded": sorted(c.name for c in bpy.data.collections if c.lighthouse_lights_collapsed),
            }
"""


def test_expand_all_also_unfolds_lights_rows():
    result = run(TOGGLE_ALL + """
        for collection in (set_, lamps, props):
            collection.lighthouse_collapsed = True
        set_.lighthouse_lights_collapsed = True
        bpy.ops.lighthouse.toggle_all_groups()
        report(state())
    """)

    assert result == {"collapsed": [], "folded": []}


def test_collapse_all_leaves_folded_lights_rows_folded():
    result = run(TOGGLE_ALL + """
        set_.lighthouse_lights_collapsed = True
        bpy.ops.lighthouse.toggle_all_groups()
        report(state())
    """)

    assert result == {"collapsed": ["Lamps", "Props", "Set"], "folded": ["Set"]}


def test_folded_lights_rows_do_not_count_as_collapsed():
    result = run(TOGGLE_ALL + """
        set_.lighthouse_lights_collapsed = True
        lamps.lighthouse_lights_collapsed = True
        bpy.ops.lighthouse.toggle_all_groups()
        report(state()["collapsed"])
    """)

    assert result == ["Lamps", "Props", "Set"]


def test_folding_the_scene_collection_hides_only_its_own_lights():
    rows = run("""
        bpy.ops.lighthouse.toggle_lights_row(name="")
        report(entries())
    """)

    assert rows == [
        ["scene", 1],
        ["group", "Set", 0, 3],
        ["lights", "Set", 1, 2],
        ["light", "Fill", 2],
        ["light", "Key", 2],
        ["group", "Lamps", 1, 1],
        ["light", "Bulb", 2],
    ]


def test_expand_all_unfolds_the_scene_collection_and_collapse_all_leaves_it_unfolded():
    result = run(TOGGLE_ALL + """
        scene_collection = bpy.context.scene.collection
        for collection in (set_, lamps, props):
            collection.lighthouse_collapsed = True
        scene_collection.lighthouse_lights_collapsed = True
        bpy.ops.lighthouse.toggle_all_groups()
        expanded = scene_collection.lighthouse_lights_collapsed
        bpy.ops.lighthouse.toggle_all_groups()
        report({"after expand": expanded, "after collapse": scene_collection.lighthouse_lights_collapsed,
                "collapsed": state()["collapsed"]})
    """)

    assert result == {"after expand": False, "after collapse": False, "collapsed": ["Lamps", "Props", "Set"]}


def test_scene_collection_fold_stays_after_saving_and_reopening(tmp_path):
    folded = run(f"""
        bpy.ops.lighthouse.toggle_lights_row(name="")
        path = {str(tmp_path / "scene.blend")!r}
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.read_homefile(use_factory_startup=True)
        bpy.ops.wm.open_mainfile(filepath=path)
        report(bpy.context.scene.collection.lighthouse_lights_collapsed)
    """)

    assert folded is True
