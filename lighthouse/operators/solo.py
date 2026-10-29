import bpy

from ..lights import (
    find_collection,
    find_object,
    solo_label,
    toggle_solo_group,
    toggle_solo_light,
    toggle_solo_world,
    unsolo,
)


class LIGHTHOUSE_OT_solo_light(bpy.types.Operator):
    """Show only this light, or restore every light's visibility if it is already soloed.
    Shift+click: add it to the solo, or remove it if soloed"""
    bl_idname = "lighthouse.solo_light"
    bl_label = "Solo Light"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})
    extend: bpy.props.BoolProperty(
        name="Extend", description="Add to the solo, or remove if soloed (Shift+click)", options={'SKIP_SAVE'})

    def invoke(self, context, event):
        if event.shift:
            self.extend = True
        return self.execute(context)

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        toggle_solo_light(context.scene.lighthouse_solo, context.view_layer, obj, self.extend)
        return {'FINISHED'}


class LIGHTHOUSE_OT_exit_solo(bpy.types.Operator):
    """Restore every light's and collection's visibility from before solo"""
    bl_idname = "lighthouse.exit_solo"
    bl_label = "Exit Solo"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.lighthouse_solo.active

    @classmethod
    def description(cls, context, properties):
        solo = context.scene.lighthouse_solo
        if not solo.active:
            return "Solo is off"
        return f"Exit Solo ({solo_label(solo)}): restore every light's and collection's visibility from before solo"

    def execute(self, context):
        unsolo(context.scene.lighthouse_solo)
        return {'FINISHED'}


class LIGHTHOUSE_OT_solo_group(bpy.types.Operator):
    """Show only the lights in this collection and its sub-collections,
    or restore every light's and collection's visibility if it is already soloed.
    Shift+click: add it to the solo, or remove it if soloed"""
    bl_idname = "lighthouse.solo_group"
    bl_label = "Solo Group"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})
    extend: bpy.props.BoolProperty(
        name="Extend", description="Add to the solo, or remove if soloed (Shift+click)", options={'SKIP_SAVE'})

    def invoke(self, context, event):
        if event.shift:
            self.extend = True
        return self.execute(context)

    def execute(self, context):
        collection = find_collection(self.name, self.library)
        if collection is None:
            return {'CANCELLED'}
        toggle_solo_group(context.scene.lighthouse_solo, context.view_layer, collection, self.extend)
        return {'FINISHED'}


class LIGHTHOUSE_OT_solo_world(bpy.types.Operator):
    """Light the scene with the World only: darken every light and un-mute the World,
    or restore every light's and the World's state if the World is already soloed"""
    bl_idname = "lighthouse.solo_world"
    bl_label = "Solo World"
    bl_options = {'REGISTER', 'UNDO'}
    # Shift+click on the World's star is a plain World solo: the World never joins a lamp solo.
    extend: bpy.props.BoolProperty(name="Extend", options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        toggle_solo_world(context.scene.lighthouse_solo, context.view_layer, context.scene)
        return {'FINISHED'}


classes = (
    LIGHTHOUSE_OT_solo_light,
    LIGHTHOUSE_OT_exit_solo,
    LIGHTHOUSE_OT_solo_group,
    LIGHTHOUSE_OT_solo_world,
)
