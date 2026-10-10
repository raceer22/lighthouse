import textwrap

from blender_runner import RECORDER, blender_version, run_in_blender

SETUP = """
import lighthouse
lighthouse.register()
empty_scene()
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
layer = bpy.context.view_layer
filters = bpy.context.window_manager.lighthouse
add_light("Key")
props = bpy.data.collections.new("Props")
bpy.context.scene.collection.children.link(props)
bpy.ops.lighthouse.set_active_collection(name="Props")

def panel_draw(holder, context):
    # The panel's draw calls its own draw_* methods, so give the stand-in those too.
    panel = bpy.types.LIGHTHOUSE_PT_lights
    methods = {name: value for name, value in vars(panel).items() if name.startswith("draw")}
    panel.draw(type("Panel", (), {**methods, "layout": holder.layout})(), context)

def header():
    # Everything the panel draws before the type filter row is the header row.
    entries = drawn(panel_draw)
    return entries[:entries.index(["prop", "type_filter"])]
"""


def run(snippet, setup=""):
    return run_in_blender(RECORDER + SETUP + setup + textwrap.dedent(snippet))


def test_header_draws_one_add_menu_and_no_separate_add_buttons_in_every_mode():
    result = run("""
        def adders():
            return [e for e in header()
                    if "lighthouse.add_light" in e or "lighthouse.new_collection" in e or "LIGHTHOUSE_MT_new" in e]
        grouped = adders()
        filters.grouped = False
        flat = adders()
        filters.grouped = True
        filters.name_filter = "Key"
        searching = adders()
        report({"grouped": grouped, "flat": flat, "searching": searching})
    """)

    menu = [["menu", "LIGHTHOUSE_MT_new", "", "ADD"]]
    assert result == {"grouped": menu, "flat": menu, "searching": menu}


def test_header_row_has_one_button_fewer_than_with_two_add_buttons():
    # Search, Grouped, Show Empty, Toggle All, Reveal, Exit Solo, + menu, and on 5.0+ the
    # Color/Kelvin toggle in the slot New Collection left (v5 task 03).
    result = run("""
        report(len(header()))
    """)

    assert result == (8 if blender_version() >= (5, 0) else 7)


def test_new_menu_adds_to_the_active_collection():
    result = run("""
        report(drawn(bpy.types.LIGHTHOUSE_MT_new.draw))
    """)

    assert result == [
        ["menu", "LIGHTHOUSE_MT_new_light", "New Light", "LIGHT"],
        ["operator", "lighthouse.new_collection", "New Collection"],
    ]


def test_new_menu_is_greyed_out_when_the_active_collection_is_linked():
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
        report([entry[0] + (" disabled" if entry[-1] == "disabled" else "")
                for entry in drawn(bpy.types.LIGHTHOUSE_MT_new.draw)])
    """)

    assert result == ["menu disabled", "operator disabled"]
