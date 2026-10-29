import bpy

from ..lights import (
    GroupEntry,
    details_open,
    empty_message,
    group_soloed,
    is_lights_folded,
    is_read_only,
    LightsEntry,
    SceneEntry,
    light_objects,
    list_entries,
    listed_groups,
    tree_under_message,
    row_state,
    supports_temperature,
    world_setup,
    world_mute_node,
    world_muted,
)
from ..common import target, current_new_light_mode, all_collapsed, EV_STEPS
from ..operators.groups import (
    LIGHTHOUSE_OT_set_active_collection,
    LIGHTHOUSE_OT_select_group,
    LIGHTHOUSE_OT_move_to_group,
    LIGHTHOUSE_OT_hide_group,
)
from ..operators.lights import (
    LIGHTHOUSE_OT_toggle_new_light_mode,
    LIGHTHOUSE_OT_scale_lights,
    LIGHTHOUSE_OT_step_exposure,
)
from ..operators.presets import (
    LIGHTHOUSE_OT_apply_preset,
    LIGHTHOUSE_OT_save_preset,
    LIGHTHOUSE_OT_delete_preset,
)
from ..operators.solo import LIGHTHOUSE_OT_exit_solo, LIGHTHOUSE_OT_solo_group, LIGHTHOUSE_OT_solo_world
from ..operators.view import (
    LIGHTHOUSE_OT_toggle_details,
    LIGHTHOUSE_OT_toggle_group,
    LIGHTHOUSE_OT_reveal_active_light,
    LIGHTHOUSE_OT_toggle_lights_row,
    LIGHTHOUSE_OT_clear_filters,
    LIGHTHOUSE_OT_toggle_all_groups,
)
from ..operators.world import LIGHTHOUSE_OT_add_world_rotation, LIGHTHOUSE_OT_mute_world
from .draw import draw_load_hdri, indent, draw_light_controls, draw_light_details
from .menus import LIGHTHOUSE_MT_new


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


classes = (
    LIGHTHOUSE_PT_lights,
    LIGHTHOUSE_PT_world,
    LIGHTHOUSE_PT_intensity,
    LIGHTHOUSE_PT_presets,
    LIGHTHOUSE_PT_active_light,
)
