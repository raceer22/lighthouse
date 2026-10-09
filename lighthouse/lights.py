import json
from typing import NamedTuple


class RowState(NamedTuple):
    dimmed: bool
    read_only: bool
    shared: bool
    muted: bool
    soloed: bool


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


def is_read_only(light):
    """True when light data comes from a library or a non-editable (system) override."""
    override = light.override_library
    return light.library is not None or (override is not None and override.is_system_override)


def row_state(obj, view_layer, scene=None):
    """How a light's row is drawn: dimmed when hidden in the viewport, the render or the view layer;
    read-only when its light data comes from a library or a non-editable (system) override;
    shared when other objects use the same light data; muted when hidden in both the viewport
    and the render; soloed when it is the scene's soloed light."""
    light = obj.data
    return RowState(
        dimmed=obj.hide_viewport or obj.hide_render or obj.hide_get(view_layer=view_layer),
        read_only=is_read_only(light),
        shared=light.users > 1,
        muted=obj.hide_render and obj.hide_viewport,
        soloed=scene is not None and soloed_light_name(scene) == obj.name,
    )


SOLO_KEY = "lighthouse_solo"


def soloed_light_name(scene):
    """Name of the light soloed in this scene, or None."""
    saved = scene.get(SOLO_KEY)
    return None if saved is None else json.loads(saved)["light"]


def toggle_solo(scene, view_layer, obj):
    """Solo a light: snapshot every light's visibility on the scene, then hide all others.
    Soloing another light while soloing switches to it and keeps the first snapshot,
    adding only lights created since then.
    Pressing it again on the soloed light restores the snapshot exactly and clears it."""
    saved = scene.get(SOLO_KEY)
    lights = light_objects(view_layer)
    if saved is None:
        solo = {"light": obj.name, "flags": {o.name: [o.hide_render, o.hide_viewport] for o in lights}}
    else:
        solo = json.loads(saved)
        if solo["light"] == obj.name:
            for name, (render, viewport) in solo["flags"].items():
                light = view_layer.objects.get(name)
                if light is not None:
                    light.hide_render, light.hide_viewport = render, viewport
            del scene[SOLO_KEY]
            return
        solo["light"] = obj.name
        for o in lights:
            solo["flags"].setdefault(o.name, [o.hide_render, o.hide_viewport])
    scene[SOLO_KEY] = json.dumps(solo)
    for other in lights:
        other.hide_render = other.hide_viewport = other != obj


def scale_lights(lights, factor):
    """Multiply the power of each light object's data by factor, once per datablock
    even when several of the objects share it, along with every keyframe of its power animation.
    Read-only (library) lights are skipped. Returns how many datablocks were scaled and how many
    of them were keyframed."""
    scaled = {obj.data for obj in lights if not is_read_only(obj.data)}
    keyframed = 0
    for light in scaled:
        light.energy *= factor
        energy_curve = _energy_fcurve(light)
        if energy_curve is not None:
            keyframed += 1
            for key in energy_curve.keyframe_points:
                key.co.y *= factor
                key.handle_left.y *= factor
                key.handle_right.y *= factor
            energy_curve.update()
    return len(scaled), keyframed


def scale_summary(scaled, keyframed):
    """Status bar message after scaling, e.g. "Scaled 4 lights (2 keyframed, whole animation)"."""
    message = f"Scaled {scaled} light{'' if scaled == 1 else 's'}"
    return message + (f" ({keyframed} keyframed, whole animation)" if keyframed else "")


def _energy_fcurve(light):
    """The F-curve animating a light's power in its assigned action, or None.
    Uses the action slot's channelbag (Blender 4.4+), else legacy action F-curves."""
    animation = light.animation_data
    if animation is None or animation.action is None:
        return None
    from bpy_extras import anim_utils
    if hasattr(anim_utils, "action_get_channelbag_for_slot"):
        bag = anim_utils.action_get_channelbag_for_slot(animation.action, animation.action_slot)
        if bag is not None:
            return bag.fcurves.find("energy")
    fcurves = getattr(animation.action, "fcurves", None)
    return None if fcurves is None else fcurves.find("energy")
