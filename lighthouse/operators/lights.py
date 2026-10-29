import bpy

from ..lights import (
    find_object,
    is_read_only,
    light_info_tooltip,
    LightEntry,
    list_entries,
    delete_lights,
    duplicate_lights,
    light_scope,
    scope_summary,
    reveal,
    scale_lights,
    scale_summary,
    supports_temperature,
    toggled_mode,
    update_snapshot,
)
from ..common import (
    LIGHT_TYPES,
    SCOPE_ITEMS,
    target_layer_collection,
    default_new_light_mode,
    current_new_light_mode,
    SHIFT_A_VALUES,
    light_muted,
    _lights_in_scope,
    POWER_UNIT_NAMES,
)


class LIGHTHOUSE_OT_select_light(bpy.types.Operator):
    """Click: select only this light and make it active.
    Shift+click: select the listed lights from the active one to this one.
    Ctrl+Shift+click: add it to the selection, or remove it if selected.
    Ctrl+click: rename it.
    Alt+click: select only this light and frame it in the 3D view"""
    bl_idname = "lighthouse.select_light"
    bl_label = "Select Light"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})
    action: bpy.props.EnumProperty(
        name="Action",
        items=(
            ('SELECT', "Select", "Select only this light and make it active"),
            ('TOGGLE', "Toggle", "Add this light to the selection and make it active, or remove it if selected"),
            ('RENAME', "Rename", "Rename this light"),
            ('RANGE', "Range", "Select only the listed lights from the active one to this one"),
            ('FRAME', "Frame", "Select only this light and frame it in the 4D view"),
        ),
    )
    new_name: bpy.props.StringProperty(name="Name")

    def invoke(self, context, event):
        if event.shift and event.ctrl:
            self.action = 'TOGGLE'
        elif event.shift:
            self.action = 'RANGE'
        elif event.ctrl:
            self.action = 'RENAME'
        elif event.alt:
            self.action = 'FRAME'
        else:
            self.action = 'SELECT'
        if self.action == 'RENAME':
            obj = find_object(context.view_layer, self.name, self.library)
            if obj is None:
                return {'CANCELLED'}
            self.new_name = obj.name
            return context.window_manager.invoke_props_dialog(self, title="Rename Light")
        return self.execute(context)

    def draw(self, context):
        self.layout.prop(self, "new_name", text="")

    def execute(self, context):
        layer = context.view_layer
        obj = find_object(layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        if self.action == 'RENAME':
            name = self.new_name.strip()
            if not name:
                self.report({'ERROR'}, "Light name can't be empty")
                return {'CANCELLED'}
            obj.name = name
            return {'FINISHED'}
        if self.action == 'RANGE':
            filters = context.window_manager.lighthouse
            listed = [
                entry.obj
                for entry in list_entries(layer, filters.name_filter, filters.type_filter, filters.grouped,
                                          filters.show_empty)
                if isinstance(entry, LightEntry)
            ]
            if layer.objects.active in listed and obj in listed:
                ends = sorted((listed.index(layer.objects.active), listed.index(obj)))
                for other in layer.objects:
                    other.select_set(False)
                for light in listed[ends[0]:ends[1] + 1]:
                    light.select_set(True)
                return {'FINISHED'}
        if self.action == 'TOGGLE':
            if obj.select_get():
                obj.select_set(False)
                return {'FINISHED'}
        else:
            for other in layer.objects:
                other.select_set(False)
        obj.select_set(True)
        layer.objects.active = obj
        if self.action == 'FRAME':
            frame_selected(context)
        return {'FINISHED'}


class LIGHTHOUSE_OT_rename_light(bpy.types.Operator):
    """Rename this light's object (its light data keeps its name)"""
    bl_idname = "lighthouse.rename_light"
    bl_label = "Rename Light"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})
    new_name: bpy.props.StringProperty(name="Name")

    def invoke(self, context, event):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        self.new_name = obj.name
        return context.window_manager.invoke_props_dialog(self, title="Rename Light")

    def draw(self, context):
        self.layout.prop(self, "new_name", text="")

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        if is_read_only(obj):
            self.report({'ERROR'}, f"{obj.name} is read-only (linked from a library)")
            return {'CANCELLED'}
        name = self.new_name.strip()
        if not name:
            self.report({'ERROR'}, "Light name can't be empty")
            return {'CANCELLED'}
        obj.name = name
        return {'FINISHED'}


def read_only_scope(objects):
    """The warning when every light in scope is read-only."""
    if len(objects) == 1:
        return f"{objects[0].name} is read-only (linked from a library)"
    return f"All {len(objects)} lights are read-only (linked from a library)"


class LIGHTHOUSE_OT_delete_lights(bpy.types.Operator):
    """Delete this light, or every selected light if it is selected.
    Read-only (library) lights are skipped"""
    bl_idname = "lighthouse.delete_lights"
    bl_label = "Delete Lights"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        lights = light_scope(context.view_layer, obj)
        deleted, skipped = delete_lights(lights)
        if not deleted:
            self.report({'WARNING'}, read_only_scope(lights))
            return {'CANCELLED'}
        self.report({'INFO'}, scope_summary("Deleted", deleted, skipped))
        return {'FINISHED'}


class LIGHTHOUSE_OT_duplicate_lights(bpy.types.Operator):
    """Duplicate this light, or every selected light if it is selected, into the same collections.
    Read-only (library) lights are skipped"""
    bl_idname = "lighthouse.duplicate_lights"
    bl_label = "Duplicate Lights"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})
    linked: bpy.props.BoolProperty(name="Linked", description="Share the light data instead of copying it")

    def execute(self, context):
        layer = context.view_layer
        obj = find_object(layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        lights = light_scope(layer, obj)
        copies, skipped = duplicate_lights(lights, self.linked, context.scene.lighthouse_solo)
        if not copies:
            self.report({'WARNING'}, read_only_scope(lights))
            return {'CANCELLED'}
        for other in layer.objects:
            other.select_set(False)
        for copy in copies.values():
            copy.select_set(True)
        layer.objects.active = copies.get(obj, next(iter(copies.values())))
        self.report({'INFO'}, scope_summary("Duplicated", len(copies), skipped))
        return {'FINISHED'}


def frame_selected(context):
    """Frame the selection in the panel's 3D view, or the first one on screen.
    Does nothing without one (in background mode)."""
    areas = [context.area] if context.area and context.area.type == 'VIEW_3D' else []
    if context.screen:
        areas += [area for area in context.screen.areas if area.type == 'VIEW_3D']
    for area in areas:
        region = next((r for r in area.regions if r.type == 'WINDOW'), None)
        if region is not None:
            with context.temp_override(area=area, region=region):
                bpy.ops.view3d.view_selected()
            return


class LIGHTHOUSE_OT_toggle_new_light_mode(bpy.types.Operator):
    """Switch whether lights added by Lighthouse start in Color or in Kelvin"""
    bl_idname = "lighthouse.toggle_new_light_mode"
    bl_label = "New Lights: Color or Kelvin"
    # UNDO because the mode is file data: without an undo step, undoing something else would revert it.
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def description(cls, context, properties):
        mode = "Kelvin" if current_new_light_mode(context) == 'KELVIN' else "Color"
        source = "Preferences default" if context.scene.lighthouse_new_lights == 'FOLLOW' else "this file"
        return f"New lights start in {mode} ({source}). Click to switch"

    def execute(self, context):
        scene = context.scene
        scene.lighthouse_new_lights = toggled_mode(scene.lighthouse_new_lights, default_new_light_mode(context))
        return {'FINISHED'}


class LIGHTHOUSE_OT_add_light(bpy.types.Operator):
    """Add a light at the 3D cursor in the active collection, selected and active"""
    bl_idname = "lighthouse.add_light"
    bl_label = "Add Light"
    bl_options = {'REGISTER', 'UNDO'}

    type: bpy.props.EnumProperty(name="Type", items=LIGHT_TYPES)
    # The target collection, used when use_active is off. SKIP_SAVE so a call never reuses the last one's.
    name: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    library: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'})
    use_active: bpy.props.BoolProperty(default=True, options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        layer = context.view_layer
        if self.use_active:
            layer_collection = layer.active_layer_collection
        else:
            layer_collection = target_layer_collection(context, self.name, self.library)
            if layer_collection is None:
                return {'CANCELLED'}
        collection = layer_collection.collection
        if is_read_only(collection):
            self.report({'ERROR'}, f"{collection.name} is read-only (linked from a library)")
            return {'CANCELLED'}
        name = next(label for key, label, *_ in LIGHT_TYPES if key == self.type)
        light = bpy.data.lights.new(name, self.type)
        for prop, value in SHIFT_A_VALUES.get(self.type, {}).items():
            setattr(light, prop, value)
        if supports_temperature() and current_new_light_mode(context) == 'KELVIN':
            light.use_temperature = True
            light.temperature = bpy.types.Light.bl_rna.properties["temperature"].default
            light.color = (1.0, 1.0, 1.0)
        obj = bpy.data.objects.new(name, light)
        obj.location = context.scene.cursor.location
        collection.objects.link(obj)
        reveal(layer, obj)
        for other in layer.objects:
            other.select_set(False)
        obj.select_set(True)
        layer.objects.active = obj
        layer.active_layer_collection = layer_collection
        return {'FINISHED'}


class LIGHTHOUSE_OT_mute_light(bpy.types.Operator):
    """Hide or show this light in the viewport and in renders"""
    bl_idname = "lighthouse.mute_light"
    bl_label = "Mute Light"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        hide = not light_muted(obj)
        obj.hide_render = obj.hide_viewport = hide
        update_snapshot(context.scene.lighthouse_solo, obj, hide)
        return {'FINISHED'}


class LIGHTHOUSE_OT_mute_lights(bpy.types.Operator):
    """Mute this light, or every selected light if it is selected; unmute them if this light is muted.
    Read-only (library) lights are skipped"""
    bl_idname = "lighthouse.mute_lights"
    bl_label = "Mute Lights"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        lights = light_scope(context.view_layer, obj)
        editable = [light for light in lights if not is_read_only(light)]
        if not editable:
            self.report({'WARNING'}, read_only_scope(lights))
            return {'CANCELLED'}
        hide = not light_muted(obj)
        for light in editable:
            light.hide_render = light.hide_viewport = hide
            update_snapshot(context.scene.lighthouse_solo, light, hide)
        self.report({'INFO'}, scope_summary("Muted" if hide else "Unmuted", len(editable), len(lights) - len(editable)))
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
        if self.factor == 1.0:
            return {'CANCELLED'}
        lights, empty = _lights_in_scope(context, self.scope)
        if not lights:
            self.report({'WARNING'}, empty)
            return {'CANCELLED'}
        scaled, keyframed = scale_lights(lights, self.factor)
        if not scaled:
            self.report({'WARNING'}, scale_summary(scaled, keyframed))
            return {'CANCELLED'}
        self.report({'INFO'}, scale_summary(scaled, keyframed))
        return {'FINISHED'}


class LIGHTHOUSE_OT_step_exposure(bpy.types.Operator):
    """Multiply the power of the lights in scope by 2 to the power of the EV steps:
    +1 EV doubles it, -1 EV halves it, fractions give finer steps.
    On keyframed lights, every power keyframe is scaled"""
    bl_idname = "lighthouse.step_exposure"
    bl_label = "Step Light Exposure"
    bl_options = {'REGISTER', 'UNDO'}

    steps: bpy.props.FloatProperty(name="Steps", description="EV steps: +1 doubles power, -1 halves it", default=1.0)
    scope: bpy.props.EnumProperty(name="Scope", items=SCOPE_ITEMS)

    def execute(self, context):
        if self.steps == 0.0:
            return {'CANCELLED'}
        lights, empty = _lights_in_scope(context, self.scope)
        if not lights:
            self.report({'WARNING'}, empty)
            return {'CANCELLED'}
        scaled, keyframed = scale_lights(lights, 2.0 ** self.steps)
        if not scaled:
            self.report({'WARNING'}, scale_summary(scaled, keyframed))
            return {'CANCELLED'}
        self.report({'INFO'}, scale_summary(scaled, keyframed))
        return {'FINISHED'}


class LIGHTHOUSE_OT_light_info(bpy.types.Operator):
    """Light data shared with other objects, or the light listed in other collections"""
    bl_idname = "lighthouse.light_info"
    bl_label = "Light Info"
    bl_options = {'INTERNAL'}

    other_users: bpy.props.IntProperty()
    other_collections: bpy.props.IntProperty()

    @classmethod
    def description(cls, context, properties):
        return light_info_tooltip(properties.other_users, properties.other_collections)

    def execute(self, context):
        return {'CANCELLED'}


class LIGHTHOUSE_OT_power_unit(bpy.types.Operator):
    """Unit of the light's power"""
    bl_idname = "lighthouse.power_unit"
    bl_label = "Power Unit"
    bl_options = {'INTERNAL'}

    unit: bpy.props.StringProperty()

    @classmethod
    def description(cls, context, properties):
        return f"Power in {POWER_UNIT_NAMES[properties.unit]} ({properties.unit})"

    def execute(self, context):
        return {'CANCELLED'}


classes = (
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_OT_rename_light,
    LIGHTHOUSE_OT_delete_lights,
    LIGHTHOUSE_OT_duplicate_lights,
    LIGHTHOUSE_OT_mute_lights,
    LIGHTHOUSE_OT_toggle_new_light_mode,
    LIGHTHOUSE_OT_add_light,
    LIGHTHOUSE_OT_mute_light,
    LIGHTHOUSE_OT_scale_lights,
    LIGHTHOUSE_OT_step_exposure,
    LIGHTHOUSE_OT_light_info,
    LIGHTHOUSE_OT_power_unit,
)
