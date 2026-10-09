import bpy

from .lights import light_objects, listed_lights, power_unit, row_state, scale_lights, toggle_solo


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
    """Multiply the power of the lights in scope by the factor"""
    bl_idname = "lighthouse.scale_lights"
    bl_label = "Scale Light Power"
    bl_options = {'REGISTER', 'UNDO'}

    factor: bpy.props.FloatProperty(name="Factor", default=1.0, min=0.0)
    scope: bpy.props.EnumProperty(name="Scope", items=SCOPE_ITEMS)

    def execute(self, context):
        lights = light_objects(context.view_layer)
        if self.scope == 'SELECTED':
            lights = [obj for obj in lights if obj.select_get()]
        scale_lights(lights, self.factor)
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

    def draw_intensity(self, settings):
        box = self.layout.box()
        box.label(text="Intensity", icon='LIGHT')
        box.row(align=True).prop(settings, "scale_scope", expand=True)
        row = box.row(align=True)
        row.prop(settings, "scale_factor", slider=True)
        op = row.operator(LIGHTHOUSE_OT_scale_lights.bl_idname, text="Apply")
        op.factor = settings.scale_factor
        op.scope = settings.scale_scope


classes = (
    LIGHTHOUSE_PG_settings,
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_OT_mute_light,
    LIGHTHOUSE_OT_solo_light,
    LIGHTHOUSE_OT_scale_lights,
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
