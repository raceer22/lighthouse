# Copyright (C) 2026 raceer22
# Licensed under the GNU General Public License v3 or later (GPL-3.0-or-later)
import bpy

from .lights import GroupEntry, detail_properties, detail_target, group_lights, indent_level, is_read_only, light_info_tooltip, light_objects, list_entries, move_lights, move_summary, power_unit, row_state, scale_lights, scale_summary, toggle_solo
from pathlib import Path

from .presets import BUILTIN_PRESETS, apply_preset, delete_user_preset, preset_from_light, preset_summary, save_user_preset, user_presets


def presets_folder():
    return Path(bpy.utils.extension_path_user(__package__, create=True))


def all_presets():
    return BUILTIN_PRESETS | user_presets(presets_folder())


_preset_items = []


def preset_items(self, context):
    """Built-in presets, then user presets marked with a user icon."""
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
    grouped: bpy.props.BoolProperty(
        name="Group by Collection",
        description="Nest lights under their collections, as in the outliner. The list is flat while searching",
        default=True,
    )
    scale_factor: bpy.props.FloatProperty(
        name="Factor",
        description="Multiply light power by this value",
        default=1.0,
        min=0.0,
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


class LIGHTHOUSE_OT_toggle_group(bpy.types.Operator):
    """Collapse or expand this collection in the list"""
    bl_idname = "lighthouse.toggle_group"
    bl_label = "Toggle Group"
    bl_options = {'INTERNAL'}

    name: bpy.props.StringProperty()

    def execute(self, context):
        collection = bpy.data.collections.get(self.name)
        if collection is None:
            return {'CANCELLED'}
        collection.lighthouse_collapsed = not collection.lighthouse_collapsed
        return {'FINISHED'}


class LIGHTHOUSE_OT_collapse_all_groups(bpy.types.Operator):
    """Collapse every collection in the list"""
    bl_idname = "lighthouse.collapse_all_groups"
    bl_label = "Collapse All Groups"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        for collection in context.view_layer.layer_collection.collection.children_recursive:
            collection.lighthouse_collapsed = True
        return {'FINISHED'}


class LIGHTHOUSE_OT_select_group(bpy.types.Operator):
    """Select the listed lights in this collection and its sub-collections.
    Shift+click to add them to the selection"""
    bl_idname = "lighthouse.select_group"
    bl_label = "Select Group"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    extend: bpy.props.BoolProperty(name="Extend", description="Add to the selection instead of replacing it")

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)

    def execute(self, context):
        collection = bpy.data.collections.get(self.name)
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

    def execute(self, context):
        collection = bpy.data.collections.get(self.name)
        if collection is None:
            return {'CANCELLED'}
        if is_read_only(collection):
            self.report({'ERROR'}, f"{collection.name} is read-only (linked from a library)")
            return {'CANCELLED'}
        lights = [obj for obj in light_objects(context.view_layer) if obj.select_get()]
        self.report({'INFO'}, move_summary(*move_lights(lights, collection), collection.name))
        return {'FINISHED'}


class LIGHTHOUSE_OT_hide_group(bpy.types.Operator):
    """Hide or show this collection in the viewport and in renders.
    The lights' own visibility is kept"""
    bl_idname = "lighthouse.hide_group"
    bl_label = "Hide Group"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()

    def execute(self, context):
        collection = bpy.data.collections.get(self.name)
        if collection is None:
            return {'CANCELLED'}
        hide = not (collection.hide_render and collection.hide_viewport)
        collection.hide_render = collection.hide_viewport = hide
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
    """Multiply the power of the lights in scope by 2 to the power of the EV steps:
    +1 EV doubles it, -1 EV halves it, fractions give finer steps.
    On keyframed lights, every power keyframe is scaled"""
    bl_idname = "lighthouse.step_exposure"
    bl_label = "Step Light Exposure"
    bl_options = {'REGISTER', 'UNDO'}

    steps: bpy.props.FloatProperty(name="Steps", description="EV steps: +1 doubles power, -1 halves it", default=1.0)
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


EV_STEPS = ((-1.0, "−1"), (-0.5, "−½"), (-0.25, "−¼"), (0.25, "+¼"), (0.5, "+½"), (1.0, "+1"))


class LIGHTHOUSE_PT_intensity(bpy.types.Panel):
    bl_label = "Intensity"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Lights"

    def draw(self, context):
        settings = context.window_manager.lighthouse
        self.layout.row(align=True).prop(settings, "scale_scope", expand=True)
        row = self.layout.row(align=True)
        row.prop(settings, "scale_factor")
        op = row.operator(LIGHTHOUSE_OT_scale_lights.bl_idname, text="Apply")
        op.factor = settings.scale_factor
        op.scope = settings.scale_scope
        row = self.layout.row(align=True)
        row.label(text="EV")
        for steps, text in EV_STEPS:
            op = row.operator(LIGHTHOUSE_OT_step_exposure.bl_idname, text=text)
            op.steps = steps
            op.scope = settings.scale_scope


class LIGHTHOUSE_PT_presets(bpy.types.Panel):
    bl_label = "Presets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Lights"

    def draw_header(self, context):
        settings = context.window_manager.lighthouse
        row = self.layout.row(align=True)
        row.prop(settings, "preset", text="")
        row.operator(LIGHTHOUSE_OT_apply_preset.bl_idname, text="Apply").preset = settings.preset

    def draw(self, context):
        settings = context.window_manager.lighthouse
        row = self.layout.row(align=True)
        row.operator(LIGHTHOUSE_OT_save_preset.bl_idname, text="Save", icon='ADD')
        if settings.preset not in BUILTIN_PRESETS:
            row.operator(LIGHTHOUSE_OT_delete_preset.bl_idname, text="Delete", icon='REMOVE').preset = settings.preset


INDENT_STEP = 1.5


def indent(row, depth):
    """Indent a list row by a fixed step per nesting level, capped by indent_level()."""
    if indent_level(depth):
        row.separator(factor=INDENT_STEP * indent_level(depth))


class LIGHTHOUSE_PT_lights(bpy.types.Panel):
    bl_label = "Lights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Lights"

    def draw(self, context):
        filters = context.window_manager.lighthouse
        row = self.layout.row(align=True)
        row.prop(filters, "name_filter", text="", icon='VIEWZOOM')
        row.prop(filters, "grouped", text="", icon='OUTLINER')
        if filters.grouped and not filters.name_filter:
            row.operator(LIGHTHOUSE_OT_collapse_all_groups.bl_idname, text="", icon='FULLSCREEN_EXIT')
        self.layout.row(align=True).prop(filters, "type_filter", expand=True)

        entries = list_entries(context.view_layer, filters.name_filter, filters.type_filter, filters.grouped)
        for entry in entries:
            if isinstance(entry, GroupEntry):
                self.draw_group(entry)
            else:
                self.draw_light(context, entry)

    def draw_group(self, entry):
        collection = entry.collection
        row = self.layout.row(align=True)
        indent(row, entry.depth)
        row.operator(
            LIGHTHOUSE_OT_toggle_group.bl_idname,
            text="",
            icon='DISCLOSURE_TRI_RIGHT' if collection.lighthouse_collapsed else 'DISCLOSURE_TRI_DOWN',
            emboss=False,
        ).name = collection.name
        row.label(text=f"{collection.name} ({entry.count})", icon='OUTLINER_COLLECTION')
        actions = row.row(align=True)
        actions.operator(LIGHTHOUSE_OT_select_group.bl_idname, text="", icon='RESTRICT_SELECT_OFF').name = collection.name
        actions.operator(LIGHTHOUSE_OT_move_to_group.bl_idname, text="", icon='IMPORT').name = collection.name
        hidden = collection.hide_render and collection.hide_viewport
        actions.operator(
            LIGHTHOUSE_OT_hide_group.bl_idname,
            text="",
            icon='HIDE_ON' if hidden else 'HIDE_OFF',
            depress=hidden,
        ).name = collection.name

    def draw_light(self, context, entry):
        obj = entry.obj
        light = obj.data
        state = row_state(obj, context.view_layer, context.scene)
        row = self.layout.row(align=True)
        row.active = not state.dimmed
        indent(row, entry.depth)
        row.prop(
            obj,
            "lighthouse_expanded",
            text="",
            icon='DISCLOSURE_TRI_DOWN' if obj.lighthouse_expanded else 'DISCLOSURE_TRI_RIGHT',
            emboss=False,
        )
        op = row.operator(
            LIGHTHOUSE_OT_select_light.bl_idname,
            text=obj.name,
            icon='LIGHT_' + light.type,
            emboss=False,
        )
        op.name = obj.name
        if light_info_tooltip(light.users - 1, entry.other_collections):
            op = row.operator(LIGHTHOUSE_OT_light_info.bl_idname, text="", icon='INFO', emboss=False)
            op.other_users = light.users - 1
            op.other_collections = entry.other_collections
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
        if obj.lighthouse_expanded:
            self.draw_details(light, state, context.scene.render.engine)

    def draw_details(self, light, state, engine):
        box = self.layout.box()
        box.active = not state.dimmed
        box.enabled = not state.read_only
        box.use_property_split = True
        for path in detail_properties(light, engine):
            box.prop(*detail_target(light, path))


classes = (
    LIGHTHOUSE_PG_settings,
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_OT_mute_light,
    LIGHTHOUSE_OT_solo_light,
    LIGHTHOUSE_OT_toggle_group,
    LIGHTHOUSE_OT_collapse_all_groups,
    LIGHTHOUSE_OT_select_group,
    LIGHTHOUSE_OT_move_to_group,
    LIGHTHOUSE_OT_hide_group,
    LIGHTHOUSE_OT_scale_lights,
    LIGHTHOUSE_OT_step_exposure,
    LIGHTHOUSE_OT_apply_preset,
    LIGHTHOUSE_OT_save_preset,
    LIGHTHOUSE_OT_delete_preset,
    LIGHTHOUSE_OT_light_info,
    LIGHTHOUSE_PT_intensity,
    LIGHTHOUSE_PT_presets,
    LIGHTHOUSE_PT_lights,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.lighthouse = bpy.props.PointerProperty(type=LIGHTHOUSE_PG_settings)
    bpy.types.Object.lighthouse_expanded = bpy.props.BoolProperty(
        name="Show Details",
        description="Show this light's shadow, influence and render engine settings",
    )
    bpy.types.Collection.lighthouse_collapsed = bpy.props.BoolProperty(
        name="Collapsed",
        description="Hide this collection's lights and sub-collections in the Lights list",
    )


def unregister():
    del bpy.types.Collection.lighthouse_collapsed
    del bpy.types.Object.lighthouse_expanded
    del bpy.types.WindowManager.lighthouse
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
