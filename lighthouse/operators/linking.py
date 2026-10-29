import bpy

from ..lights import (
    find_collection,
    _lookup,
    find_object,
    linking_tooltip,
    clear_receivers,
    link_receivers,
    remove_receiver,
    details_open,
    is_read_only,
    toggle_details,
)


class LIGHTHOUSE_OT_light_linking_info(bpy.types.Operator):
    """Light linking summary. Click to open the light's details.
    Shift+click to keep other lights' details open"""
    bl_idname = "lighthouse.light_linking_info"
    bl_label = "Light Linking"
    bl_options = {'INTERNAL'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})
    included: bpy.props.IntProperty()
    excluded: bpy.props.IntProperty()
    included_collections: bpy.props.IntProperty()
    excluded_collections: bpy.props.IntProperty()
    keep_others: bpy.props.BoolProperty(name="Keep Others", description="Leave other lights' details open")

    @classmethod
    def description(cls, context, properties):
        return linking_tooltip(properties.included, properties.excluded,
                               properties.included_collections, properties.excluded_collections)

    def invoke(self, context, event):
        self.keep_others = event.shift
        return self.execute(context)

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        settings = context.window_manager.lighthouse
        if not details_open(settings, obj):
            toggle_details(settings, obj, self.keep_others)
        return {'FINISHED'}


class LIGHTHOUSE_OT_link_receivers(bpy.types.Operator):
    """Light only the selected objects with this light (Light Linking receivers)"""
    bl_idname = "lighthouse.link_receivers"
    bl_label = "Link Selected"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty(options={'HIDDEN'})
    library: bpy.props.StringProperty(options={'HIDDEN'})
    state: bpy.props.EnumProperty(items=(('INCLUDE', "Include", ""), ('EXCLUDE', "Exclude", "")),
                                  default='INCLUDE')

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        selected = [o for o in context.selected_objects if o != obj]
        if not selected:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        collection = obj.light_linking.receiver_collection
        for id in (obj, collection):
            if id is not None and is_read_only(id):
                self.report({'ERROR'}, f"{id.name} is read-only (linked from a library)")
                return {'CANCELLED'}
        link_receivers(obj, selected, self.state)
        return {'FINISHED'}


class LIGHTHOUSE_OT_clear_receivers(bpy.types.Operator):
    """Remove every object and collection from this light's linking (and from every light sharing it)"""
    bl_idname = "lighthouse.clear_receivers"
    bl_label = "Clear"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty(options={'HIDDEN'})
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None or obj.light_linking.receiver_collection is None:
            return {'CANCELLED'}
        for data in (obj, obj.light_linking.receiver_collection):
            if is_read_only(data):
                self.report({'ERROR'}, f"{data.name} is read-only (linked from a library)")
                return {'CANCELLED'}
        clear_receivers(obj)
        return {'FINISHED'}


class LIGHTHOUSE_OT_remove_receiver(bpy.types.Operator):
    """Stop linking this object or collection to the light"""
    bl_idname = "lighthouse.remove_receiver"
    bl_label = "Remove Receiver"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty(options={'HIDDEN'})
    library: bpy.props.StringProperty(options={'HIDDEN'})
    receiver: bpy.props.StringProperty(options={'HIDDEN'})
    receiver_library: bpy.props.StringProperty(options={'HIDDEN'})
    kind: bpy.props.EnumProperty(items=(('OBJECT', "Object", ""), ('COLLECTION', "Collection", "")),
                                 options={'HIDDEN'})

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None or obj.light_linking.receiver_collection is None:
            return {'CANCELLED'}
        id = (find_collection(self.receiver, self.receiver_library) if self.kind == 'COLLECTION'
              else _lookup(bpy.data.objects, self.receiver, self.receiver_library))
        for data in (obj, obj.light_linking.receiver_collection):
            if is_read_only(data):
                self.report({'ERROR'}, f"{data.name} is read-only (linked from a library)")
                return {'CANCELLED'}
        if id is None:
            return {'CANCELLED'}
        remove_receiver(obj, id)
        return {'FINISHED'}


classes = (
    LIGHTHOUSE_OT_light_linking_info,
    LIGHTHOUSE_OT_link_receivers,
    LIGHTHOUSE_OT_remove_receiver,
    LIGHTHOUSE_OT_clear_receivers,
)
