import textwrap

from blender_runner import RECORDER, run_in_blender

HELPERS = """
import lighthouse
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
props = new_collection("Props")
set_ = new_collection("Set")
bpy.ops.lighthouse.set_active_collection(name="Props")
"""


LINKED = """
import os, tempfile
library = os.path.join(tempfile.mkdtemp(), "library.blend")
linked = bpy.data.collections.new("Linked")
bpy.data.libraries.write(library, {linked})
bpy.data.collections.remove(linked)
with bpy.data.libraries.load(library, link=True) as (source, target):
    target.collections = ["Linked"]
linked = target.collections[0]
bpy.context.scene.collection.children.link(linked)
layer.update()
"""


# A header's name button as context.button_operator sees it in the right-click menu.
BUTTON = """
def button(identifier, **props):
    return type("Props", (), {"bl_rna": type("RNA", (), {"identifier": identifier})(), **props})()

def header(name, library=""):
    return button("LIGHTHOUSE_OT_set_active_collection", name=name, library=library)

def menu_for(button_operator):
    return drawn(lighthouse.draw_group_menu, FakeContext(button_operator=button_operator))
"""


def run(snippet, setup=""):
    return run_in_blender(HELPERS + setup + textwrap.dedent(snippet))


def test_new_light_with_a_target_adds_there_and_makes_it_active():
    result = run("""
        bpy.ops.lighthouse.add_light(type='SPOT', name="Set", use_active=False)
        light = layer.objects.active
        report({
            "in": [c.name for c in light.users_collection],
            "type": light.data.type,
            "selected": [o.name for o in layer.objects if o.select_get()],
            "active collection": active_collection().name,
        })
    """)

    assert result == {"in": ["Set"], "type": "SPOT", "selected": ["Spot"], "active collection": "Set"}


def test_a_light_added_without_a_target_goes_to_the_active_collection_not_the_last_target():
    result = run("""
        bpy.ops.lighthouse.add_light(type='SPOT', name="Set", use_active=False)
        after_target = [c.name for c in layer.objects.active.users_collection]
        bpy.ops.lighthouse.add_light(type='POINT')
        follow_up = [c.name for c in layer.objects.active.users_collection]
        bpy.ops.lighthouse.set_active_collection(name="Props")
        bpy.ops.lighthouse.add_light(type='POINT')
        report([after_target, follow_up, [c.name for c in layer.objects.active.users_collection]])
    """)

    assert result == [["Set"], ["Set"], ["Props"]]


def test_new_light_targeting_the_scene_collection_adds_there_and_makes_it_active():
    result = run("""
        bpy.ops.lighthouse.add_light(type='POINT', name="", use_active=False)
        report({
            "in scene collection": layer.objects.active.name in bpy.context.scene.collection.objects,
            "master active": layer.active_layer_collection == layer.layer_collection,
        })
    """)

    assert result == {"in scene collection": True, "master active": True}


def test_target_properties_are_never_remembered_for_the_next_call_from_the_ui():
    # bpy.ops from Python never reuses last properties, so the flag is the only thing to check headless.
    result = run("""
        report({
            op: sorted(p.identifier for p in getattr(bpy.ops.lighthouse, op).get_rna_type().properties
                       if p.is_skip_save)
            for op in ("add_light", "new_collection")
        })
    """)

    assert result == {"add_light": ["library", "name", "use_active"],
                      "new_collection": ["library", "name", "use_active"]}


def test_new_collection_with_a_target_goes_inside_it_and_the_new_one_becomes_active():
    result = run("""
        bpy.ops.lighthouse.new_collection(name="Set", use_active=False, new_name="Fill")
        report({"children of Set": [c.name for c in set_.children], "active": active_collection().name})
    """)

    assert result == {"children of Set": ["Fill"], "active": "Fill"}


def test_a_missing_target_cancels_and_a_linked_one_is_refused_without_adding_anything():
    result = run("""
        def count():
            return len(bpy.data.objects), len(bpy.data.collections)

        def outcome(call):
            before = count()
            try:
                status = sorted(call())
            except RuntimeError as e:
                status = ["read-only" if "Linked is read-only" in str(e) else str(e)]
            return status + [count() == before]

        linked_path = linked.library.filepath
        report({
            "light, missing": outcome(lambda: bpy.ops.lighthouse.add_light(name="Nope", use_active=False)),
            "light, linked": outcome(lambda: bpy.ops.lighthouse.add_light(
                name="Linked", library=linked_path, use_active=False)),
            "collection, missing": outcome(lambda: bpy.ops.lighthouse.new_collection(
                name="Nope", use_active=False)),
            "collection, linked": outcome(lambda: bpy.ops.lighthouse.new_collection(
                name="Linked", library=linked_path, use_active=False)),
        })
    """, LINKED)

    assert result == {
        "light, missing": ["CANCELLED", True],
        "light, linked": ["read-only", True],
        "collection, missing": ["CANCELLED", True],
        "collection, linked": ["read-only", True],
    }


def test_a_header_name_button_gets_new_light_and_new_collection_above_a_separator():
    result = run("""
        report({
            "Set": menu_for(header("Set")),
            "Scene Collection": menu_for(header("")),
        })
    """, RECORDER + BUTTON)

    assert result == {
        "Set": [
            ["context_pointer_set", "lighthouse_collection", "Set"],
            ["menu", "LIGHTHOUSE_MT_new_light", "New Light", "LIGHT"],
            ["operator", "lighthouse.new_collection", "New Collection",
             {"name": "Set", "library": "", "use_active": False}],
            ["separator"],
        ],
        "Scene Collection": [
            ["context_pointer_set", "lighthouse_collection", "Scene Collection"],
            ["menu", "LIGHTHOUSE_MT_new_light", "New Light", "LIGHT"],
            ["operator", "lighthouse.new_collection", "New Collection",
             {"name": "", "library": "", "use_active": False}],
            ["separator"],
        ],
    }


def test_other_buttons_get_no_lighthouse_entries():
    result = run("""
        report({
            "light row": menu_for(button("LIGHTHOUSE_OT_select_light", name="Key", library="")),
            "header icon": menu_for(button("LIGHTHOUSE_OT_select_group", name="Set", library="")),
            "no operator": menu_for(None),
        })
    """, RECORDER + BUTTON)

    assert result == {"light row": [], "header icon": [], "no operator": []}


def test_a_linked_collection_gets_the_entries_greyed_out():
    result = run("""
        report([entry[0] + (" disabled" if entry[-1] == "disabled" else "")
                for entry in menu_for(header("Linked", linked.library.filepath))])
    """, LINKED + RECORDER + BUTTON)

    assert result == ["context_pointer_set disabled", "menu disabled", "operator disabled", "separator"]


def test_new_light_menu_adds_to_the_collection_it_was_given_or_else_the_active_one():
    result = run("""
        def lights(**members):
            return [entry[2:] for entry in drawn(bpy.types.LIGHTHOUSE_MT_new_light.draw, FakeContext(**members))]
        report({
            "Set": lights(lighthouse_collection=set_),
            "Scene Collection": lights(lighthouse_collection=bpy.context.scene.collection)[0],
            "none": lights(),
        })
    """, RECORDER)

    assert result == {
        "Set": [[label, {"type": key, "name": "Set", "library": "", "use_active": False}]
                for key, label in (("POINT", "Point"), ("SUN", "Sun"), ("SPOT", "Spot"), ("AREA", "Area"))],
        "Scene Collection": ["Point", {"type": "POINT", "name": "", "library": "", "use_active": False}],
        "none": [["Point", {"type": "POINT"}], ["Sun", {"type": "SUN"}],
                 ["Spot", {"type": "SPOT"}], ["Area", {"type": "AREA"}]],
    }


def test_the_group_menu_is_in_blenders_right_click_menu_only_while_registered():
    result = run("""
        def hooked():
            menu = bpy.types.UI_MT_button_context_menu
            return lighthouse.draw_group_menu in getattr(menu.draw, "_draw_funcs", [])
        registered = hooked()
        lighthouse.unregister()
        report([registered, hooked()])
    """)

    assert result == [True, False]
