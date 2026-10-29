from ..lights import (
    DETAIL_LABELS,
    light_linking_note,
    linking_counts,
    linking_tooltip,
    shared_label,
    receivers,
    id_key,
    color_control,
    detail_properties,
    detail_target,
    hdri_addable,
    hdri_target,
    indent_level,
    is_read_only,
    light_info_tooltip,
    power_unit,
)
from ..common import target
from ..operators.lights import (
    LIGHTHOUSE_OT_select_light,
    LIGHTHOUSE_OT_mute_light,
    LIGHTHOUSE_OT_light_info,
    LIGHTHOUSE_OT_power_unit,
)
from ..operators.linking import LIGHTHOUSE_OT_light_linking_info
from ..operators.solo import LIGHTHOUSE_OT_solo_light
from ..operators.world import LIGHTHOUSE_OT_load_hdri


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


def draw_load_hdri(layout, world, setup):
    """Load HDRI…, for a world with exactly one Environment Texture (any setup), or a simple
    Background-only one, where it adds the texture."""
    if hdri_target(world) is not None or hdri_addable(setup):
        row = layout.row()
        row.enabled = not is_read_only(world)
        row.operator(LIGHTHOUSE_OT_load_hdri.bl_idname, text="Load HDRI…", icon='FILE_IMAGE')


INDENT_STEP = 1.5
# Fixed widths for a light row's unit label and color swatch (or Kelvin field), so power fills the rest with no gap.
UNIT_WIDTH = 1.5
SWATCH_WIDTH = 2


def indent(row, depth):
    """Indent a list row by a fixed step per nesting level, capped by indent_level()."""
    if indent_level(depth):
        row.separator(factor=INDENT_STEP * indent_level(depth))


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
