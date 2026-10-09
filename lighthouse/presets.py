import json
import re
from pathlib import Path
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


USER_PREFIX = "USER:"


def preset_from_light(light, label):
    """A preset holding the light's power, color and soft size (as a radius), compatible with
    sun lights if the light is a sun, and with point, spot and area lights otherwise."""
    if light.type == 'AREA':
        radius = light.size / 2
    elif light.type == 'SUN':
        radius = light.angle
    else:
        radius = light.shadow_soft_size
    compat = {'SUN'} if light.type == 'SUN' else {'POINT', 'SPOT', 'AREA'}
    return Preset(label, frozenset(compat), light.energy, tuple(light.color), radius)


def preset_path(folder, label):
    return Path(folder) / (re.sub(r'[^\w\- ]', '_', label) + ".json")


def save_user_preset(folder, preset):
    data = preset._asdict() | {'type_compat': sorted(preset.type_compat)}
    preset_path(folder, preset.label).write_text(json.dumps(data, indent=2))


def delete_user_preset(folder, key):
    (Path(folder) / (key.removeprefix(USER_PREFIX) + ".json")).unlink(missing_ok=True)


def user_presets(folder):
    """User presets saved in folder, keyed by USER_PREFIX plus the file name, sorted by label.
    Files that can't be read as a preset are skipped with a warning on the console."""
    presets = {}
    for path in Path(folder).glob("*.json"):
        try:
            data = json.loads(path.read_text())
            preset = Preset(
                str(data['label']), frozenset(data['type_compat']), float(data['power']),
                tuple(float(c) for c in data['color'][:3]), float(data['radius']),
            )
        except (OSError, ValueError, TypeError, KeyError) as error:
            print(f"Lighthouse: Skipped user preset {path.name}: {error!r}")
            continue
        presets[USER_PREFIX + path.stem] = preset
    return dict(sorted(presets.items(), key=lambda item: item[1].label.lower()))


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
