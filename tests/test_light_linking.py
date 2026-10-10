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


def test_open_details_end_with_link_selected_and_one_removable_row_per_receiver():
    result = run(prelude=RECORDER, snippet="""
        from lighthouse.lights import RowState
        select(cube, sphere)
        bpy.ops.lighthouse.link_receivers(name="Key")
        state = RowState(dimmed=False, read_only=False, muted=False, soloed=False)
        def draw(self, context):
            bpy.types.LIGHTHOUSE_PT_lights.draw_details(self, key, state, context.scene.render.engine)
        entries = drawn(draw)
        report(entries[[e[:2] for e in entries].index(["label", "Light Linking"]):])
    """)

    remove = {"name": "Key", "library": "", "receiver_library": "", "kind": "OBJECT"}
    assert result == [
        ["label", "Light Linking"],
        ["operator", "lighthouse.link_receivers", "Link Selected", {"name": "Key", "library": ""}],
        ["label", "Cube"],
        ["operator", "lighthouse.remove_receiver", "", dict(remove, receiver="Cube")],
        ["label", "sphere"],
        ["operator", "lighthouse.remove_receiver", "", dict(remove, receiver="sphere")],
    ]
