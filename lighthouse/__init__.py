# Copyright (C) 2026 raceer22
# Licensed under the GNU General Public License v3 or later (GPL-3.0-or-later)
import bpy

from . import operators, properties
from .lights import (
    DETAIL_LABELS,
    find_object,
    light_linking_note,
    linking_counts,
    linking_tooltip,
    shared_label,
    receivers,
    id_key,
    GroupEntry,
    color_control,
    detail_properties,
    detail_target,
    details_open,
    empty_message,
    group_soloed,
    hdri_addable,
    hdri_target,
    is_solo_target,
    indent_level,
    is_lights_folded,
    is_read_only,
    light_info_tooltip,
    LightsEntry,
    SceneEntry,
    light_objects,
    list_entries,
    listed_groups,
    tree_under_message,
    light_scope,
    scope_label,
    power_unit,
    row_state,
    supports_temperature,
    world_setup,
    world_mute_node,
    world_muted,
)
from .common import (
    preset_items,
    LIGHT_TYPES,
    scene_or_collection,
    target,
    NEW_LIGHT_MODES,
    current_new_light_mode,
    light_muted,
    all_collapsed,
    EV_STEPS,
    target_collection,
)
from .handlers import register_last_light, unregister_last_light, migrate_solo_targets
from .properties import LIGHTHOUSE_PG_settings, LIGHTHOUSE_PG_solo
from .operators.groups import (
    LIGHTHOUSE_OT_new_collection,
    LIGHTHOUSE_OT_set_active_collection,
    LIGHTHOUSE_OT_select_group,
    LIGHTHOUSE_OT_move_to_group,
    LIGHTHOUSE_OT_hide_group,
)
from .operators.lights import (
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_OT_rename_light,
    LIGHTHOUSE_OT_delete_lights,
    LIGHTHOUSE_OT_duplicate_lights,
    LIGHTHOUSE_OT_toggle_new_light_mode,
    LIGHTHOUSE_OT_add_light,
    LIGHTHOUSE_OT_mute_light,
    LIGHTHOUSE_OT_mute_lights,
    LIGHTHOUSE_OT_scale_lights,
    LIGHTHOUSE_OT_step_exposure,
    LIGHTHOUSE_OT_light_info,
    LIGHTHOUSE_OT_power_unit,
)
from .operators.linking import LIGHTHOUSE_OT_light_linking_info
from .operators.presets import (
    LIGHTHOUSE_OT_apply_preset,
    LIGHTHOUSE_OT_save_preset,
    LIGHTHOUSE_OT_delete_preset,
    LIGHTHOUSE_OT_restore_default_presets,
)
from .operators.solo import (
    LIGHTHOUSE_OT_solo_light,
    LIGHTHOUSE_OT_exit_solo,
    LIGHTHOUSE_OT_solo_group,
    LIGHTHOUSE_OT_solo_world,
)
from .operators.view import (
    LIGHTHOUSE_OT_toggle_details,
    LIGHTHOUSE_OT_toggle_group,
    LIGHTHOUSE_OT_reveal_active_light,
    LIGHTHOUSE_OT_toggle_lights_row,
    LIGHTHOUSE_OT_clear_filters,
    LIGHTHOUSE_OT_toggle_all_groups,
)
from .operators.world import (
    LIGHTHOUSE_OT_add_world_rotation,
    LIGHTHOUSE_OT_mute_world,
    LIGHTHOUSE_OT_load_hdri,
)


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
            draw_load_hdri(self.layout, world, setup)
        else:
            col = self.layout.column()
            col.enabled = not is_read_only(world)
            col.active = not muted
            col.prop(setup.background.inputs["Strength"], "default_value", text="Strength")
            if setup.rotation == 'MAPPING':
                col.prop(setup.mapping.inputs["Rotation"], "default_value", index=2, text="Rotation")
            elif setup.rotation == 'ADDABLE':
                col.operator(LIGHTHOUSE_OT_add_world_rotation.bl_idname, text="Add Rotation")
            draw_load_hdri(col, world, setup)


def draw_load_hdri(layout, world, setup):
    """Load HDRI…, for a world with exactly one Environment Texture (any setup), or a simple
    Background-only one, where it adds the texture."""
    if hdri_target(world) is not None or hdri_addable(setup):
        row = layout.row()
        row.enabled = not is_read_only(world)
        row.operator(LIGHTHOUSE_OT_load_hdri.bl_idname, text="Load HDRI…", icon='FILE_IMAGE')


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


class LIGHTHOUSE_MT_apply_preset(bpy.types.Menu):
    """The light right-click menu's Apply Preset submenu, for context.lighthouse_light and its selection."""
    bl_idname = "LIGHTHOUSE_MT_apply_preset"
    bl_label = "Apply Preset"

    def draw(self, context):
        obj = context.lighthouse_light
        for key, label, *_ in preset_items(self, context):
            op = target_light(self.layout.operator(LIGHTHOUSE_OT_apply_preset.bl_idname, text=label), obj)
            op.preset = key


def draw_light_menu(self, context):
    """Prepended to Blender's right-click menu (UI_MT_button_context_menu) for the light whose row name
    button is under the cursor: Rename and Frame (that light), Duplicate, Duplicate Linked, Delete,
    Apply Preset and Mute (its selection, see light_scope), Solo and Add to Solo (that light)."""
    op = getattr(context, "button_operator", None)
    if op is None or op.bl_rna.identifier != LIGHTHOUSE_OT_select_light.bl_rna.identifier:
        return
    obj = find_object(context.view_layer, op.name, op.library)
    if obj is None:
        return
    layout = self.layout
    rename = layout.row()
    rename.enabled = not is_read_only(obj)
    target_light(rename.operator(LIGHTHOUSE_OT_rename_light.bl_idname, text="Rename"), obj)
    # Exec, so select_light keeps action FRAME instead of reading it from the click's modifier keys.
    frame = layout.row()
    frame.operator_context = 'EXEC_DEFAULT'
    target_light(frame.operator(LIGHTHOUSE_OT_select_light.bl_idname, text="Frame"), obj).action = 'FRAME'
    count = len(light_scope(context.view_layer, obj))
    target_light(layout.operator(LIGHTHOUSE_OT_duplicate_lights.bl_idname, text=scope_label("Duplicate", count)), obj)
    target_light(layout.operator(LIGHTHOUSE_OT_duplicate_lights.bl_idname,
                                 text=scope_label("Duplicate Linked", count)), obj).linked = True
    target_light(layout.operator(LIGHTHOUSE_OT_delete_lights.bl_idname, text=scope_label("Delete", count)), obj)
    layout.context_pointer_set("lighthouse_light", obj)
    layout.menu(LIGHTHOUSE_MT_apply_preset.bl_idname, text="Apply Preset", icon='PRESET')
    layout.menu(LIGHTHOUSE_MT_new_light.bl_idname, text="New Light", icon='LIGHT')
    verb = "Unmute" if light_muted(obj) else "Mute"
    target_light(layout.operator(LIGHTHOUSE_OT_mute_lights.bl_idname, text=scope_label(verb, count)), obj)
    solo = context.scene.lighthouse_solo
    soloed = is_solo_target(solo, obj)
    target_light(layout.operator(LIGHTHOUSE_OT_solo_light.bl_idname, text="Exit Solo" if soloed else "Solo"), obj)
    target_light(layout.operator(LIGHTHOUSE_OT_solo_light.bl_idname,
                                 text="Remove from Solo" if soloed else "Add to Solo"), obj).extend = True
    layout.separator()


def target_light(op, obj):
    """Point a light operator's name and library at obj."""
    op.name, op.library = id_key(obj)
    return op


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
    controls = row.row(align=True)
    controls.enabled = not state.read_only
    controls.prop(light, "energy", text="")
    unit = controls.row(align=True)
    unit.alignment = "CENTER"
    unit.ui_units_x = UNIT_WIDTH + 0.4
    if linking_tooltip(*counts):
        op = unit.operator(LIGHTHOUSE_OT_light_linking_info.bl_idname, text="", icon='LINKED', emboss=False)
        target(op, obj)
        op.included, op.excluded, op.included_collections, op.excluded_collections = counts
    else:
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
            obj = context.scene.lighthouse_last_light
        if obj is None:
            self.layout.label(text="Select a light")
            return
        state = row_state(obj, context.view_layer, context.scene)
        row = self.layout.row(align=True)
        row.active = not state.dimmed
        # What the list's other_collections counts for a light listed once per collection holding it.
        draw_light_controls(row, context, obj, state, max(len(obj.users_collection) - 1, 0))
        draw_light_details(self.layout, obj, state, context.scene.render.engine)


classes = properties.classes + operators.classes + (
    LIGHTHOUSE_MT_new_light,
    LIGHTHOUSE_MT_apply_preset,
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
    bpy.app.handlers.load_post.append(migrate_solo_targets)
    bpy.types.UI_MT_button_context_menu.prepend(draw_light_menu)
    register_last_light()


def unregister():
    bpy.app.handlers.load_post.remove(migrate_solo_targets)
    bpy.types.UI_MT_button_context_menu.remove(draw_light_menu)
    bpy.types.UI_MT_button_context_menu.remove(draw_group_menu)
    del bpy.types.Collection.lighthouse_lights_collapsed
    del bpy.types.Collection.lighthouse_collapsed
    del bpy.types.Scene.lighthouse_new_lights
    del bpy.types.Scene.lighthouse_solo
    del bpy.types.WindowManager.lighthouse
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unregister_last_light()
