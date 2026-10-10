import textwrap

from blender_runner import run_in_blender

HELPERS = """
import lighthouse
from lighthouse.lights import empty_message
lighthouse.register()

def message(name_filter="", type_filter='ALL'):
    return empty_message(bpy.context.view_layer, name_filter, type_filter)
"""


def run(snippet):
    return run_in_blender(HELPERS + textwrap.dedent(snippet))


def test_empty_message_names_why_the_list_is_empty():
    result = run("""
        empty_scene()
        no_lights = message()
        add_mesh("Cube")
        add_light("Key", "SPOT")
        report({
            "no_lights": no_lights,
            "search": message(name_filter="fill"),
            "type": message(type_filter='SUN'),
            "listed": message(),
        })
    """)

    assert result == {
        "no_lights": "No lights in this view layer",
        "search": "No lights match the filter(s)",
        "type": "No lights match the filter(s)",
        "listed": None,
    }


def test_lights_inside_collapsed_groups_do_not_make_the_list_empty():
    result = run("""
        empty_scene()
        lamps = bpy.data.collections.new("Lamps")
        bpy.context.scene.collection.children.link(lamps)
        bulb = add_light("Bulb")
        bpy.context.scene.collection.objects.unlink(bulb)
        lamps.objects.link(bulb)
        bpy.context.view_layer.update()
        lamps.lighthouse_collapsed = True
        report(message())
    """)

    assert result is None


def test_clear_filters_resets_search_and_type_filter():
    result = run("""
        filters = bpy.context.window_manager.lighthouse
        filters.name_filter = "key"
        filters.type_filter = 'SPOT'
        bpy.ops.lighthouse.clear_filters()
        report([filters.name_filter, filters.type_filter,
                "UNDO" in bpy.types.LIGHTHOUSE_OT_clear_filters.bl_options])
    """)

    assert result == ["", "ALL", False]
