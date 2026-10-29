import bpy

from ..lights import (
    find_collection,
    find_layer_collection,
    group_lights,
    is_read_only,
    move_lights,
    move_summary,
    update_snapshot,
)
from ..common import scene_or_collection, target_layer_collection, _lights_in_scope


class LIGHTHOUSE_OT_new_collection(bpy.types.Operator):
    """Add a collection inside the active collection and make it active"""
    bl_idname = "lighthouse.new_collection"
    bl_label = "New Collection"
    bl_options = {'REGISTER', 'UNDO'}

    new_name: bpy.props.StringProperty(name="Name", default="Collection")
    # The parent collection, used when use_active is off. SKIP_SAVE so a call never reuses the last one's.
    name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    library: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    use_active: bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        layer = context.view_layer
        if self.use_active:
            parent = layer.active_layer_collection.collection
        else:
            parent_layer = target_layer_collection(context, self.name, self.library)
            if parent_layer is None:
                return {'CANCELLED'}
            parent = parent_layer.collection
        if is_read_only(parent):
            self.report({'ERROR'}, f"{parent.name} is read-only (linked from a library)")
            return {'CANCELLED'}
        collection = bpy.data.collections.new(self.new_name.strip() or "Collection")
        parent.children.link(collection)
        layer.active_layer_collection = find_layer_collection(layer.layer_collection, collection)
        return {'FINISHED'}


class LIGHTHOUSE_OT_set_active_collection(bpy.types.Operator):
    """Click: make this the active collection, where new lights are added.
    Ctrl+click: rename it"""
    bl_idname = "lighthouse.set_active_collection"
    bl_label = "Set Active Collection"
    # Like clicking a collection in the Outliner (outliner.item_activate), which pushes an undo step.
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})
    action: bpy.props.EnumProperty(
        name="Action",
        items=(
            ('ACTIVATE', "Activate", "Make this the active collection"),
            ('RENAME', "Rename", "Rename this collection"),
        ),
    )
    new_name: bpy.props.StringProperty(name="Name")

    def invoke(self, context, event):
        self.action = 'RENAME' if event.ctrl else 'ACTIVATE'
        if self.action == 'RENAME':
            # The Scene Collection can't be renamed, so Ctrl+click on it does nothing.
            collection = find_collection(self.name, self.library) if self.name else None
            if collection is None:
                return {'CANCELLED'}
            self.new_name = collection.name
            return context.window_manager.invoke_props_dialog(self, title="Rename Collection")
        return self.execute(context)

    def draw(self, context):
        self.layout.prop(self, "new_name", text="")

    def execute(self, context):
        if self.action == 'RENAME':
            collection = find_collection(self.name, self.library) if self.name else None
            if collection is None:
                return {'CANCELLED'}
            if is_read_only(collection):
                self.report({'ERROR'}, f"{collection.name} is read-only (linked from a library)")
                return {'CANCELLED'}
            name = self.new_name.strip()
            if not name:
                self.report({'ERROR'}, "Collection name can't be empty")
                return {'CANCELLED'}
            collection.name = name
            return {'FINISHED'}
        root = context.view_layer.layer_collection
        if self.name == "":
            layer_collection = root
        else:
            collection = find_collection(self.name, self.library)
            layer_collection = collection and find_layer_collection(root, collection)
        if layer_collection is None:
            return {'CANCELLED'}
        context.view_layer.active_layer_collection = layer_collection
        return {'FINISHED'}


class LIGHTHOUSE_OT_select_group(bpy.types.Operator):
    """Select the listed lights in this collection and its sub-collections.
    Shift+click to add them to the selection"""
    bl_idname = "lighthouse.select_group"
    bl_label = "Select Group"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})
    extend: bpy.props.BoolProperty(name="Extend", description="Add to the selection instead of replacing it")

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)

    def execute(self, context):
        collection = find_collection(self.name, self.library)
        if collection is None:
            return {'CANCELLED'}
        layer = context.view_layer
        lights = group_lights(layer, collection, context.window_manager.lighthouse.type_filter)
        if not self.extend:
            for other in layer.objects:
                other.select_set(False)
            if lights and layer.objects.active not in lights:
                layer.objects.active = lights[0]
        for obj in lights:
            obj.select_set(True)
        return {'FINISHED'}


class LIGHTHOUSE_OT_move_to_group(bpy.types.Operator):
    """Move the selected lights into this collection, out of every other one.
    Read-only (library) lights are skipped"""
    bl_idname = "lighthouse.move_to_group"
    bl_label = "Move Selected Lights Here"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        collection = scene_or_collection(context, self.name, self.library)
        if collection is None:
            return {'CANCELLED'}
        if is_read_only(collection):
            self.report({'ERROR'}, f"{collection.name} is read-only (linked from a library)")
            return {'CANCELLED'}
        lights, empty = _lights_in_scope(context, 'SELECTED')
        if not lights:
            self.report({'WARNING'}, empty)
            return {'CANCELLED'}
        moved, skipped = move_lights(lights, collection)
        if not moved:
            self.report({'WARNING'}, move_summary(moved, skipped, collection.name))
            return {'CANCELLED'}
        self.report({'INFO'}, move_summary(moved, skipped, collection.name))
        return {'FINISHED'}


class LIGHTHOUSE_OT_hide_group(bpy.types.Operator):
    """Hide or show this collection in the viewport and in renders.
    The lights' own visibility is kept"""
    bl_idname = "lighthouse.hide_group"
    bl_label = "Hide Group"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        collection = find_collection(self.name, self.library)
        if collection is None:
            return {'CANCELLED'}
        hide = not (collection.hide_render and collection.hide_viewport)
        collection.hide_render = collection.hide_viewport = hide
        update_snapshot(context.scene.lighthouse_solo, collection, hide)
        return {'FINISHED'}


classes = (
    LIGHTHOUSE_OT_new_collection,
    LIGHTHOUSE_OT_set_active_collection,
    LIGHTHOUSE_OT_select_group,
    LIGHTHOUSE_OT_move_to_group,
    LIGHTHOUSE_OT_hide_group,
)
