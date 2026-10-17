import textwrap

from blender_runner import RECORDER, run_in_blender

SETUP = """
import lighthouse
lighthouse.register()
empty_scene()
layer = bpy.context.view_layer
bpy.context.scene.render.engine = 'CYCLES'  # no light linking engine note

def panel_draw(holder, context):
    bpy.types.LIGHTHOUSE_PT_active_light.draw(holder, context)

def make_active(obj):
    for other in layer.objects:
        other.select_set(False)
    if obj is not None:
        obj.select_set(True)
    layer.objects.active = obj
"""


def run(snippet, prelude=""):
    return run_in_blender(RECORDER + SETUP + prelude + textwrap.dedent(snippet))


def test_with_a_mesh_or_nothing_active_it_asks_to_select_a_light_and_never_hides():
    result = run("""
        add_light("Key")
        make_active(add_mesh("Cube"))
        mesh = drawn(panel_draw)
        make_active(None)
        nothing = drawn(panel_draw)
        panel = bpy.types.LIGHTHOUSE_PT_active_light
        report([mesh, nothing, panel.bl_label, not hasattr(panel, "poll") or panel.poll(bpy.context)])
    """)

    assert result == [[["label", "Select a light"]], [["label", "Select a light"]], "Active Light", True]


LIST_DRAW = """
def lights_panel_draw(holder, context):
    panel = bpy.types.LIGHTHOUSE_PT_lights
    methods = {name: value for name, value in vars(panel).items() if name.startswith("draw")}
    panel.draw(type("Panel", (), {**methods, "layout": holder.layout})(), context)

def expanded_row(name, next_name):
    \"\"\"What the Lights panel draws for a light with its details open, after its details toggle.\"\"\"
    entries = drawn(lights_panel_draw)
    start = next(i for i, e in enumerate(entries) if e[1:2] == ["lighthouse.toggle_details"] and e[-1]["name"] == name)
    end = next(i for i, e in enumerate(entries) if e[1:2] == ["lighthouse.toggle_details"] and e[-1]["name"] == next_name)
    return entries[start + 1:end]
"""


def test_with_a_light_active_it_draws_the_same_controls_and_details_as_its_expanded_row():
    result = run(prelude=LIST_DRAW, snippet="""
        key = add_light("Key", "AREA")
        twin = bpy.data.objects.new("Twin", key.data)
        bpy.context.scene.collection.objects.link(twin)
        make_active(key)
        bpy.ops.lighthouse.toggle_details(name="Key")
        panel = drawn(panel_draw)
        row = expanded_row("Key", "Twin")
        report([panel == row, [e[:3] for e in panel[:3]], ["prop", "name"] in panel])
    """)

    assert result == [True, [["prop", "type"], ["operator", "lighthouse.select_light", "Key"],
                             ["operator", "lighthouse.light_info", ""]], True]


def test_an_active_library_light_is_disabled_and_a_muted_one_is_dimmed(tmp_path):
    result = run(f"""
        library_light = add_light("Library")
        path = {str(tmp_path / "library.blend")!r}
        bpy.data.libraries.write(path, {{library_light}})
        bpy.data.objects.remove(library_light)
        with bpy.data.libraries.load(path, link=True) as (src, dst):
            dst.objects = ["Library"]
        bpy.context.scene.collection.objects.link(dst.objects[0])
        muted = add_light("Muted")
        muted.hide_render = muted.hide_viewport = True
        def flags(obj, *wanted):
            make_active(obj)
            entries = drawn(panel_draw)
            return {{e[1]: e[-1] if isinstance(e[-1], str) and e[-1] in ("disabled", "inactive") else "enabled"
                    for e in entries if e[1] in wanted}}
        report([flags(dst.objects[0], "type", "energy", "color", "name", "lighthouse.mute_light", "lighthouse.solo_light"),
                flags(muted, "energy", "lighthouse.solo_light")])
    """)

    assert result == [
        {"type": "disabled", "energy": "disabled", "color": "disabled", "name": "disabled",
         "lighthouse.mute_light": "enabled", "lighthouse.solo_light": "enabled"},
        {"energy": "inactive", "lighthouse.solo_light": "inactive"},
    ]
