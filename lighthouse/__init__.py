import bpy

from .lights import light_objects, listed_lights, power_unit, row_state, scale_lights, scale_summary, toggle_solo
from pathlib import Path

from .presets import BUILTIN_PRESETS, apply_preset, delete_user_preset, preset_from_light, preset_summary, save_user_preset, user_presets


def presets_folder():
    return Path(bpy.utils.extension_path_user(__package__, create=True))


def all_presets():
    return BUILTIN_PRESETS | user_presets(presets_folder())


_preset_items = []


def preset_items(self, context):
    """Built-in presets, then user presets marked with a user icon."""
    # Blender doesn't keep the strings of dynamic enum items alive, so the list must outlive this call.
    _preset_items[:] = [
        (key, preset.label, "User preset" if key not in BUILTIN_PRESETS else "", 'USER' if key not in BUILTIN_PRESETS else 'NONE', number)
        for number, (key, preset) in enumerate(all_presets().items())
    ]
    return _preset_items

SCOPE_ITEMS = (
    ('ALL', "All Lights", "Every light in the view layer, whatever the list filters show"),
    ('SELECTED', "Selected Lights", "Only selected lights"),
)


class LIGHTHOUSE_PG_settings(bpy.types.PropertyGroup):
    name_filter: bpy.props.StringProperty(
        name="Search",
        description="Only list lights whose name contains this text",
        options={'TEXTEDIT_UPDATE'},
    )
    type_filter: bpy.props.EnumProperty(
        name="Type",
        description="Only list lights of this type",
        items=(
            ('ALL', "All", "Every light type"),
            ('POINT', "Point", "Point lights", 'LIGHT_POINT', 1),
            ('SUN', "Sun", "Sun lights", 'LIGHT_SUN', 2),
            ('SPOT', "Spot", "Spot lights", 'LIGHT_SPOT', 3),
            ('AREA', "Area", "Area lights", 'LIGHT_AREA', 4),
        ),
    )
    scale_factor: bpy.props.FloatProperty(
        name="Factor",
        description="Multiply light power by this value",
        default=1.0,
        min=0.0,
        soft_max=10.0,
    )
    scale_scope: bpy.props.EnumProperty(name="Scope", description="Which lights to scale", items=SCOPE_ITEMS)
    preset: bpy.props.EnumProperty(name="Preset", description="Light setup to apply to selected lights", items=preset_items)


class LIGHTHOUSE_OT_select_light(bpy.types.Operator):
    """Select this light only and make it active"""
    bl_idname = "lighthouse.select_light"
    bl_label = "Select Light"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()

    def execute(self, context):
        layer = context.view_layer
        obj = layer.objects.get(self.name)
        if obj is None:
            return {'CANCELLED'}
        for other in layer.objects:
            other.select_set(False)
        obj.select_set(True)
        layer.objects.active = obj
        return {'FINISHED'}


class LIGHTHOUSE_OT_mute_light(bpy.types.Operator):
    """Hide or show this light in the viewport and in renders"""
    bl_idname = "lighthouse.mute_light"
    bl_label = "Mute Light"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.view_layer.objects.get(self.name)
        if obj is None:
            return {'CANCELLED'}
        hide = not (obj.hide_render and obj.hide_viewport)
        obj.hide_render = obj.hide_viewport = hide
        return {'FINISHED'}


class LIGHTHOUSE_OT_solo_light(bpy.types.Operator):
    """Show only this light, or restore every light's visibility if it is already soloed"""
    bl_idname = "lighthouse.solo_light"
    bl_label = "Solo Light"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()

    def execute(self, context):
        obj = context.view_layer.objects.get(self.name)
        if obj is None:
            return {'CANCELLED'}
        toggle_solo(context.scene, context.view_layer, obj)
        return {'FINISHED'}


class LIGHTHOUSE_OT_scale_lights(bpy.types.Operator):
    """Multiply the power of the lights in scope by the factor.
    On keyframed lights, every power keyframe is scaled"""
    bl_idname = "lighthouse.scale_lights"
    bl_label = "Scale Light Power"
    bl_options = {'REGISTER', 'UNDO'}

    factor: bpy.props.FloatProperty(name="Factor", default=1.0, min=0.0)
    scope: bpy.props.EnumProperty(name="Scope", items=SCOPE_ITEMS)

    def execute(self, context):
        lights = light_objects(context.view_layer)
        if self.scope == 'SELECTED':
            lights = [obj for obj in lights if obj.select_get()]
        self.report({'INFO'}, scale_summary(*scale_lights(lights, self.factor)))
        return {'FINISHED'}


class LIGHTHOUSE_OT_step_exposure(bpy.types.Operator):
    """Double (+1 EV) or halve (-1 EV) the power of the lights in scope.
    On keyframed lights, every power keyframe is scaled"""
    bl_idname = "lighthouse.step_exposure"
    bl_label = "Step Light Exposure"
    bl_options = {'REGISTER', 'UNDO'}

    steps: bpy.props.IntProperty(name="Steps", description="EV steps: +1 doubles power, -1 halves it", default=1)
    scope: bpy.props.EnumProperty(name="Scope", items=SCOPE_ITEMS)

    def execute(self, context):
        lights = light_objects(context.view_layer)
        if self.scope == 'SELECTED':
            lights = [obj for obj in lights if obj.select_get()]
        self.report({'INFO'}, scale_summary(*scale_lights(lights, 2.0 ** self.steps)))
        return {'FINISHED'}


class LIGHTHOUSE_OT_apply_preset(bpy.types.Operator):
    """Set power, color and soft size of the selected lights from a preset.
    Lights of a type the preset doesn't suit are skipped"""
    bl_idname = "lighthouse.apply_preset"
    bl_label = "Apply Light Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset: bpy.props.EnumProperty(name="Preset", items=preset_items)

    def execute(self, context):
        lights = [obj for obj in light_objects(context.view_layer) if obj.select_get()]
        preset = all_presets()[self.preset]
        self.report({'INFO'}, preset_summary(preset, *apply_preset(lights, preset)))
        return {'FINISHED'}


class LIGHTHOUSE_OT_save_preset(bpy.types.Operator):
    """Save the active light's power, color and soft size as a preset available in every file"""
    bl_idname = "lighthouse.save_preset"
    bl_label = "Save Light Preset"

    name: bpy.props.StringProperty(name="Name", description="Preset name")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'LIGHT'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        name = self.name.strip()
        if not name:
            self.report({'ERROR'}, "Preset name can't be empty")
            return {'CANCELLED'}
        if name.lower() in {preset.label.lower() for preset in BUILTIN_PRESETS.values()}:
            self.report({'ERROR'}, f'"{name}" is a built-in preset. Choose another name')
            return {'CANCELLED'}
        save_user_preset(presets_folder(), preset_from_light(context.active_object.data, name))
        self.report({'INFO'}, f"Saved preset {name}")
        return {'FINISHED'}


def user_preset_items(self, context):
    _user_preset_items[:] = [(key, preset.label, "") for key, preset in user_presets(presets_folder()).items()]
    return _user_preset_items


_user_preset_items = []


class LIGHTHOUSE_OT_delete_preset(bpy.types.Operator):
    """Delete this user preset from every file. Built-in presets can't be deleted"""
    bl_idname = "lighthouse.delete_preset"
    bl_label = "Delete Light Preset"

    preset: bpy.props.EnumProperty(name="Preset", items=user_preset_items)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        delete_user_preset(presets_folder(), self.preset)
        return {'FINISHED'}


class LIGHTHOUSE_OT_shared_light_info(bpy.types.Operator):
    """This light's data is shared with other objects: editing it changes all of them"""
    bl_idname = "lighthouse.shared_light_info"
    bl_label = "Shared Light Data"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {'CANCELLED'}


class LIGHTHOUSE_PT_lights(bpy.types.Panel):
    bl_label = "Lights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Lights"

    def draw(self, context):
        filters = context.window_manager.lighthouse
        self.draw_intensity(filters)
        self.draw_presets(filters)
        self.layout.prop(filters, "name_filter", text="", icon='VIEWZOOM')
        self.layout.row(align=True).prop(filters, "type_filter", expand=True)

        for obj in listed_lights(context.view_layer, filters.name_filter, filters.type_filter):
            light = obj.data
            state = row_state(obj, context.view_layer, context.scene)
            row = self.layout.row(align=True)
            row.active = not state.dimmed
            op = row.operator(
                LIGHTHOUSE_OT_select_light.bl_idname,
                text=obj.name,
                icon='LIGHT_' + light.type,
                emboss=False,
            )
            op.name = obj.name
            if state.shared:
                row.operator(LIGHTHOUSE_OT_shared_light_info.bl_idname, text="", icon='LINKED', emboss=False)
            controls = row.row(align=True)
            controls.enabled = not state.read_only
            controls.prop(light, "energy", text="")
            controls.label(text=power_unit(light))
            controls.prop(light, "color", text="")
            toggles = row.row(align=True)
            op = toggles.operator(
                LIGHTHOUSE_OT_mute_light.bl_idname,
                text="",
                icon='HIDE_ON' if state.muted else 'HIDE_OFF',
                depress=state.muted,
            )
            op.name = obj.name
            op = toggles.operator(
                LIGHTHOUSE_OT_solo_light.bl_idname,
                text="",
                icon='SOLO_ON' if state.soloed else 'SOLO_OFF',
                depress=state.soloed,
            )
            op.name = obj.name

    def draw_presets(self, settings):
        box = self.layout.box()
        box.label(text="Presets", icon='PRESET')
        row = box.row(align=True)
        row.prop(settings, "preset", text="")
        row.operator(LIGHTHOUSE_OT_apply_preset.bl_idname, text="Apply").preset = settings.preset
        row.operator(LIGHTHOUSE_OT_save_preset.bl_idname, text="", icon='ADD')
        if settings.preset not in BUILTIN_PRESETS:
            row.operator(LIGHTHOUSE_OT_delete_preset.bl_idname, text="", icon='REMOVE').preset = settings.preset

    def draw_intensity(self, settings):
        box = self.layout.box()
        box.label(text="Intensity", icon='LIGHT')
        box.row(align=True).prop(settings, "scale_scope", expand=True)
        row = box.row(align=True)
        row.prop(settings, "scale_factor", slider=True)
        op = row.operator(LIGHTHOUSE_OT_scale_lights.bl_idname, text="Apply")
        op.factor = settings.scale_factor
        op.scope = settings.scale_scope
        row = box.row(align=True)
        for steps, text in ((-1, "-1 EV"), (1, "+1 EV")):
            op = row.operator(LIGHTHOUSE_OT_step_exposure.bl_idname, text=text)
            op.steps = steps
            op.scope = settings.scale_scope


classes = (
    LIGHTHOUSE_PG_settings,
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_OT_mute_light,
    LIGHTHOUSE_OT_solo_light,
    LIGHTHOUSE_OT_scale_lights,
    LIGHTHOUSE_OT_step_exposure,
    LIGHTHOUSE_OT_apply_preset,
    LIGHTHOUSE_OT_save_preset,
    LIGHTHOUSE_OT_delete_preset,
    LIGHTHOUSE_OT_shared_light_info,
    LIGHTHOUSE_PT_lights,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.lighthouse = bpy.props.PointerProperty(type=LIGHTHOUSE_PG_settings)


def unregister():
    del bpy.types.WindowManager.lighthouse
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
