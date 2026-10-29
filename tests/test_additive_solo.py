import textwrap

from blender_runner import RECORDER, run_in_blender
from test_light_menu import BUTTON

HELPERS = """
import lighthouse
lighthouse.register()
from lighthouse.lights import world_setup
empty_scene()
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
scene = bpy.context.scene
parent = bpy.data.collections.new("Parent")
scene.collection.children.link(parent)
group = bpy.data.collections.new("Group")
parent.children.link(group)
inner = bpy.data.collections.new("Inner")
group.children.link(inner)

def light(name, collection=None):
    obj = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT"))
    (collection or scene.collection).objects.link(obj)
    return obj

a, b, c = light("A"), light("B"), light("C")
g1, g2 = light("G1", group), light("G2", inner)
rim = light("Rim")
parent.hide_viewport = parent.hide_render = True
c.hide_viewport = c.hide_render = True
bpy.context.view_layer.update()
solo = scene.lighthouse_solo
ALL = (a, b, c, g1, g2, rim)

def shown():
    return sorted(o.name for o in ALL if not (o.hide_viewport or o.hide_render))

def solo_light(name, extend=False):
    bpy.ops.lighthouse.solo_light(name=name, library="", extend=extend)

def soloed():
    return sorted((t.object or t.collection).name for t in solo.targets)
"""


def run(snippet, setup=""):
    return run_in_blender(HELPERS + setup + textwrap.dedent(snippet))


def test_extend_adds_a_light_and_again_removes_it():
    result = run("""
        solo_light("A")
        solo_light("B", extend=True)
        both = [shown(), soloed()]
        solo_light("A", extend=True)
        report({"both": both, "after removing A": [shown(), soloed()]})
    """)

    assert result == {"both": [["A", "B"], ["A", "B"]], "after removing A": [["B"], ["B"]]}


def test_extend_on_the_last_soloed_light_ends_solo_and_restores_the_snapshot():
    result = run("""
        solo_light("A")
        solo_light("A", extend=True)
        report({"active": solo.active, "shown": shown(), "parent hidden": parent.hide_viewport})
    """)

    assert result == {"active": False, "shown": ["A", "B", "G1", "G2", "Rim"], "parent hidden": True}


def test_extend_with_a_group_shows_its_lights_and_unhides_its_parents():
    result = run("""
        solo_light("A")
        bpy.ops.lighthouse.solo_group(name="Group", library="", extend=True)
        report({"shown": shown(), "parent hidden": [parent.hide_viewport, parent.hide_render],
                "soloed": soloed(), "group pressed": lighthouse.lights.group_soloed(scene, group)})
    """)

    assert result == {"shown": ["A", "G1", "G2"], "parent hidden": [False, False],
                      "soloed": ["A", "Group"], "group pressed": True}


def test_a_plain_click_replaces_several_targets_and_again_ends_solo():
    result = run("""
        solo_light("A")
        solo_light("B", extend=True)
        solo_light("A")
        only_a = [shown(), soloed()]
        solo_light("A")
        report({"plain": only_a, "again": solo.active})
    """)

    assert result == {"plain": [["A"], ["A"]], "again": False}


def test_extend_on_the_world_is_a_world_solo_and_extend_on_a_lamp_leaves_it():
    result = run("""
        background = world_setup(scene).background
        background.mute = True
        solo_light("A")
        solo_light("B", extend=True)
        bpy.ops.lighthouse.solo_world(extend=True)
        world = {"soloed": soloed(), "world": solo.world_soloed, "shown": shown(), "mute": background.mute}
        solo_light("B", extend=True)
        report({"world": world, "lamp": [solo.world_soloed, soloed(), background.mute]})
    """)

    assert result == {
        "world": {"soloed": [], "world": True, "shown": [], "mute": False},
        "lamp": [False, ["B"], True],
    }


def test_exit_solo_description_names_up_to_three_targets_and_drops_deleted_ones():
    result = run("""
        describe = lambda: bpy.types.LIGHTHOUSE_OT_exit_solo.description(bpy.context, None).split(":")[0]
        for name in ("A", "B", "Rim"):
            solo_light(name, extend=True)
        three = describe()
        bpy.ops.lighthouse.solo_group(name="Group", library="", extend=True)
        four = describe()
        bpy.data.objects.remove(a)
        bpy.data.objects.remove(rim)
        bpy.data.objects.remove(b)
        bpy.data.collections.remove(inner)
        bpy.data.collections.remove(group)
        report([three, four, describe()])
    """)

    assert result == ["Exit Solo (A, B, Rim)", "Exit Solo (A, B, Rim, …)", "Exit Solo (deleted)"]


def test_add_to_solo_in_the_menu_adds_the_clicked_light_and_then_offers_removal():
    result = run("""
        def entry():
            return [e for e in menu_for(row("B"))[:-1] if e[2] in ("Add to Solo", "Remove from Solo")]
        solo_light("A")
        before = entry()
        solo_light("B", extend=True)
        report({"before": before, "after": entry(), "soloed": soloed()})
    """, RECORDER + BUTTON)

    assert result == {
        "before": [["operator", "lighthouse.solo_light", "Add to Solo", {"name": "B", "library": "", "extend": True}]],
        "after": [["operator", "lighthouse.solo_light", "Remove from Solo", {"name": "B", "library": "", "extend": True}]],
        "soloed": ["A", "B"],
    }
