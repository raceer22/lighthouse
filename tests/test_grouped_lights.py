import textwrap

from blender_runner import run_in_blender

HELPERS = """
from lighthouse.lights import GroupEntry, LightEntry, LightsEntry, list_entries

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
        ["group", e.collection.name, e.depth, e.count] if isinstance(e, GroupEntry)
        else ["lights", e.collection.name, e.depth, e.count] if isinstance(e, LightsEntry)
        else ["light", e.obj.name, e.depth, e.other_collections]
        for e in list_entries(bpy.context.view_layer, **options)
    ]
"""


def run(snippet):
    return run_in_blender(HELPERS + textwrap.dedent(snippet))


def test_collections_on_the_path_to_a_light_are_kept_as_nested_groups():
    rows = run("""
        empty_scene()
        set_ = new_collection("Set")
        interior = new_collection("Interior", set_)
        lamps = new_collection("Lamps", interior)
        move_to(add_light("Bulb"), lamps)
        report(entries())
    """)

    assert rows == [
        ["group", "Set", 0, 1],
        ["group", "Interior", 1, 1],
        ["group", "Lamps", 2, 1],
        ["light", "Bulb", 3, 0],
    ]


def test_collections_without_lights_are_left_out_and_scene_collection_lights_have_no_header():
    rows = run("""
        empty_scene()
        new_collection("Empty")
        move_to(add_mesh("Cube"), new_collection("Props"))
        move_to(add_light("Key"), new_collection("Lights"))
        add_light("Sun", "SUN")
        report(entries())
    """)

    assert rows == [
        ["light", "Sun", 0, 0],
        ["group", "Lights", 0, 1],
        ["light", "Key", 1, 0],
    ]


def test_excluded_collection_has_no_header_and_its_lights_are_not_listed():
    rows = run("""
        empty_scene()
        move_to(add_light("Key"), new_collection("Shown"))
        move_to(add_light("Hidden"), new_collection("Excluded"))
        bpy.context.view_layer.layer_collection.children["Excluded"].exclude = True
        report(entries())
    """)

    assert rows == [
        ["group", "Shown", 0, 1],
        ["light", "Key", 1, 0],
    ]


def test_search_flattens_the_list_and_clearing_it_restores_groups():
    result = run("""
        empty_scene()
        move_to(add_light("Key Lamp"), new_collection("Lamps"))
        add_light("key sun", "SUN")
        add_light("Fill")
        report({"search": entries(name_filter="key"), "cleared": entries(name_filter="")})
    """)

    assert result == {
        "search": [["light", "Key Lamp", 0, 0], ["light", "key sun", 0, 0]],
        "cleared": [
            ["light", "Fill", 0, 0],
            ["light", "key sun", 0, 0],
            ["group", "Lamps", 0, 1],
            ["light", "Key Lamp", 1, 0],
        ],
    }


def test_flat_mode_lists_every_light_by_name_with_no_groups():
    rows = run("""
        empty_scene()
        move_to(add_light("Zed"), new_collection("Lamps"))
        add_light("alpha")
        report(entries(grouped=False))
    """)

    assert rows == [["light", "alpha", 0, 0], ["light", "Zed", 0, 0]]


def test_light_in_two_collections_is_listed_under_each_and_once_when_flat():
    result = run("""
        empty_scene()
        move_to(add_light("Key"), new_collection("A"), new_collection("B"))
        report({"grouped": entries(), "flat": entries(grouped=False)})
    """)

    assert result == {
        "grouped": [
            ["group", "A", 0, 1],
            ["light", "Key", 1, 1],
            ["group", "B", 0, 1],
            ["light", "Key", 1, 1],
        ],
        "flat": [["light", "Key", 0, 0]],
    }


def test_group_counts_include_sub_collections_once_and_follow_the_type_filter():
    result = run("""
        empty_scene()
        set_ = new_collection("Set")
        lamps = new_collection("Lamps", set_)
        spots = new_collection("Spots", set_)
        move_to(add_light("Shared"), lamps, spots)
        move_to(add_light("Bulb"), lamps)
        move_to(add_light("Beam", "SPOT"), spots)
        move_to(add_light("Fill", "AREA"), set_)
        groups = lambda **f: [[e[1], e[3]] for e in entries(**f) if e[0] == "group"]
        report({"all": groups(), "spot": groups(type_filter="SPOT")})
    """)

    assert result == {
        "all": [["Set", 4], ["Lamps", 2], ["Spots", 2]],
        "spot": [["Set", 1], ["Spots", 1]],
    }


def test_indentation_stops_growing_after_three_levels():
    levels = run_in_blender("""
        from lighthouse.lights import indent_level
        report([indent_level(depth) for depth in range(6)])
    """)

    assert levels == [0, 1, 2, 3, 3, 3]


def test_info_tooltip_names_whichever_cases_apply():
    tooltips = run_in_blender("""
        from lighthouse.lights import light_info_tooltip
        report([light_info_tooltip(*case) for case in [(0, 0), (2, 0), (1, 0), (0, 1), (0, 3), (1, 2)]])
    """)

    assert tooltips == [
        "",
        "Light data is shared with 2 other objects",
        "Light data is shared with 1 other object",
        "Also in 1 other collection",
        "Also in 3 other collections",
        "Light data is shared with 1 other object. Also in 2 other collections",
    ]


def test_a_collections_own_lights_come_before_its_sub_collections():
    rows = run("""
        empty_scene()
        set_ = new_collection("Set")
        move_to(add_light("Zenith"), set_)
        move_to(add_light("Bulb"), new_collection("Lamps", set_))
        add_light("Sun", "SUN")
        report(entries())
    """)

    assert rows == [
        ["light", "Sun", 0, 0],
        ["group", "Set", 0, 2],
        ["lights", "Set", 1, 1],
        ["light", "Zenith", 2, 0],
        ["group", "Lamps", 1, 1],
        ["light", "Bulb", 2, 0],
    ]


def test_own_lights_next_to_sub_collections_go_under_a_lights_row():
    rows = run("""
        empty_scene()
        set_ = new_collection("Set")
        move_to(add_light("Key"), set_)
        move_to(add_light("Fill"), set_)
        move_to(add_light("Bulb"), new_collection("Lamps", set_))
        report(entries())
    """)

    assert rows == [
        ["group", "Set", 0, 3],
        ["lights", "Set", 1, 2],
        ["light", "Fill", 2, 0],
        ["light", "Key", 2, 0],
        ["group", "Lamps", 1, 1],
        ["light", "Bulb", 2, 0],
    ]


def test_a_leaf_collection_lists_its_lights_with_no_lights_row():
    rows = run("""
        empty_scene()
        props = new_collection("Props")
        move_to(add_light("Lamp"), props)
        move_to(add_light("Candle"), props)
        report(entries())
    """)

    assert rows == [
        ["group", "Props", 0, 2],
        ["light", "Candle", 1, 0],
        ["light", "Lamp", 1, 0],
    ]
