import bpy

from .lights import listed_lights, power_unit


class LIGHTHOUSE_PG_filters(bpy.types.PropertyGroup):
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


class LIGHTHOUSE_PT_lights(bpy.types.Panel):
    bl_label = "Lights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Lights"

    def draw(self, context):
        filters = context.window_manager.lighthouse
        self.layout.prop(filters, "name_filter", text="", icon='VIEWZOOM')
        self.layout.row(align=True).prop(filters, "type_filter", expand=True)

        for obj in listed_lights(context.view_layer, filters.name_filter, filters.type_filter):
            light = obj.data
            row = self.layout.row(align=True)
            op = row.operator(
                LIGHTHOUSE_OT_select_light.bl_idname,
                text=obj.name,
                icon='LIGHT_' + light.type,
                emboss=False,
            )
            op.name = obj.name
            row.prop(light, "energy", text="")
            row.label(text=power_unit(light))
            row.prop(light, "color", text="")


classes = (
    LIGHTHOUSE_PG_filters,
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_PT_lights,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.lighthouse = bpy.props.PointerProperty(type=LIGHTHOUSE_PG_filters)


def unregister():
    del bpy.types.WindowManager.lighthouse
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
