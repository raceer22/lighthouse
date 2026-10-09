import bpy

from .lights import light_objects, power_unit


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
        for obj in light_objects(context.view_layer):
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
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_PT_lights,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
