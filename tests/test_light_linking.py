import textwrap

from blender_runner import RECORDER, run_in_blender, run_in_blender_with_reports

SETUP = """
    import lighthouse
    lighthouse.register()
    from lighthouse.lights import receivers
    empty_scene()
    key = add_light("Key")
    cube, sphere, plane = add_mesh("Cube"), add_mesh("sphere"), add_mesh("Plane")

    def select(*objs):
        for obj in bpy.context.view_layer.objects:
            obj.select_set(obj in objs)

    def listed():
        return [[r.id.name, r.kind, r.state] for r in receivers(key)]
"""


def run(snippet, prelude=""):
    return run_in_blender(textwrap.dedent(SETUP) + prelude + textwrap.dedent(snippet))


def test_link_selected_includes_the_selected_objects_sorted_by_name():
    result = run("""
        select(sphere, cube)
        status = sorted(bpy.ops.lighthouse.link_receivers(name="Key"))
        report([status, key.light_linking.receiver_collection.name, listed()])
    """)

    assert result == [["FINISHED"], "Light Linking for Key",
                      [["Cube", "OBJECT", "INCLUDE"], ["sphere", "OBJECT", "INCLUDE"]]]


def test_linking_again_adds_only_new_objects_and_never_the_light_itself():
    result = run("""
        select(cube, sphere)
        bpy.ops.lighthouse.link_receivers(name="Key")
        select(cube, plane, key)
        bpy.ops.lighthouse.link_receivers(name="Key")
        report(listed())
    """)

    assert result == [["Cube", "OBJECT", "INCLUDE"], ["Plane", "OBJECT", "INCLUDE"],
                      ["sphere", "OBJECT", "INCLUDE"]]


def test_link_selected_with_only_the_light_selected_cancels_without_a_collection():
    result = run_in_blender_with_reports(textwrap.dedent(SETUP) + textwrap.dedent("""
        select(key)
        status = sorted(bpy.ops.lighthouse.link_receivers(name="Key"))
        report([status, key.light_linking.receiver_collection is None])
    """), level="Warning")

    assert result == ([["CANCELLED"], True], ["No objects selected"])


def test_remove_receiver_drops_one_object_and_keeps_the_rest():
    result = run("""
        select(cube, sphere)
        bpy.ops.lighthouse.link_receivers(name="Key")
        status = sorted(bpy.ops.lighthouse.remove_receiver(name="Key", receiver="Cube", kind='OBJECT'))
        report([status, listed()])
    """)

    assert result == [["FINISHED"], [["sphere", "OBJECT", "INCLUDE"]]]


def test_child_collections_are_listed_before_objects():
    result = run("""
        select(cube)
        bpy.ops.lighthouse.link_receivers(name="Key")
        props = bpy.data.collections.new("Props")
        key.light_linking.receiver_collection.children.link(props)
        report(listed())
    """)

    assert result == [["Props", "COLLECTION", "INCLUDE"], ["Cube", "OBJECT", "INCLUDE"]]


DRAW_SECTION = """
    from lighthouse.lights import RowState
    state = RowState(dimmed=False, read_only=False, muted=False, soloed=False)

    def section(light):
        def draw(self, context):
            bpy.types.LIGHTHOUSE_PT_lights.draw_details(self, light, state, context.scene.render.engine)
        entries = drawn(draw)
        return entries[[e[:2] for e in entries].index(["label", "Light Linking"]):]
"""
LIGHT = {"name": "Key", "library": ""}
BUTTONS = [
    ["label", "Light Linking"],
    ["operator", "lighthouse.link_receivers", "Link Selected", LIGHT],
    ["operator", "lighthouse.link_receivers", "Exclude Selected", dict(LIGHT, state="EXCLUDE")],
]


def test_open_details_end_with_the_buttons_and_one_row_per_receiver():
    result = run(prelude=RECORDER + textwrap.dedent(DRAW_SECTION), snippet="""
        select(cube, sphere)
        bpy.ops.lighthouse.link_receivers(name="Key")
        report(section(key))
    """)

    remove = dict(LIGHT, receiver_library="", kind="OBJECT")
    assert result == BUTTONS + [
        ["operator", "lighthouse.clear_receivers", "Clear", LIGHT],
        ["label", "Cube"],
        ["prop", "link_state"],
        ["operator", "lighthouse.remove_receiver", "", dict(remove, receiver="Cube")],
        ["label", "sphere"],
        ["prop", "link_state"],
        ["operator", "lighthouse.remove_receiver", "", dict(remove, receiver="sphere")],
    ]


def test_clear_is_greyed_out_when_empty_and_the_shared_label_shows_only_when_shared():
    result = run(prelude=RECORDER + textwrap.dedent(DRAW_SECTION), snippet="""
        empty = section(key)
        rim = add_light("Rim")
        select(cube)
        bpy.ops.lighthouse.link_receivers(name="Key")
        rim.light_linking.receiver_collection = key.light_linking.receiver_collection
        report([empty, section(key)[3:5]])
    """)

    assert result == [
        BUTTONS + [["operator", "lighthouse.clear_receivers", "Clear", LIGHT, "disabled"]],
        [["operator", "lighthouse.clear_receivers", "Clear", LIGHT],
         ["label", "Shared with Rim (2 lights)"]],
    ]


def test_exclude_selected_flips_listed_objects_and_adds_new_ones_as_exclude():
    result = run("""
        select(cube, sphere)
        bpy.ops.lighthouse.link_receivers(name="Key")
        select(cube, plane)
        bpy.ops.lighthouse.link_receivers(name="Key", state='EXCLUDE')
        report(listed())
    """)

    assert result == [["Cube", "OBJECT", "EXCLUDE"], ["Plane", "OBJECT", "EXCLUDE"],
                      ["sphere", "OBJECT", "INCLUDE"]]


def test_setting_a_rows_link_state_changes_the_listed_state():
    result = run("""
        select(cube)
        bpy.ops.lighthouse.link_receivers(name="Key")
        receivers(key)[0].link.light_linking.link_state = 'EXCLUDE'
        report(listed())
    """)

    assert result == [["Cube", "OBJECT", "EXCLUDE"]]


def test_clear_empties_the_shared_collection_and_keeps_it_assigned():
    result = run("""
        rim = add_light("Rim")
        select(cube, sphere)
        bpy.ops.lighthouse.link_receivers(name="Key")
        props = bpy.data.collections.new("Props")
        key.light_linking.receiver_collection.children.link(props)
        rim.light_linking.receiver_collection = key.light_linking.receiver_collection
        status = sorted(bpy.ops.lighthouse.clear_receivers(name="Key"))
        collection = key.light_linking.receiver_collection
        report([status, collection.name, listed(), rim.light_linking.receiver_collection == collection,
                len(receivers(rim))])
    """)

    assert result == [["FINISHED"], "Light Linking for Key", [], True, 0]


def test_shared_label_names_the_other_lights_and_counts_all():
    result = run("""
        from lighthouse.lights import shared_label
        rim, fill, solo = add_light("Rim"), add_light("Fill"), add_light("Solo")
        select(cube)
        bpy.ops.lighthouse.link_receivers(name="Key")
        for light in (rim, fill):
            light.light_linking.receiver_collection = key.light_linking.receiver_collection
        select(cube)
        bpy.ops.lighthouse.link_receivers(name="Solo")
        report([shared_label(fill), shared_label(solo), shared_label(plane)])
    """)

    assert result == ["Shared with Key, Rim (3 lights)", "", ""]


def test_linking_tooltip_summarizes_included_and_excluded_counts():
    result = run("""
        from lighthouse.lights import linking_tooltip
        report([linking_tooltip(*case) for case in
                [(3, 0), (3, 1), (0, 2), (1, 0), (0, 1), (0, 0), (2, 1, 1, 0), (0, 0, 0, 1)]])
    """)

    assert result == [
        "Lights only 3 objects",
        "Lights only 3 objects, excludes 1",
        "Excludes 2 objects",
        "Lights only 1 object",
        "Excludes 1 object",
        "",
        "Lights only 2 objects and 1 collection, excludes 1",
        "Excludes 1 collection",
    ]


def test_linking_info_opens_the_details_closing_others_and_never_closes_them():
    result = run("""
        from lighthouse.lights import details_open
        rim = add_light("Rim")
        settings = bpy.context.window_manager.lighthouse
        bpy.ops.lighthouse.toggle_details(name="Rim")
        def open_now():
            return [details_open(settings, key), details_open(settings, rim)]
        out = []
        for _ in range(2):
            status = sorted(bpy.ops.lighthouse.light_linking_info(name="Key"))
            out.append([status, open_now()])
        report(out)
    """)

    assert result == [[["FINISHED"], [True, False]], [["FINISHED"], [True, False]]]


def test_rows_draw_the_link_button_after_info_and_before_power_only_with_receivers():
    result = run(prelude=RECORDER, snippet="""
        rim, fill = add_light("Rim"), add_light("Fill")
        twin = bpy.data.objects.new("Twin", key.data)
        bpy.context.scene.collection.objects.link(twin)
        select(cube)
        bpy.ops.lighthouse.link_receivers(name="Key")
        select(cube, sphere)
        bpy.ops.lighthouse.link_receivers(name="Rim", state='EXCLUDE')
        fill.light_linking.receiver_collection = bpy.data.collections.new("Empty")
        def panel_draw(holder, context):
            panel = bpy.types.LIGHTHOUSE_PT_lights
            methods = {name: value for name, value in vars(panel).items() if name.startswith("draw")}
            panel.draw(type("Panel", (), {**methods, "layout": holder.layout})(), context)
        entries = drawn(panel_draw)
        def between_name_and_power(name):
            start = next(i for i, e in enumerate(entries) if e[1:3] == ["lighthouse.select_light", name])
            end = next(i for i, e in enumerate(entries) if i > start and e[:2] == ["prop", "energy"])
            return [[e[1]] + e[3:] for e in entries[start + 1:end]]
        report({name: between_name_and_power(name) for name in ("Key", "Rim", "Fill", "Twin")})
    """)

    link = {"name": "Key", "library": "", "included": 1, "excluded": 0,
            "included_collections": 0, "excluded_collections": 0}
    assert result == {
        "Key": [["lighthouse.light_info", {"other_users": 1, "other_collections": 0}],
                ["lighthouse.light_linking_info", link]],
        "Rim": [["lighthouse.light_linking_info", dict(link, name="Rim", included=0, excluded=2)]],
        "Fill": [],
        "Twin": [["lighthouse.light_info", {"other_users": 1, "other_collections": 0}]],
    }
