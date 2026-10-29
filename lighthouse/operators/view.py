import bpy

from ..lights import find_collection, find_object, listed_groups, reveal, toggle_details
from ..common import scene_or_collection, all_collapsed


class LIGHTHOUSE_OT_toggle_details(bpy.types.Operator):
    """Show or hide this light's details, closing the others.
    Shift+click to keep the others open"""
    bl_idname = "lighthouse.toggle_details"
    bl_label = "Toggle Details"
    bl_options = {'INTERNAL'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})
    keep_others: bpy.props.BoolProperty(name="Keep Others", description="Leave other lights' details open")

    def invoke(self, context, event):
        self.keep_others = event.shift
        return self.execute(context)

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        toggle_details(context.window_manager.lighthouse, obj, self.keep_others)
        return {'FINISHED'}


class LIGHTHOUSE_OT_toggle_group(bpy.types.Operator):
    """Collapse or expand this collection in the list"""
    bl_idname = "lighthouse.toggle_group"
    bl_label = "Toggle Group"
    bl_options = {'INTERNAL'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        collection = find_collection(self.name, self.library)
        if collection is None:
            return {'CANCELLED'}
        collection.lighthouse_collapsed = not collection.lighthouse_collapsed
        return {'FINISHED'}


class LIGHTHOUSE_OT_reveal_active_light(bpy.types.Operator):
    """Expand the collections and lights rows that hide the active light"""
    bl_idname = "lighthouse.reveal_active_light"
    bl_label = "Reveal Active Light"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        obj = context.view_layer.objects.active
        return obj is not None and obj.type == 'LIGHT'

    def execute(self, context):
        reveal(context.view_layer, context.view_layer.objects.active)
        return {'FINISHED'}


class LIGHTHOUSE_OT_toggle_lights_row(bpy.types.Operator):
    """Fold or unfold this collection's own lights in the list"""
    bl_idname = "lighthouse.toggle_lights_row"
    bl_label = "Toggle Lights Row"
    bl_options = {'INTERNAL'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        collection = scene_or_collection(context, self.name, self.library)
        if collection is None:
            return {'CANCELLED'}
        collection.lighthouse_lights_collapsed = not collection.lighthouse_lights_collapsed
        return {'FINISHED'}


class LIGHTHOUSE_OT_clear_filters(bpy.types.Operator):
    """Clear the search and show every light type"""
    bl_idname = "lighthouse.clear_filters"
    bl_label = "Clear Filter(s)"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        filters = context.window_manager.lighthouse
        filters.name_filter = ""
        filters.type_filter = 'ALL'
        return {'FINISHED'}


class LIGHTHOUSE_OT_toggle_all_groups(bpy.types.Operator):
    """Expand every collection and lights row when all collections are collapsed,
    otherwise collapse every collection"""
    bl_idname = "lighthouse.toggle_all_groups"
    bl_label = "Collapse or Expand All Groups"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        filters = context.window_manager.lighthouse
        groups = listed_groups(context.view_layer, filters.type_filter, filters.show_empty)
        collapse = not all_collapsed(context.view_layer, filters)
        for collection in groups:
            collection.lighthouse_collapsed = collapse
            if not collapse:
                collection.lighthouse_lights_collapsed = False
        if not collapse:
            context.scene.collection.lighthouse_lights_collapsed = False
        return {'FINISHED'}


classes = (
    LIGHTHOUSE_OT_toggle_details,
    LIGHTHOUSE_OT_toggle_group,
    LIGHTHOUSE_OT_toggle_lights_row,
    LIGHTHOUSE_OT_toggle_all_groups,
    LIGHTHOUSE_OT_reveal_active_light,
    LIGHTHOUSE_OT_clear_filters,
)
