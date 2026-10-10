# Copyright (C) 2026 raceer22
# Licensed under the GNU General Public License v3 or later (GPL-3.0-or-later)
import zlib
from pathlib import Path

import bpy

from .lights import (
    DETAIL_LABELS,
    find_collection,
    find_layer_collection,
    find_object,
    id_key,
    GroupEntry,
    color_control,
    detail_properties,
    detail_target,
    details_open,
    empty_message,
    group_lights,
    group_soloed,
    indent_level,
    is_collapsed,
    is_lights_folded,
    is_read_only,
    light_info_tooltip,
    LightEntry,
    LightsEntry,
    SceneEntry,
    light_objects,
    list_entries,
    listed_groups,
    tree_under_message,
    move_lights,
    move_summary,
    power_unit,
    row_state,
    scale_lights,
    scale_summary,
    solo_label,
    toggle_details,
    toggle_solo_group,
    toggle_solo_light,
    unsolo,
    update_snapshot,
)
from .presets import (
    BUILTIN_PRESETS,
    apply_preset,
    delete_user_preset,
    preset_from_light,
    preset_path,
    preset_summary,
    save_user_preset,
    USER_PREFIX,
    user_presets,
)


def presets_folder():
    return Path(bpy.utils.extension_path_user(__package__, create=True))


_user_presets_cache = {}


def cached_user_presets():
    """user_presets() of the presets folder, read again only when the folder's mtime changes
    (a file added, removed or renamed) or after clear_user_presets_cache(). A file edited in
    place outside Blender is picked up after a restart."""
    folder = presets_folder()
    stamp = folder.stat().st_mtime_ns
    if _user_presets_cache.get("stamp") != stamp:
        _user_presets_cache.update(stamp=stamp, presets=user_presets(folder))
    return _user_presets_cache["presets"]


def clear_user_presets_cache():
    _user_presets_cache.clear()


def all_presets():
    return BUILTIN_PRESETS | cached_user_presets()


_preset_items = []


def preset_items(self, context):
    """Built-in presets, then user presets marked with a user icon. Each item's number comes from
    its key, so the stored value follows the preset when others are added or deleted."""
    _preset_items[:] = [
        (key, preset.label, "User preset" if key not in BUILTIN_PRESETS else "", 'USER' if key not in BUILTIN_PRESETS else 'NONE',
         zlib.crc32(key.encode()) & 0x7FFFFFFF)
        for key, preset in all_presets().items()
    ]
    return _preset_items

LIGHT_TYPES = (
    ('POINT', "Point", "Point lights", 'LIGHT_POINT', 1),
    ('SUN', "Sun", "Sun lights", 'LIGHT_SUN', 2),
    ('SPOT', "Spot", "Spot lights", 'LIGHT_SPOT', 3),
    ('AREA', "Area", "Area lights", 'LIGHT_AREA', 4),
)

SCOPE_ITEMS = (
    ('ALL', "All Lights", "Every light in the view layer, whatever the list filters show"),
    ('SELECTED', "Selected Lights", "Only selected lights"),
)


class LIGHTHOUSE_PG_expanded(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)


class LIGHTHOUSE_PG_settings(bpy.types.PropertyGroup):
    name_filter: bpy.props.StringProperty(
        name="Search",
        description="Only list lights whose name contains this text",
        options={'TEXTEDIT_UPDATE'},
    )
    type_filter: bpy.props.EnumProperty(
        name="Type",
        description="Only list lights of this type",
        items=(('ALL', "All", "Every light type"),) + LIGHT_TYPES,
    )
    grouped: bpy.props.BoolProperty(
        name="Group by Collection",
        description="Nest lights under their collections, as in the outliner. The list is flat while searching",
        default=True,
    )
    show_empty: bpy.props.BoolProperty(
        name="Show Empty Collections",
        description="List collections without (matching) lights too, so you can make them active or move lights into them",
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
    # Lights whose details are open. Panel state: not saved, not undoable, kept on rename.
    expanded: bpy.props.CollectionProperty(type=LIGHTHOUSE_PG_expanded)


class LIGHTHOUSE_PG_solo_object(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    hide_render: bpy.props.BoolProperty()
    hide_viewport: bpy.props.BoolProperty()


class LIGHTHOUSE_PG_solo_collection(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)
    hide_render: bpy.props.BoolProperty()
    hide_viewport: bpy.props.BoolProperty()


class LIGHTHOUSE_PG_solo(bpy.types.PropertyGroup):
    """The scene's solo target and the visibility flags to restore on un-solo."""
    active: bpy.props.BoolProperty()
    light: bpy.props.PointerProperty(type=bpy.types.Object)
    group: bpy.props.PointerProperty(type=bpy.types.Collection)
    objects: bpy.props.CollectionProperty(type=LIGHTHOUSE_PG_solo_object)
    collections: bpy.props.CollectionProperty(type=LIGHTHOUSE_PG_solo_collection)


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
            ('FRAME', "Frame", "Select only this light and frame it in the 3D view"),
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


def scene_or_collection(context, name, library):
    """The collection a header button targets: name "" (no ID has an empty name) is the scene's
    master collection, which is not in bpy.data.collections."""
    return context.scene.collection if name == "" else find_collection(name, library)


def target(op, id):
    """Point a row or header button's operator at this exact light or collection."""
    op.name, op.library = id_key(id)


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


class LIGHTHOUSE_OT_add_light(bpy.types.Operator):
    """Add a light at the 3D cursor in the active collection, selected and active"""
    bl_idname = "lighthouse.add_light"
    bl_label = "Add Light"
    bl_options = {'REGISTER', 'UNDO'}

    type: bpy.props.EnumProperty(name="Type", items=LIGHT_TYPES)

    def execute(self, context):
        layer = context.view_layer
        collection = layer.active_layer_collection.collection
        if is_read_only(collection):
            self.report({'ERROR'}, f"{collection.name} is read-only (linked from a library)")
            return {'CANCELLED'}
        name = next(label for key, label, *_ in LIGHT_TYPES if key == self.type)
        obj = bpy.data.objects.new(name, bpy.data.lights.new(name, self.type))
        obj.location = context.scene.cursor.location
        collection.objects.link(obj)
        for other in layer.objects:
            other.select_set(False)
        obj.select_set(True)
        layer.objects.active = obj
        return {'FINISHED'}


class LIGHTHOUSE_OT_new_collection(bpy.types.Operator):
    """Add a collection inside the active collection and make it active"""
    bl_idname = "lighthouse.new_collection"
    bl_label = "New Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        layer = context.view_layer
        parent = layer.active_layer_collection.collection
        if is_read_only(parent):
            self.report({'ERROR'}, f"{parent.name} is read-only (linked from a library)")
            return {'CANCELLED'}
        collection = bpy.data.collections.new("Collection")
        parent.children.link(collection)
        layer.active_layer_collection = find_layer_collection(layer.layer_collection, collection)
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
        hide = not (obj.hide_render and obj.hide_viewport)
        obj.hide_render = obj.hide_viewport = hide
        update_snapshot(context.scene.lighthouse_solo, obj, hide)
        return {'FINISHED'}


class LIGHTHOUSE_OT_solo_light(bpy.types.Operator):
    """Show only this light, or restore every light's visibility if it is already soloed"""
    bl_idname = "lighthouse.solo_light"
    bl_label = "Solo Light"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        obj = find_object(context.view_layer, self.name, self.library)
        if obj is None:
            return {'CANCELLED'}
        toggle_solo_light(context.scene.lighthouse_solo, context.view_layer, obj)
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


class LIGHTHOUSE_OT_set_active_collection(bpy.types.Operator):
    """Make this the active collection, where new lights are added"""
    bl_idname = "lighthouse.set_active_collection"
    bl_label = "Set Active Collection"
    # Like clicking a collection in the Outliner (outliner.item_activate), which pushes an undo step.
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
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


def all_collapsed(view_layer, filters):
    """True when every listed collection with a triangle is collapsed (also when there are none).
    Only collections count: a folded lights row, or an empty collection with nothing to fold, never decides it."""
    groups = listed_groups(view_layer, filters.type_filter, filters.show_empty, foldable_only=True)
    return all(is_collapsed(collection) for collection in groups)


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


class LIGHTHOUSE_OT_solo_group(bpy.types.Operator):
    """Show only the lights in this collection and its sub-collections,
    or restore every light's and collection's visibility if it is already soloed"""
    bl_idname = "lighthouse.solo_group"
    bl_label = "Solo Group"
    bl_options = {'REGISTER', 'UNDO'}

    name: bpy.props.StringProperty()
    library: bpy.props.StringProperty(options={'HIDDEN'})

    def execute(self, context):
        collection = find_collection(self.name, self.library)
        if collection is None:
            return {'CANCELLED'}
        toggle_solo_group(context.scene.lighthouse_solo, context.view_layer, collection)
        return {'FINISHED'}


def _lights_in_scope(context, scope):
    """The view layer's lights for scope ALL, or the selected ones for SELECTED,
    and the warning to report if there are none."""
    lights = light_objects(context.view_layer)
    if scope == 'SELECTED':
        return [obj for obj in lights if obj.select_get()], "No lights selected"
    return lights, "No lights in the view layer"


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


class LIGHTHOUSE_OT_apply_preset(bpy.types.Operator):
    """Set power, color, soft size, exposure and temperature of the selected lights from a preset.
    Lights of a type the preset doesn't suit are skipped"""
    bl_idname = "lighthouse.apply_preset"
    bl_label = "Apply Light Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset: bpy.props.EnumProperty(name="Preset", items=preset_items)

    def execute(self, context):
        lights, empty = _lights_in_scope(context, 'SELECTED')
        if not lights:
            self.report({'WARNING'}, empty)
            return {'CANCELLED'}
        preset = all_presets()[self.preset]
        changed, *skipped = apply_preset(lights, preset)
        if not changed:
            self.report({'WARNING'}, preset_summary(preset, changed, *skipped))
            return {'CANCELLED'}
        self.report({'INFO'}, preset_summary(preset, changed, *skipped))
        return {'FINISHED'}


class LIGHTHOUSE_OT_save_preset(bpy.types.Operator):
    """Save the active light's power, color, soft size, exposure and temperature as a preset
    available in every file"""
    bl_idname = "lighthouse.save_preset"
    bl_label = "Save Light Preset"

    name: bpy.props.StringProperty(name="Name", description="Preset name")
    overwrite: bpy.props.BoolProperty(name="Overwrite", description="Replace the existing preset with this name")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'LIGHT'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def exists(self):
        name = self.name.strip()
        return bool(name) and preset_path(presets_folder(), name).exists()

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "name")
        if self.exists():
            layout.label(text="A preset with this name exists", icon='ERROR')
            layout.prop(self, "overwrite")

    def execute(self, context):
        name = self.name.strip()
        if not name:
            self.report({'ERROR'}, "Preset name can't be empty")
            return {'CANCELLED'}
        if name.lower() in {preset.label.lower() for preset in BUILTIN_PRESETS.values()}:
            self.report({'ERROR'}, f'"{name}" is a built-in preset. Choose another name')
            return {'CANCELLED'}
        # The file path, not the label, so names that sanitize to the same file count too.
        if self.exists() and not self.overwrite:
            self.report({'ERROR'}, f'Preset "{name}" exists. Tick Overwrite to replace it')
            return {'CANCELLED'}
        save_user_preset(presets_folder(), preset_from_light(context.active_object.data, name))
        clear_user_presets_cache()
        context.window_manager.lighthouse.preset = USER_PREFIX + preset_path(presets_folder(), name).stem
        self.report({'INFO'}, f"Saved preset {name}")
        return {'FINISHED'}


def user_preset_items(self, context):
    _user_preset_items[:] = [(key, preset.label, "") for key, preset in cached_user_presets().items()]
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
        settings = context.window_manager.lighthouse
        if settings.preset == self.preset:
            settings.preset = 'CANDLE'
        delete_user_preset(presets_folder(), self.preset)
        clear_user_presets_cache()
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


POWER_UNIT_NAMES = {"W": "watts", "W/m²": "watts per square metre"}


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
        for i, (steps, text) in enumerate(EV_STEPS):
            if i == len(EV_STEPS) // 2:
                # A flat no-op button: labels can't center their text, buttons do
                row.operator(LIGHTHOUSE_OT_step_exposure.bl_idname, text="EV", emboss=False).steps = 0.0
            op = row.operator(LIGHTHOUSE_OT_step_exposure.bl_idname, text=text)
            op.steps = steps
            op.scope = settings.scale_scope


class LIGHTHOUSE_PT_presets(bpy.types.Panel):
    bl_label = "Presets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Lights"

    def draw(self, context):
        settings = context.window_manager.lighthouse
        row = self.layout.row(align=True)
        row.prop(settings, "preset", text="")
        # '' when the selected preset's file was removed outside Blender. Assigning '' to the
        # operator's enum raises TypeError and stops the panel drawing.
        apply_row = row.row(align=True)
        apply_row.enabled = bool(settings.preset)
        op = apply_row.operator(LIGHTHOUSE_OT_apply_preset.bl_idname, text="Apply")
        if settings.preset:
            op.preset = settings.preset
        row = self.layout.row(align=True)
        row.operator(LIGHTHOUSE_OT_save_preset.bl_idname, text="Save")
        if settings.preset and settings.preset not in BUILTIN_PRESETS:
            row.operator(LIGHTHOUSE_OT_delete_preset.bl_idname, text="Delete").preset = settings.preset


INDENT_STEP = 1.5
# Fixed widths for a light row's unit label and color swatch (or Kelvin field), so power fills the rest with no gap.
UNIT_WIDTH = 1.5
SWATCH_WIDTH = 2


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
        row.prop(filters, "show_empty", text="", icon='OUTLINER_COLLECTION')
        if filters.grouped and not filters.name_filter:
            groups = listed_groups(context.view_layer, filters.type_filter, filters.show_empty, foldable_only=True)
            collapsed = bool(groups) and all_collapsed(context.view_layer, filters)
            row.operator(LIGHTHOUSE_OT_toggle_all_groups.bl_idname, text="",
                         icon='FULLSCREEN_ENTER' if collapsed else 'FULLSCREEN_EXIT')
        # Always drawn (greyed out by poll when solo is off) so the list never shifts.
        solo_active = context.scene.lighthouse_solo.active
        row.operator(LIGHTHOUSE_OT_exit_solo.bl_idname, text="",
                     icon='SOLO_ON' if solo_active else 'SOLO_OFF', depress=solo_active)
        row.operator_menu_enum(LIGHTHOUSE_OT_add_light.bl_idname, "type", text="", icon='ADD')
        row.operator(LIGHTHOUSE_OT_new_collection.bl_idname, text="", icon='COLLECTION_NEW')
        self.layout.row(align=True).prop(filters, "type_filter", expand=True)

        message = empty_message(context.view_layer, filters.name_filter, filters.type_filter)
        if message:
            self.layout.label(text=message, icon='INFO')
            if light_objects(context.view_layer):
                self.layout.operator(LIGHTHOUSE_OT_clear_filters.bl_idname)
            if not tree_under_message(filters.grouped, filters.name_filter, filters.show_empty):
                return

        entries = list_entries(context.view_layer, filters.name_filter, filters.type_filter, filters.grouped,
                               filters.show_empty)
        for entry in entries:
            if isinstance(entry, SceneEntry):
                self.draw_scene_row(context, entry)
            elif isinstance(entry, GroupEntry):
                self.draw_group(context, entry)
            elif isinstance(entry, LightsEntry):
                self.draw_lights_row(entry)
            else:
                self.draw_light(context, entry)

    def draw_scene_row(self, context, entry):
        # name "" targets the Scene Collection, set explicitly so a button never reuses the last name.
        row = self.layout.row(align=True)
        if entry.count:
            row.operator(
                LIGHTHOUSE_OT_toggle_lights_row.bl_idname,
                text="",
                icon='DISCLOSURE_TRI_RIGHT' if is_lights_folded(entry.collection) else 'DISCLOSURE_TRI_DOWN',
                emboss=False,
            ).name = ""
        else:
            row.label(text="", icon='BLANK1')
        active = context.view_layer.active_layer_collection == context.view_layer.layer_collection
        row.operator(
            LIGHTHOUSE_OT_set_active_collection.bl_idname,
            text="Scene Collection",
            icon='OUTLINER_COLLECTION',
            emboss=active,
            depress=active,
        ).name = ""
        # Blanks where other headers have Select, Hide and Solo, so Move here lines up with theirs.
        actions = row.row(align=True)
        actions.label(text="", icon='BLANK1')
        actions.operator(LIGHTHOUSE_OT_move_to_group.bl_idname, text="", icon='IMPORT').name = ""
        actions.label(text="", icon='BLANK1')
        actions.label(text="", icon='BLANK1')

    def draw_group(self, context, entry):
        collection = entry.collection
        row = self.layout.row(align=True)
        indent(row, entry.depth)
        if entry.foldable:
            target(row.operator(
                LIGHTHOUSE_OT_toggle_group.bl_idname,
                text="",
                icon='DISCLOSURE_TRI_RIGHT' if collection.lighthouse_collapsed else 'DISCLOSURE_TRI_DOWN',
                emboss=False,
            ), collection)
        else:
            row.label(text="", icon='BLANK1')
        active = context.view_layer.active_layer_collection.collection == collection
        target(row.operator(
            LIGHTHOUSE_OT_set_active_collection.bl_idname,
            text=f"{collection.name} ({entry.count})",
            icon='OUTLINER_COLLECTION',
            emboss=active,
            depress=active,
        ), collection)
        # All four are always drawn so columns line up; Select and Solo have nothing to act on at (0).
        actions = row.row(align=True)
        select = actions.row(align=True)
        select.enabled = bool(entry.count)
        target(select.operator(LIGHTHOUSE_OT_select_group.bl_idname, text="", icon='RESTRICT_SELECT_OFF'), collection)
        target(actions.operator(LIGHTHOUSE_OT_move_to_group.bl_idname, text="", icon='IMPORT'), collection)
        hidden = collection.hide_render and collection.hide_viewport
        target(actions.operator(
            LIGHTHOUSE_OT_hide_group.bl_idname,
            text="",
            icon='HIDE_ON' if hidden else 'HIDE_OFF',
            depress=hidden,
        ), collection)
        soloed = group_soloed(context.scene, collection)
        solo = actions.row(align=True)
        solo.enabled = bool(entry.count)
        target(solo.operator(
            LIGHTHOUSE_OT_solo_group.bl_idname,
            text="",
            icon='SOLO_ON' if soloed else 'SOLO_OFF',
            depress=soloed,
        ), collection)

    def draw_lights_row(self, entry):
        collection = entry.collection
        row = self.layout.row(align=True)
        indent(row, entry.depth)
        target(row.operator(
            LIGHTHOUSE_OT_toggle_lights_row.bl_idname,
            text="",
            icon='DISCLOSURE_TRI_RIGHT' if is_lights_folded(collection) else 'DISCLOSURE_TRI_DOWN',
            emboss=False,
        ), collection)
        row.label(text=f"Lights ({entry.count})", icon='LIGHT')

    def draw_light(self, context, entry):
        obj = entry.obj
        light = obj.data
        state = row_state(obj, context.view_layer, context.scene)
        row = self.layout.row(align=True)
        row.active = not state.dimmed
        indent(row, entry.depth)
        expanded = details_open(context.window_manager.lighthouse, obj)
        target(row.operator(
            LIGHTHOUSE_OT_toggle_details.bl_idname,
            text="",
            icon='DISCLOSURE_TRI_DOWN' if expanded else 'DISCLOSURE_TRI_RIGHT',
            emboss=False,
        ), obj)
        light_type = row.row(align=True)
        light_type.enabled = not state.read_only
        light_type.prop(light, "type", icon_only=True)
        selected = obj.select_get(view_layer=context.view_layer)
        active = context.view_layer.objects.active == obj
        op = row.operator(
            LIGHTHOUSE_OT_select_light.bl_idname,
            text=obj.name,
            emboss=selected or active,
            depress=active,
        )
        target(op, obj)
        if light_info_tooltip(light.users - 1, entry.other_collections):
            op = row.operator(LIGHTHOUSE_OT_light_info.bl_idname, text="", icon='INFO', emboss=False)
            op.other_users = light.users - 1
            op.other_collections = entry.other_collections
        controls = row.row(align=True)
        controls.enabled = not state.read_only
        controls.prop(light, "energy", text="")
        unit = controls.row(align=True)
        unit.ui_units_x = UNIT_WIDTH
        unit.operator(LIGHTHOUSE_OT_power_unit.bl_idname, text="W", emboss=False).unit = power_unit(light)
        swatch = controls.row(align=True)
        swatch.ui_units_x = SWATCH_WIDTH
        swatch.prop(light, color_control(light), text="")
        toggles = row.row(align=True)
        op = toggles.operator(
            LIGHTHOUSE_OT_mute_light.bl_idname,
            text="",
            icon='HIDE_ON' if state.muted else 'HIDE_OFF',
            depress=state.muted,
        )
        target(op, obj)
        op = toggles.operator(
            LIGHTHOUSE_OT_solo_light.bl_idname,
            text="",
            icon='SOLO_ON' if state.soloed else 'SOLO_OFF',
            depress=state.soloed,
        )
        target(op, obj)
        if expanded:
            self.draw_details(obj, state, context.scene.render.engine)

    def draw_details(self, obj, state, engine):
        light = obj.data
        box = self.layout.box()
        box.active = not state.dimmed
        box.enabled = not state.read_only
        box.use_property_split = True
        box.prop(obj, "name")
        for path in detail_properties(light, engine):
            label = DETAIL_LABELS.get(path)
            box.prop(*detail_target(light, path), **({"text": label} if label else {}))


classes = (
    LIGHTHOUSE_PG_expanded,
    LIGHTHOUSE_PG_settings,
    LIGHTHOUSE_PG_solo_object,
    LIGHTHOUSE_PG_solo_collection,
    LIGHTHOUSE_PG_solo,
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_OT_add_light,
    LIGHTHOUSE_OT_new_collection,
    LIGHTHOUSE_OT_mute_light,
    LIGHTHOUSE_OT_solo_light,
    LIGHTHOUSE_OT_exit_solo,
    LIGHTHOUSE_OT_toggle_details,
    LIGHTHOUSE_OT_toggle_group,
    LIGHTHOUSE_OT_toggle_lights_row,
    LIGHTHOUSE_OT_set_active_collection,
    LIGHTHOUSE_OT_toggle_all_groups,
    LIGHTHOUSE_OT_clear_filters,
    LIGHTHOUSE_OT_select_group,
    LIGHTHOUSE_OT_move_to_group,
    LIGHTHOUSE_OT_hide_group,
    LIGHTHOUSE_OT_solo_group,
    LIGHTHOUSE_OT_scale_lights,
    LIGHTHOUSE_OT_step_exposure,
    LIGHTHOUSE_OT_apply_preset,
    LIGHTHOUSE_OT_save_preset,
    LIGHTHOUSE_OT_delete_preset,
    LIGHTHOUSE_OT_light_info,
    LIGHTHOUSE_OT_power_unit,
    LIGHTHOUSE_PT_intensity,
    LIGHTHOUSE_PT_presets,
    LIGHTHOUSE_PT_lights,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.lighthouse = bpy.props.PointerProperty(type=LIGHTHOUSE_PG_settings)
    bpy.types.Scene.lighthouse_solo = bpy.props.PointerProperty(type=LIGHTHOUSE_PG_solo)
    bpy.types.Collection.lighthouse_collapsed = bpy.props.BoolProperty(
        name="Collapsed",
        description="Hide this collection's lights and sub-collections in the Lights list",
    )
    bpy.types.Collection.lighthouse_lights_collapsed = bpy.props.BoolProperty(
        name="Lights Folded",
        description="Hide this collection's own lights in the Lights list, keeping its sub-collections",
    )


def unregister():
    del bpy.types.Collection.lighthouse_lights_collapsed
    del bpy.types.Collection.lighthouse_collapsed
    del bpy.types.Scene.lighthouse_solo
    del bpy.types.WindowManager.lighthouse
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
