from typing import NamedTuple


class RowState(NamedTuple):
    dimmed: bool
    read_only: bool
    shared: bool


def light_objects(view_layer):
    """Every light object in the given view layer."""
    return [obj for obj in view_layer.objects if obj.type == 'LIGHT']


def listed_lights(view_layer, name_filter="", type_filter='ALL'):
    """The lights the panel shows: matching type, name containing the search (any case),
    sorted by name ignoring case."""
    needle = name_filter.casefold()
    matches = [
        obj for obj in light_objects(view_layer)
        if type_filter in ('ALL', obj.data.type) and needle in obj.name.casefold()
    ]
    return sorted(matches, key=lambda obj: obj.name.casefold())


def power_unit(light):
    """Display unit for a light's power: irradiance for sun, watts otherwise."""
    return "W/m²" if light.type == 'SUN' else "W"


def row_state(obj, view_layer):
    """How a light's row is drawn: dimmed when hidden in the viewport, the render or the view layer;
    read-only when its light data comes from a library or a non-editable (system) override;
    shared when other objects use the same light data."""
    light = obj.data
    override = light.override_library
    return RowState(
        dimmed=obj.hide_viewport or obj.hide_render or obj.hide_get(view_layer=view_layer),
        read_only=light.library is not None or (override is not None and override.is_system_override),
        shared=light.users > 1,
    )
