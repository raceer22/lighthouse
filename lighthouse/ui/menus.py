import bpy

from ..lights import find_object, id_key, is_solo_target, is_read_only, light_scope, scope_label
from ..common import preset_items, LIGHT_TYPES, scene_or_collection, light_muted, target_collection
from ..operators.groups import LIGHTHOUSE_OT_new_collection, LIGHTHOUSE_OT_set_active_collection
from ..operators.lights import (
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_OT_rename_light,
    LIGHTHOUSE_OT_delete_lights,
    LIGHTHOUSE_OT_duplicate_lights,
    LIGHTHOUSE_OT_add_light,
    LIGHTHOUSE_OT_mute_lights,
)
from ..operators.presets import LIGHTHOUSE_OT_apply_preset
from ..operators.solo import LIGHTHOUSE_OT_solo_light


class LIGHTHOUSE_MT_new_light(bpy.types.Menu):
    """Add a light at the 3D cursor"""
    bl_idname = "LIGHTHOUSE_MT_new_light"
    bl_label = "New Light"

    def draw(self, context):
        # Set by layout.context_pointer_set() in the group menu. Without it, lights go to the active collection.
        collection = getattr(context, "lighthouse_collection", None)
        for key, label, _description, icon, _number in LIGHT_TYPES:
            op = self.layout.operator(LIGHTHOUSE_OT_add_light.bl_idname, text=label, icon=icon)
            op.type = key
            if collection is not None:
                target_collection(op, context, collection)


class LIGHTHOUSE_MT_new(bpy.types.Menu):
    """Add a light or a collection in the active collection"""
    bl_idname = "LIGHTHOUSE_MT_new"
    bl_label = "New"

    def draw(self, context):
        entries = self.layout.column()
        entries.enabled = not is_read_only(context.view_layer.active_layer_collection.collection)
        entries.menu(LIGHTHOUSE_MT_new_light.bl_idname, text="New Light", icon='LIGHT')
        entries.operator(LIGHTHOUSE_OT_new_collection.bl_idname, text="New Collection", icon='COLLECTION_NEW')


def draw_group_menu(self, context):
    """Prepended to Blender's right-click menu (UI_MT_button_context_menu): New Light and New Collection
    for the collection whose header name button (or the Scene Collection row's) is under the cursor."""
    op = getattr(context, "button_operator", None)
    if op is None or op.bl_rna.identifier != LIGHTHOUSE_OT_set_active_collection.bl_rna.identifier:
        return
    collection = scene_or_collection(context, op.name, op.library)
    if collection is None:
        return
    entries = self.layout.column()
    entries.enabled = not is_read_only(collection)
    entries.context_pointer_set("lighthouse_collection", collection)
    entries.menu(LIGHTHOUSE_MT_new_light.bl_idname, text="New Light", icon='LIGHT')
    target_collection(
        entries.operator(LIGHTHOUSE_OT_new_collection.bl_idname, text="New Collection", icon='COLLECTION_NEW'),
        context, collection)
    self.layout.separator()


class LIGHTHOUSE_MT_apply_preset(bpy.types.Menu):
    """The light right-click menu's Apply Preset submenu, for context.lighthouse_light and its selection."""
    bl_idname = "LIGHTHOUSE_MT_apply_preset"
    bl_label = "Apply Preset"

    def draw(self, context):
        obj = context.lighthouse_light
        for key, label, *_ in preset_items(self, context):
            op = target_light(self.layout.operator(LIGHTHOUSE_OT_apply_preset.bl_idname, text=label), obj)
            op.preset = key


def draw_light_menu(self, context):
    """Prepended to Blender's right-click menu (UI_MT_button_context_menu) for the light whose row name
    button is under the cursor: Rename and Frame (that light), Duplicate, Duplicate Linked, Delete,
    Apply Preset and Mute (its selection, see light_scope), Solo and Add to Solo (that light)."""
    op = getattr(context, "button_operator", None)
    if op is None or op.bl_rna.identifier != LIGHTHOUSE_OT_select_light.bl_rna.identifier:
        return
    obj = find_object(context.view_layer, op.name, op.library)
    if obj is None:
        return
    layout = self.layout
    rename = layout.row()
    rename.enabled = not is_read_only(obj)
    target_light(rename.operator(LIGHTHOUSE_OT_rename_light.bl_idname, text="Rename"), obj)
    # Exec, so select_light keeps action FRAME instead of reading it from the click's modifier keys.
    frame = layout.row()
    frame.operator_context = 'EXEC_DEFAULT'
    target_light(frame.operator(LIGHTHOUSE_OT_select_light.bl_idname, text="Frame"), obj).action = 'FRAME'
    count = len(light_scope(context.view_layer, obj))
    target_light(layout.operator(LIGHTHOUSE_OT_duplicate_lights.bl_idname, text=scope_label("Duplicate", count)), obj)
    target_light(layout.operator(LIGHTHOUSE_OT_duplicate_lights.bl_idname,
                                 text=scope_label("Duplicate Linked", count)), obj).linked = True
    target_light(layout.operator(LIGHTHOUSE_OT_delete_lights.bl_idname, text=scope_label("Delete", count)), obj)
    layout.context_pointer_set("lighthouse_light", obj)
    layout.menu(LIGHTHOUSE_MT_apply_preset.bl_idname, text="Apply Preset", icon='PRESET')
    layout.menu(LIGHTHOUSE_MT_new_light.bl_idname, text="New Light", icon='LIGHT')
    verb = "Unmute" if light_muted(obj) else "Mute"
    target_light(layout.operator(LIGHTHOUSE_OT_mute_lights.bl_idname, text=scope_label(verb, count)), obj)
    solo = context.scene.lighthouse_solo
    soloed = is_solo_target(solo, obj)
    target_light(layout.operator(LIGHTHOUSE_OT_solo_light.bl_idname, text="Exit Solo" if soloed else "Solo"), obj)
    target_light(layout.operator(LIGHTHOUSE_OT_solo_light.bl_idname,
                                 text="Remove from Solo" if soloed else "Add to Solo"), obj).extend = True
    layout.separator()


def target_light(op, obj):
    """Point a light operator's name and library at obj."""
    op.name, op.library = id_key(obj)
    return op


classes = (
    LIGHTHOUSE_MT_new_light,
    LIGHTHOUSE_MT_apply_preset,
    LIGHTHOUSE_MT_new,
)
