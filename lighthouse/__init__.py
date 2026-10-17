# Copyright (C) 2026 raceer22
# Licensed under the GNU General Public License v3 or later (GPL-3.0-or-later)
import zlib
from pathlib import Path

import bpy

from .lights import (
    DETAIL_LABELS,
    find_collection,
    _lookup,
    find_layer_collection,
    find_object,
    light_linking_note,
    linking_counts,
    linking_tooltip,
    clear_receivers,
    shared_label,
    link_receivers,
    receivers,
    remove_receiver,
    new_light_mode,
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
    reveal,
    row_state,
    scale_lights,
    scale_summary,
    solo_label,
    toggle_details,
    toggle_solo_group,
    supports_temperature,
    toggle_solo_light,
    toggle_solo_world,
    toggled_mode,
    unsolo,
    update_snapshot,
    world_setup,
    add_world_rotation,
    world_mute_node,
    world_muted,
)
from .presets import (
    apply_preset,
    delete_user_preset,
    preset_from_light,
    preset_path,
    preset_summary,
    restore_default_presets,
    save_user_preset,
    seed_default_presets,
    USER_PREFIX,
    user_presets,
)


_seeded = False


def presets_folder():
    """The presets folder, with the default presets written into it on the first call of the
    session if they never were."""
    global _seeded
    folder = Path(bpy.utils.extension_path_user(__package__, create=True))
    if not _seeded:
        seed_default_presets(folder)
        _seeded = True
    return folder


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
    return cached_user_presets()


_preset_items = []


def preset_items(self, context):
    """Every preset in the folder, sorted by label ignoring case. Each item's number comes from
    its key, so the stored value follows the preset when others are added or deleted."""
    _preset_items[:] = [
        (key, preset.label, "", 'NONE', zlib.crc32(key.encode()) & 0x7FFFFFFF)
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
    scale_scope: bpy.props.EnumProperty(name="Scope", description="Which lights to scale", items=SCOPE_ITEMS,
                                       default='SELECTED')
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
    world_soloed: bpy.props.BoolProperty()
    # The World snapshot, taken only by World solo: the node muted and its mute before solo
    world_saved: bpy.props.BoolProperty()
    world: bpy.props.PointerProperty(type=bpy.types.World)
    world_node: bpy.props.StringProperty()
    world_muted: bpy.props.BoolProperty()


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


def target_layer_collection(context, name, library):
    """The view layer's layer collection for a header button's target (name "" is the Scene
    Collection), or None when the collection doesn't exist or is excluded."""
    root = context.view_layer.layer_collection
    if name == "":
        return root
    collection = find_collection(name, library)
    return collection and find_layer_collection(root, collection)


def target(op, id):
    """Point a row or header button's operator at this exact light or collection."""
    op.name, op.library = id_key(id)


def draw_linking(box, obj, engine):
    """The Light Linking section at the end of a light's details, with a note (still editable)
    under an engine that doesn't render light linking."""
    linking = box.column()
    linking.use_property_split = False
    linking.label(text="Light Linking")
    note = light_linking_note(engine)
    if note:
        linking.label(text=note, icon='INFO')
    listed = receivers(obj)
    buttons = linking.row(align=True)
    target(buttons.operator("lighthouse.link_receivers", text="Link Selected"), obj)
    exclude = buttons.operator("lighthouse.link_receivers", text="Exclude Selected")
    target(exclude, obj)
    exclude.state = 'EXCLUDE'
    clear = buttons.row(align=True)
    clear.enabled = bool(listed)
    target(clear.operator("lighthouse.clear_receivers", text="Clear"), obj)
    shared = shared_label(obj)
    if shared:
        linking.label(text=shared, icon='INFO')
    for receiver in listed:
        row = linking.row(align=True)
        icon = 'OUTLINER_COLLECTION' if receiver.kind == 'COLLECTION' else 'OBJECT_DATA'
        row.label(text=receiver.id.name, icon=icon)
        row.prop(receiver.link.light_linking, "link_state", text="", expand=True)
        remove = row.operator("lighthouse.remove_receiver", text="", icon='X', emboss=False)
        target(remove, obj)
        remove.receiver, remove.receiver_library = id_key(receiver.id)
        remove.kind = receiver.kind


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


NEW_LIGHT_MODES = (
    ('FOLLOW', "Follow Default", "Use the default mode for new lights"),
    ('COLOR', "Color", "New lights start with a plain color"),
    ('KELVIN', "Kelvin", "New lights start at Blender's default temperature, with a white color"),
)


def default_new_light_mode(context):
    """The mode new lights start in when the file follows the default: the add-on preference when
    Lighthouse is installed, otherwise Color (as when tests import and register it directly)."""
    addon = context.preferences.addons.get(__package__)
    return addon.preferences.new_light_mode if addon and addon.preferences else 'COLOR'


def current_new_light_mode(context):
    return new_light_mode(context.scene.lighthouse_new_lights, default_new_light_mode(context))


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


# Where Shift+A (object.light_add) starts a light differently from bpy.data.lights.new() (checked in 5.2.2).
# Point and Spot already match.
SHIFT_A_VALUES = {
    'SUN': {"energy": 1.0},
    'AREA': {"size": 1.0, "size_y": 1.0},
}


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
    """Delete this preset from every file"""
    bl_idname = "lighthouse.delete_preset"
    bl_label = "Delete Light Preset"

    preset: bpy.props.EnumProperty(name="Preset", items=user_preset_items)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        settings = context.window_manager.lighthouse
        # Read before deleting: the dynamic enum resolves to another item once the file is gone.
        key = self.preset
        shown = settings.preset == key
        keys = list(cached_user_presets())
        delete_user_preset(presets_folder(), key)
        clear_user_presets_cache()
        if shown and key in keys:
            # The next one in dropdown order, or the new last one. With none left, assign
            # nothing: '' raises TypeError, and the dropdown already reads ''.
            index = keys.index(key)
            rest = keys[:index] + keys[index + 1:]
            if rest:
                settings.preset = rest[min(index, len(rest) - 1)]
        return {'FINISHED'}


class LIGHTHOUSE_OT_restore_default_presets(bpy.types.Operator):
    """Bring back deleted default presets. Defaults you edited are kept as they are"""
    bl_idname = "lighthouse.restore_default_presets"
    bl_label = "Restore Default Presets"

    def execute(self, context):
        restored = restore_default_presets(presets_folder())
        clear_user_presets_cache()
        if restored:
            self.report({'INFO'}, "Restored " + ", ".join(restored))
        else:
            self.report({'INFO'}, "Every default preset is already there")
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


class LIGHTHOUSE_OT_solo_world(bpy.types.Operator):
    """Light the scene with the World only: darken every light and un-mute the World,
    or restore every light's and the World's state if the World is already soloed"""
    bl_idname = "lighthouse.solo_world"
    bl_label = "Solo World"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        toggle_solo_world(context.scene.lighthouse_solo, context.view_layer, context.scene)
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


class LIGHTHOUSE_PT_world(bpy.types.Panel):
    bl_label = "World"
    bl_order = 1
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Lights"

    def draw(self, context):
        setup = world_setup(context.scene)
        if setup.state == 'NONE':
            self.layout.label(text="No world in this scene")
            return
        world = context.scene.world
        muted = world_muted(setup)
        row = self.layout.row(align=True)
        row.label(text=world.name, icon='WORLD')
        toggles = row.row(align=True)
        toggles.enabled = world_mute_node(setup) is not None and not is_read_only(world)
        toggles.operator(
            LIGHTHOUSE_OT_mute_world.bl_idname,
            text="",
            icon='HIDE_ON' if muted else 'HIDE_OFF',
            depress=muted,
        )
        soloed = context.scene.lighthouse_solo.world_soloed
        row.operator(
            LIGHTHOUSE_OT_solo_world.bl_idname,
            text="",
            icon='SOLO_ON' if soloed else 'SOLO_OFF',
            depress=soloed,
        )
        if setup.state == 'CUSTOM':
            self.layout.label(text="Custom world setup, edit in Shader Editor")
        else:
            col = self.layout.column()
            col.enabled = not is_read_only(world)
            col.active = not muted
            col.prop(setup.background.inputs["Strength"], "default_value", text="Strength")
            if setup.rotation == 'MAPPING':
                col.prop(setup.mapping.inputs["Rotation"], "default_value", index=2, text="Rotation")
            elif setup.rotation == 'ADDABLE':
                col.operator(LIGHTHOUSE_OT_add_world_rotation.bl_idname, text="Add Rotation")


class LIGHTHOUSE_PT_intensity(bpy.types.Panel):
    bl_label = "Intensity"
    bl_order = 2
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
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
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
        if settings.preset:
            row.operator(LIGHTHOUSE_OT_delete_preset.bl_idname, text="Delete").preset = settings.preset


class LIGHTHOUSE_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    new_light_mode: bpy.props.EnumProperty(
        name="New lights start in",
        description="Whether lights added by Lighthouse start in Color or in Kelvin, "
                    "in every file whose header toggle hasn't been flipped",
        items=NEW_LIGHT_MODES[1:],
        default='COLOR',
    )

    def draw(self, context):
        if supports_temperature():
            row = self.layout.row()
            row.label(text="New lights start in")
            row.prop(self, "new_light_mode", expand=True)
        self.layout.operator(LIGHTHOUSE_OT_restore_default_presets.bl_idname, text="Restore Default Presets")
        self.layout.label(text="Brings back deleted defaults. Defaults you edited are kept.")


def target_collection(op, context, collection):
    """Point an add_light or new_collection button at this collection instead of the active one."""
    op.name, op.library = ("", "") if collection == context.scene.collection else id_key(collection)
    op.use_active = False


class LIGHTHOUSE_MT_new_light(bpy.types.Menu):
    """Add a light at the 3D cursor"""
    bl_idname = "LIGHTHOUSE_MT_new_light"
    bl_label = "New Light"

    def draw(self, context):
        # Set by layout.context_pointer_set() in the group menu. Without it, lights go to the active collection.
        collection = getattr(context, "lighthouse_collection", None)
        for key, label, _description, icon, _number in LIGHT_TYPES:
            op = self.layout.operator(LIGHTHOUSE_OT_add_light.bl_idname, text=label, icon=icon)
            op.type = key
            if collection is not None:
                target_collection(op, context, collection)


class LIGHTHOUSE_MT_new(bpy.types.Menu):
    """Add a light or a collection in the active collection"""
    bl_idname = "LIGHTHOUSE_MT_new"
    bl_label = "New"

    def draw(self, context):
        entries = self.layout.column()
        entries.enabled = not is_read_only(context.view_layer.active_layer_collection.collection)
        entries.menu(LIGHTHOUSE_MT_new_light.bl_idname, text="New Light", icon='LIGHT')
        entries.operator(LIGHTHOUSE_OT_new_collection.bl_idname, text="New Collection", icon='COLLECTION_NEW')


def draw_group_menu(self, context):
    """Prepended to Blender's right-click menu (UI_MT_button_context_menu): New Light and New Collection
    for the collection whose header name button (or the Scene Collection row's) is under the cursor."""
    op = getattr(context, "button_operator", None)
    if op is None or op.bl_rna.identifier != LIGHTHOUSE_OT_set_active_collection.bl_rna.identifier:
        return
    collection = scene_or_collection(context, op.name, op.library)
    if collection is None:
        return
    entries = self.layout.column()
    entries.enabled = not is_read_only(collection)
    entries.context_pointer_set("lighthouse_collection", collection)
    entries.menu(LIGHTHOUSE_MT_new_light.bl_idname, text="New Light", icon='LIGHT')
    target_collection(
        entries.operator(LIGHTHOUSE_OT_new_collection.bl_idname, text="New Collection", icon='COLLECTION_NEW'),
        context, collection)
    self.layout.separator()


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
    bl_order = 4
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
            row.operator(LIGHTHOUSE_OT_reveal_active_light.bl_idname, text="", icon='VIEW_ZOOM')
        # Always drawn (greyed out by poll when solo is off) so the list never shifts.
        solo_active = context.scene.lighthouse_solo.active
        row.operator(LIGHTHOUSE_OT_exit_solo.bl_idname, text="",
                     icon='SOLO_ON' if solo_active else 'SOLO_OFF', depress=solo_active)
        row.menu(LIGHTHOUSE_MT_new.bl_idname, text="", icon='ADD')
        if supports_temperature():
            kelvin = current_new_light_mode(context) == 'KELVIN'
            row.operator(LIGHTHOUSE_OT_toggle_new_light_mode.bl_idname, text="",
                         icon='LIGHT_SUN' if kelvin else 'COLOR', depress=kelvin)
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
        draw_light_controls(row, context, obj, state, entry.other_collections)
        if expanded:
            self.draw_details(obj, state, context.scene.render.engine)

    def draw_details(self, obj, state, engine):
        draw_light_details(self.layout, obj, state, engine)


def draw_light_controls(row, context, obj, state, other_collections):
    """A light's controls after the details toggle, shared by list rows and the Active Light panel:
    type, name, info and linking icons, power, color or Kelvin, mute and solo."""
    light = obj.data
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
    if light_info_tooltip(light.users - 1, other_collections):
        op = row.operator(LIGHTHOUSE_OT_light_info.bl_idname, text="", icon='INFO', emboss=False)
        op.other_users = light.users - 1
        op.other_collections = other_collections
    counts = linking_counts(obj)
    if linking_tooltip(*counts):
        op = row.operator(LIGHTHOUSE_OT_light_linking_info.bl_idname, text="", icon='LINKED', emboss=False)
        target(op, obj)
        op.included, op.excluded, op.included_collections, op.excluded_collections = counts
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


def draw_light_details(layout, obj, state, engine):
    """A light's details box (name, the type's settings, light linking), shared by an expanded
    list row and the Active Light panel."""
    light = obj.data
    box = layout.box()
    box.active = not state.dimmed
    box.enabled = not state.read_only
    box.use_property_split = True
    box.prop(obj, "name")
    for path in detail_properties(light, engine):
        label = DETAIL_LABELS.get(path)
        box.prop(*detail_target(light, path), **({"text": label} if label else {}))
    draw_linking(box, obj, engine)

class LIGHTHOUSE_PT_active_light(bpy.types.Panel):
    """The active light's controls and details. Never hidden through poll, so the panels below
    don't jump as the active object switches between lights and other objects."""
    bl_label = "Active Light"
    bl_order = 0
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Lights"

    def draw(self, context):
        obj = context.view_layer.objects.active
        if obj is None or obj.type != 'LIGHT':
            self.layout.label(text="Select a light")
            return
        state = row_state(obj, context.view_layer, context.scene)
        row = self.layout.row(align=True)
        row.active = not state.dimmed
        # What the list's other_collections counts for a light listed once per collection holding it.
        draw_light_controls(row, context, obj, state, max(len(obj.users_collection) - 1, 0))
        draw_light_details(self.layout, obj, state, context.scene.render.engine)


classes = (
    LIGHTHOUSE_PG_expanded,
    LIGHTHOUSE_PG_settings,
    LIGHTHOUSE_PG_solo_object,
    LIGHTHOUSE_PG_solo_collection,
    LIGHTHOUSE_PG_solo,
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_OT_toggle_new_light_mode,
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
    LIGHTHOUSE_OT_reveal_active_light,
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
    LIGHTHOUSE_OT_restore_default_presets,
    LIGHTHOUSE_OT_light_info,
    LIGHTHOUSE_OT_light_linking_info,
    LIGHTHOUSE_OT_power_unit,
    LIGHTHOUSE_OT_add_world_rotation,
    LIGHTHOUSE_OT_mute_world,
    LIGHTHOUSE_OT_solo_world,
    LIGHTHOUSE_OT_link_receivers,
    LIGHTHOUSE_OT_remove_receiver,
    LIGHTHOUSE_OT_clear_receivers,
    LIGHTHOUSE_MT_new_light,
    LIGHTHOUSE_MT_new,
    LIGHTHOUSE_PT_lights,
    LIGHTHOUSE_PT_world,
    LIGHTHOUSE_PT_intensity,
    LIGHTHOUSE_PT_presets,
    LIGHTHOUSE_PT_active_light,
    LIGHTHOUSE_AP_preferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.lighthouse = bpy.props.PointerProperty(type=LIGHTHOUSE_PG_settings)
    bpy.types.Scene.lighthouse_solo = bpy.props.PointerProperty(type=LIGHTHOUSE_PG_solo)
    bpy.types.Scene.lighthouse_new_lights = bpy.props.EnumProperty(
        name="New Lights",
        description="Whether lights added by Lighthouse start in Color or in Kelvin in this file",
        items=NEW_LIGHT_MODES,
        default='FOLLOW',
    )
    bpy.types.Collection.lighthouse_collapsed = bpy.props.BoolProperty(
        name="Collapsed",
        description="Hide this collection's lights and sub-collections in the Lights list",
    )
    bpy.types.Collection.lighthouse_lights_collapsed = bpy.props.BoolProperty(
        name="Lights Folded",
        description="Hide this collection's own lights in the Lights list, keeping its sub-collections",
    )
    bpy.types.UI_MT_button_context_menu.prepend(draw_group_menu)


def unregister():
    bpy.types.UI_MT_button_context_menu.remove(draw_group_menu)
    del bpy.types.Collection.lighthouse_lights_collapsed
    del bpy.types.Collection.lighthouse_collapsed
    del bpy.types.Scene.lighthouse_new_lights
    del bpy.types.Scene.lighthouse_solo
    del bpy.types.WindowManager.lighthouse
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
