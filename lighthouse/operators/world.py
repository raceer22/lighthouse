import bpy

from ..lights import (
    add_environment,
    hdri_addable,
    hdri_target,
    is_read_only,
    update_snapshot,
    world_setup,
    add_world_rotation,
    world_mute_node,
)


class LIGHTHOUSE_OT_add_world_rotation(bpy.types.Operator):
    """Add Texture Coordinate and Mapping nodes in front of the world's Environment Texture, to rotate it"""
    bl_idname = "lighthouse.add_world_rotation"
    bl_label = "Add Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        setup = world_setup(context.scene)
        if setup.state != 'SIMPLE' or setup.rotation != 'ADDABLE':
            self.report({'WARNING'}, "The world's Environment Texture already has a Vector input")
            return {'CANCELLED'}
        if is_read_only(context.scene.world):
            self.report({'ERROR'}, f"{context.scene.world.name} is read-only (linked from a library)")
            return {'CANCELLED'}
        add_world_rotation(context.scene.world.node_tree, setup.environment)
        return {'FINISHED'}


class LIGHTHOUSE_OT_mute_world(bpy.types.Operator):
    """Turn the world's light off or on by muting its Background node"""
    bl_idname = "lighthouse.mute_world"
    bl_label = "Mute World"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node = world_mute_node(world_setup(context.scene))
        if node is None:
            self.report({'WARNING'}, "Mute needs a world with a Background node feeding World Output")
            return {'CANCELLED'}
        if is_read_only(context.scene.world):
            self.report({'ERROR'}, f"{context.scene.world.name} is read-only (linked from a library)")
            return {'CANCELLED'}
        node.mute = not node.mute
        update_snapshot(context.scene.lighthouse_solo, node, node.mute)
        return {'FINISHED'}


class LIGHTHOUSE_OT_load_hdri(bpy.types.Operator):
    """Choose an image for the world's Environment Texture.
    A world with only a Background gets an Environment Texture added in front of it"""
    bl_idname = "lighthouse.load_hdri"
    bl_label = "Load HDRI"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_image: bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})
    filter_folder: bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        world = context.scene.world
        if world is None:
            return {'CANCELLED'}
        if is_read_only(world):
            self.report({'WARNING'}, f"{world.name} is read-only (linked from a library)")
            return {'CANCELLED'}
        node = hdri_target(world)
        setup = world_setup(context.scene)
        if node is None and not hdri_addable(setup):
            self.report({'WARNING'}, f"{world.name} needs exactly one Environment Texture node")
            return {'CANCELLED'}
        try:
            image = bpy.data.images.load(self.filepath, check_existing=True)
        except RuntimeError as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        if node is None:
            add_environment(world.node_tree, setup.background, image)
        else:
            node.image = image
        return {'FINISHED'}


classes = (
    LIGHTHOUSE_OT_add_world_rotation,
    LIGHTHOUSE_OT_mute_world,
    LIGHTHOUSE_OT_load_hdri,
)
