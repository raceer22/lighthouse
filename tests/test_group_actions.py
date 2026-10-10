import textwrap

from blender_runner import run_in_blender, run_in_blender_with_reports

HELPERS = """
import lighthouse
from lighthouse.lights import GroupEntry, SceneEntry, list_entries
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
        else ["light", e.obj.name, e.depth]
        for e in list_entries(bpy.context.view_layer, **options)
    ]
"""


def run(snippet):
    return run_in_blender(HELPERS + textwrap.dedent(snippet))


def run_with_reports(snippet):
    return run_in_blender_with_reports(HELPERS + textwrap.dedent(snippet))


def test_toggle_group_flips_collapsed_without_an_undo_step():
    result = run("""
        empty_scene()
        lamps = new_collection("Lamps")
        bpy.ops.lighthouse.toggle_group(name="Lamps")
        collapsed = lamps.lighthouse_collapsed
        bpy.ops.lighthouse.toggle_group(name="Lamps")
        report({
            "collapsed": collapsed,
            "expanded": lamps.lighthouse_collapsed,
            "undo": "UNDO" in bpy.types.LIGHTHOUSE_OT_toggle_group.bl_options,
        })
    """)

    assert result == {"collapsed": True, "expanded": False, "undo": False}


def test_collapsed_group_keeps_its_header_and_count_but_hides_everything_below_it():
    rows = run("""
        empty_scene()
        set_ = new_collection("Set")
        lamps = new_collection("Lamps", set_)
        move_to(add_light("Bulb"), lamps)
        move_to(add_light("Fill"), set_)
        move_to(add_light("Key"), new_collection("Studio"))
        set_.lighthouse_collapsed = True
        report(entries())
    """)

    assert rows == [
        ["scene", 0],
        ["group", "Set", 0, 2],
        ["group", "Studio", 0, 1],
        ["light", "Key", 1],
    ]


def test_collapsed_group_stays_collapsed_after_saving_and_reopening(tmp_path):
    collapsed = run(f"""
        empty_scene()
        move_to(add_light("Bulb"), new_collection("Lamps"))
        bpy.ops.lighthouse.toggle_group(name="Lamps")
        path = {str(tmp_path / "scene.blend")!r}
        bpy.ops.wm.save_as_mainfile(filepath=path)
        bpy.ops.wm.read_homefile(use_factory_startup=True)
        bpy.ops.wm.open_mainfile(filepath=path)
        report(bpy.data.collections["Lamps"].lighthouse_collapsed)
    """)

    assert collapsed is True


TOGGLE_ALL = """
        empty_scene()
        set_ = new_collection("Set")
        lamps = new_collection("Lamps", set_)
        props = new_collection("Props")
        move_to(add_light("Bulb"), lamps)
        move_to(add_light("Desk"), props)

        def collapsed():
            return sorted(c.name for c in bpy.context.scene.collection.children_recursive
                          if c.lighthouse_collapsed)
"""


def test_toggle_all_collapses_every_listed_group_then_expands_them_without_an_undo_step():
    result = run(TOGGLE_ALL + """
        bpy.ops.lighthouse.toggle_all_groups()
        first = collapsed()
        bpy.ops.lighthouse.toggle_all_groups()
        report({
            "first": first,
            "second": collapsed(),
            "undo": "UNDO" in bpy.types.LIGHTHOUSE_OT_toggle_all_groups.bl_options,
        })
    """)

    assert result == {"first": ["Lamps", "Props", "Set"], "second": [], "undo": False}


def test_toggle_all_collapses_the_rest_when_only_some_groups_are_collapsed():
    result = run(TOGGLE_ALL + """
        props.lighthouse_collapsed = True
        bpy.ops.lighthouse.toggle_all_groups()
        report(collapsed())
    """)

    assert result == ["Lamps", "Props", "Set"]


SELECTION = """
        def selection():
            layer = bpy.context.view_layer
            return {
                "selected": sorted(o.name for o in layer.objects if o.select_get()),
                "active": layer.objects.active.name if layer.objects.active else None,
            }

        empty_scene()
        set_ = new_collection("Set")
        lamps = new_collection("Lamps", set_)
        other = new_collection("Other")
        move_to(add_light("Fill", "AREA"), set_)
        move_to(add_light("Bulb"), lamps)
        move_to(add_light("Shared"), lamps, other)
        move_to(add_light("Key"), other)
        add_light("Sun", "SUN")
        cube = add_mesh("Cube")
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube
"""


def test_select_group_selects_only_the_lights_in_it_and_its_sub_collections():
    result = run(SELECTION + """
        bpy.ops.lighthouse.select_group(name="Set")
        report(selection())
    """)

    assert result == {"selected": ["Bulb", "Fill", "Shared"], "active": "Fill"}


def test_select_group_with_extend_keeps_the_earlier_selection():
    result = run(SELECTION + """
        bpy.ops.lighthouse.select_group(name="Other")
        bpy.ops.lighthouse.select_group(name="Set", extend=True)
        report(selection())
    """)

    assert result == {"selected": ["Bulb", "Fill", "Key", "Shared"], "active": "Key"}


def test_select_group_follows_the_type_filter_and_keeps_an_active_light_already_in_the_group():
    result = run(SELECTION + """
        bpy.context.view_layer.objects.active = bpy.data.objects["Shared"]
        bpy.context.window_manager.lighthouse.type_filter = "POINT"
        bpy.ops.lighthouse.select_group(name="Set")
        report(selection())
    """)

    assert result == {"selected": ["Bulb", "Shared"], "active": "Shared"}


def test_move_relinks_selected_lights_only_into_the_target_and_skips_library_lights(tmp_path):
    places, reports = run_with_reports(f"""
        empty_scene()
        library_light = add_light("Library")
        path = {str(tmp_path / "library.blend")!r}
        bpy.data.libraries.write(path, {{library_light}})
        bpy.data.objects.remove(library_light)
        with bpy.data.libraries.load(path, link=True) as (src, dst):
            dst.objects = ["Library"]
        bpy.context.scene.collection.objects.link(dst.objects[0])
        a, b, c = new_collection("A"), new_collection("B"), new_collection("C")
        roam = add_light("Roam")
        move_to(roam, a, b, bpy.context.scene.collection)
        move_to(add_light("Still"), a)
        roam.select_set(True)
        bpy.data.objects["Library"].select_set(True)
        bpy.ops.lighthouse.move_to_group(name="C")
        report({{o.name: sorted(c.name for c in o.users_collection) for o in bpy.context.view_layer.objects}})
    """)

    assert places == {"Roam": ["C"], "Still": ["A"], "Library": ["Scene Collection"]}
    assert reports == ["Moved 1 light to C, skipped 1 read-only"]


def test_move_into_a_library_collection_is_refused_and_nothing_moves(tmp_path):
    result = run(f"""
        empty_scene()
        linked = bpy.data.collections.new("Linked")
        path = {str(tmp_path / "library.blend")!r}
        bpy.data.libraries.write(path, {{linked}})
        bpy.data.collections.remove(linked)
        with bpy.data.libraries.load(path, link=True) as (src, dst):
            dst.collections = ["Linked"]
        bpy.context.scene.collection.children.link(dst.collections[0])
        key = add_light("Key")
        key.select_set(True)
        try:
            bpy.ops.lighthouse.move_to_group(name="Linked")
            error = None
        except RuntimeError as e:
            error = str(e)
        report({{"error": error, "places": [c.name for c in key.users_collection]}})
    """)

    assert "Linked is read-only" in result["error"]
    assert result["places"] == ["Scene Collection"]


def test_hide_group_toggles_both_collection_flags_and_never_touches_light_flags():
    result = run("""
        def state():
            return {
                "group": [lamps.hide_render, lamps.hide_viewport],
                "lights": {o.name: [o.hide_render, o.hide_viewport] for o in lamps.objects},
            }

        empty_scene()
        lamps = new_collection("Lamps")
        move_to(add_light("Bulb"), lamps)
        move_to(add_light("Muted"), lamps)
        bpy.ops.lighthouse.mute_light(name="Muted")
        lamps.hide_render = True
        bpy.ops.lighthouse.hide_group(name="Lamps")
        hidden = state()
        bpy.ops.lighthouse.hide_group(name="Lamps")
        report({"hidden": hidden, "shown": state()})
    """)

    lights = {"Bulb": [False, False], "Muted": [True, True]}
    assert result == {
        "hidden": {"group": [True, True], "lights": lights},
        "shown": {"group": [False, False], "lights": lights},
    }


def test_lights_in_a_hidden_group_are_dimmed_but_not_muted():
    states = run("""
        from lighthouse.lights import row_state
        empty_scene()
        move_to(add_light("Bulb"), new_collection("Lamps"))
        add_light("Sun", "SUN")
        bpy.ops.lighthouse.hide_group(name="Lamps")
        layer = bpy.context.view_layer
        report({o.name: [row_state(o, layer).dimmed, row_state(o, layer).muted] for o in layer.objects})
    """)

    assert states == {"Bulb": [True, False], "Sun": [False, False]}
