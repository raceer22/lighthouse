# Copyright (C) 2026 raceer22
# Licensed under the GNU General Public License v3 or later (GPL-3.0-or-later)
import bpy

from . import operators, preferences, properties, ui
from .common import NEW_LIGHT_MODES
from .handlers import register_last_light, unregister_last_light, migrate_solo_targets
from .properties import LIGHTHOUSE_PG_settings, LIGHTHOUSE_PG_solo
from .ui.menus import draw_group_menu, draw_light_menu


classes = properties.classes + operators.classes + ui.classes + preferences.classes


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.lighthouse = bpy.props.PointerProperty(type=LIGHTHOUSE_PG_settings)
    bpy.types.Scene.lighthouse_solo = bpy.props.PointerProperty(type=LIGHTHOUSE_PG_solo)
    bpy.types.Scene.lighthouse_new_lights = bpy.props.EnumProperty(
        name="New Lights",
        description="Whether lights added by Lighthouse start in Color or in Kelvin in this file",
        items=NEW_LIGHT_MODES,
        default='FOLLOW',
    )
    bpy.types.Collection.lighthouse_collapsed = bpy.props.BoolProperty(
        name="Collapsed",
        description="Hide this collection's lights and sub-collections in the Lights list",
    )
    bpy.types.Collection.lighthouse_lights_collapsed = bpy.props.BoolProperty(
        name="Lights Folded",
        description="Hide this collection's own lights in the Lights list, keeping its sub-collections",
    )
    bpy.types.UI_MT_button_context_menu.prepend(draw_group_menu)
    bpy.app.handlers.load_post.append(migrate_solo_targets)
    bpy.types.UI_MT_button_context_menu.prepend(draw_light_menu)
    register_last_light()


def unregister():
    bpy.app.handlers.load_post.remove(migrate_solo_targets)
    bpy.types.UI_MT_button_context_menu.remove(draw_light_menu)
    bpy.types.UI_MT_button_context_menu.remove(draw_group_menu)
    del bpy.types.Collection.lighthouse_lights_collapsed
    del bpy.types.Collection.lighthouse_collapsed
    del bpy.types.Scene.lighthouse_new_lights
    del bpy.types.Scene.lighthouse_solo
    del bpy.types.WindowManager.lighthouse
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unregister_last_light()
