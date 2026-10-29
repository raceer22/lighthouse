import bpy

from ..lights import find_object, light_scope
from ..presets import (
    apply_preset,
    delete_user_preset,
    preset_from_light,
    preset_path,
    preset_summary,
    restore_default_presets,
    save_user_preset,
    USER_PREFIX,
)
from ..common import (
    presets_folder,
    cached_user_presets,
    clear_user_presets_cache,
    all_presets,
    preset_items,
    _lights_in_scope,
)


class LIGHTHOUSE_OT_apply_preset(bpy.types.Operator):
    """Set power, color, soft size, exposure and temperature of the selected lights from a preset.
    Lights of a type the preset doesn't suit are skipped"""
    bl_idname = "lighthouse.apply_preset"
    bl_label = "Apply Light Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset: bpy.props.EnumProperty(name="Preset", items=preset_items)
    # Set by the light right-click menu: the clicked light, whose light_scope() gets the preset.
    # Empty (the Presets panel) means the selected lights.
    name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    library: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        if self.name:
            obj = find_object(context.view_layer, self.name, self.library)
            if obj is None:
                return {'CANCELLED'}
            lights, empty = light_scope(context.view_layer, obj), ""
        else:
            lights, empty = _lights_in_scope(context, 'SELECTED')
        if not lights:
            self.report({'WARNING'}, empty)
            return {'CANCELLED'}
        preset = all_presets()[self.preset]
        changed, *skipped = apply_preset(lights, preset)
        if not changed:
            self.report({'WARNING'}, preset_summary(preset, changed, *skipped))
            return {'CANCELLED'}
        self.report({'INFO'}, preset_summary(preset, changed, *skipped))
        return {'FINISHED'}


class LIGHTHOUSE_OT_save_preset(bpy.types.Operator):
    """Save the active light's power, color, soft size, exposure and temperature as a preset
    available in every file"""
    bl_idname = "lighthouse.save_preset"
    bl_label = "Save Light Preset"

    name: bpy.props.StringProperty(name="Name", description="Preset name")
    overwrite: bpy.props.BoolProperty(name="Overwrite", description="Replace the existing preset with this name")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'LIGHT'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def exists(self):
        name = self.name.strip()
        return bool(name) and preset_path(presets_folder(), name).exists()

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "name")
        if self.exists():
            layout.label(text="A preset with this name exists", icon='ERROR')
            layout.prop(self, "overwrite")

    def execute(self, context):
        name = self.name.strip()
        if not name:
            self.report({'ERROR'}, "Preset name can't be empty")
            return {'CANCELLED'}
        # The file path, not the label, so names that sanitize to the same file count too.
        if self.exists() and not self.overwrite:
            self.report({'ERROR'}, f'Preset "{name}" exists. Tick Overwrite to replace it')
            return {'CANCELLED'}
        save_user_preset(presets_folder(), preset_from_light(context.active_object.data, name))
        clear_user_presets_cache()
        context.window_manager.lighthouse.preset = USER_PREFIX + preset_path(presets_folder(), name).stem
        self.report({'INFO'}, f"Saved preset {name}")
        return {'FINISHED'}


def user_preset_items(self, context):
    _user_preset_items[:] = [(key, preset.label, "") for key, preset in cached_user_presets().items()]
    return _user_preset_items


_user_preset_items = []


class LIGHTHOUSE_OT_delete_preset(bpy.types.Operator):
    """Delete this preset from every file"""
    bl_idname = "lighthouse.delete_preset"
    bl_label = "Delete Light Preset"

    preset: bpy.props.EnumProperty(name="Preset", items=user_preset_items)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        settings = context.window_manager.lighthouse
        # Read before deleting: the dynamic enum resolves to another item once the file is gone.
        key = self.preset
        shown = settings.preset == key
        keys = list(cached_user_presets())
        delete_user_preset(presets_folder(), key)
        clear_user_presets_cache()
        if shown and key in keys:
            # The next one in dropdown order, or the new last one. With none left, assign
            # nothing: '' raises TypeError, and the dropdown already reads ''.
            index = keys.index(key)
            rest = keys[:index] + keys[index + 1:]
            if rest:
                settings.preset = rest[min(index, len(rest) - 1)]
        return {'FINISHED'}


class LIGHTHOUSE_OT_restore_default_presets(bpy.types.Operator):
    """Bring back deleted default presets. Defaults you edited are kept as they are"""
    bl_idname = "lighthouse.restore_default_presets"
    bl_label = "Restore Default Presets"

    def execute(self, context):
        restored = restore_default_presets(presets_folder())
        clear_user_presets_cache()
        if restored:
            self.report({'INFO'}, "Restored " + ", ".join(restored))
        else:
            self.report({'INFO'}, "Every default preset is already there")
        return {'FINISHED'}


classes = (
    LIGHTHOUSE_OT_apply_preset,
    LIGHTHOUSE_OT_save_preset,
    LIGHTHOUSE_OT_delete_preset,
    LIGHTHOUSE_OT_restore_default_presets,
)
