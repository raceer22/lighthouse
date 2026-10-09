from typing import NamedTuple


class Preset(NamedTuple):
    label: str
    type_compat: frozenset
    power: float
    color: tuple
    radius: float


BUILTIN_PRESETS = {
    'CANDLE': Preset("Candle", frozenset({'POINT', 'SPOT', 'AREA'}), 1.0, (1.0, 0.58, 0.16), 0.01),
    'BULB_60W': Preset("60W Bulb", frozenset({'POINT', 'SPOT', 'AREA'}), 60.0, (1.0, 0.71, 0.42), 0.03),
    'DAYLIGHT': Preset("Daylight", frozenset({'SUN'}), 4.0, (1.0, 0.96, 0.9), 0.0093),
}


def apply_preset(lights, preset):
    """Set power, color and soft size from the preset on each light object's data whose type
    the preset is compatible with. Soft size is the radius for point and spot lights, the
    diameter for area lights and the angle for suns. Returns how many lights were changed
    and how many skipped."""
    changed = [obj.data for obj in lights if obj.data.type in preset.type_compat]
    for light in changed:
        light.energy = preset.power
        light.color = preset.color
        if light.type == 'AREA':
            light.size = 2 * preset.radius
        elif light.type == 'SUN':
            light.angle = preset.radius
        else:
            light.shadow_soft_size = preset.radius
    return len(changed), len(lights) - len(changed)


def preset_summary(preset, changed, skipped):
    """Status bar message after applying, e.g. "Applied Candle to 3 lights (1 skipped: incompatible type)"."""
    message = f"Applied {preset.label} to {changed} light{'' if changed == 1 else 's'}"
    return message + (f" ({skipped} skipped: incompatible type)" if skipped else "")
