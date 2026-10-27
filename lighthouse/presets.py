import json
import re
from pathlib import Path
from typing import NamedTuple

from .lights import has_property, is_read_only


class Preset(NamedTuple):
    label: str
    type_compat: frozenset
    power: float
    color: tuple  # RGB, and the fallback where Kelvin isn't available (Blender before 5.0)
    radius: float
    exposure: float = 0.0
    use_temperature: bool = False
    temperature: float = 6500.0


DEFAULT_PRESETS = (
    Preset("Studio Softbox", frozenset({'AREA'}), 250.0, (1.0, 0.98, 0.95), 0.50, use_temperature=True, temperature=5600.0),
    Preset("Warm Interior Bulb", frozenset({'POINT', 'SPOT', 'AREA'}), 40.0, (1.0, 0.73, 0.45), 0.035, use_temperature=True, temperature=2700.0),
    Preset("Midday Sun", frozenset({'SUN'}), 4.5, (1.0, 0.97, 0.92), 0.0093, use_temperature=True, temperature=5500.0),
    Preset("Golden Hour Sun", frozenset({'SUN'}), 2.0, (1.0, 0.65, 0.35), 0.018, use_temperature=True, temperature=2800.0),
    Preset("Moonlight", frozenset({'SUN'}), 0.05, (0.82, 0.90, 1.0), 0.0093, use_temperature=True, temperature=4100.0),
)


USER_PREFIX = "USER:"
DEFAULTS_MARKER = ".defaults_installed"


def preset_from_light(light, label):
    """A preset holding the light's power, color, soft size (as a radius), and its exposure and
    temperature where the light has them, compatible with sun lights if the light is a sun,
    and with point, spot and area lights otherwise."""
    if light.type == 'AREA':
        radius = light.size / 2
    elif light.type == 'SUN':
        radius = light.angle
    else:
        radius = light.shadow_soft_size
    compat = {'SUN'} if light.type == 'SUN' else {'POINT', 'SPOT', 'AREA'}
    newer = {name: getattr(light, name) for name in ("exposure", "use_temperature", "temperature")
             if has_property(light, name)}
    return Preset(label, frozenset(compat), light.energy, tuple(light.color), radius, **newer)


def preset_path(folder, label):
    return Path(folder) / (re.sub(r'[^\w\- ]', '_', label) + ".json")


def save_user_preset(folder, preset):
    data = preset._asdict() | {'type_compat': sorted(preset.type_compat)}
    preset_path(folder, preset.label).write_text(json.dumps(data, indent=2))


def restore_default_presets(folder):
    """Write each default preset whose file is missing, never overwriting one.
    Returns the labels written."""
    written = []
    for preset in DEFAULT_PRESETS:
        if not preset_path(folder, preset.label).exists():
            save_user_preset(folder, preset)
            written.append(preset.label)
    return written


def seed_default_presets(folder):
    """Write the default presets the first time the folder is used, then leave a marker so
    defaults the user deletes stay deleted."""
    marker = Path(folder) / DEFAULTS_MARKER
    if not marker.exists():
        restore_default_presets(folder)
        marker.touch()


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
                # Added in v2: files saved before have no exposure and temperature off.
                float(data.get('exposure', 0.0)), bool(data.get('use_temperature', False)),
                float(data.get('temperature', 6500.0)),
            )
        except (OSError, ValueError, TypeError, KeyError) as error:
            print(f"Lighthouse: Skipped user preset {path.name}: {error!r}")
            continue
        presets[USER_PREFIX + path.stem] = preset
    return dict(sorted(presets.items(), key=lambda item: item[1].label.lower()))


WHITE = (1.0, 1.0, 1.0)


def apply_preset(lights, preset):
    """Set power, color, soft size, exposure and temperature from the preset on each light
    object's data whose type the preset is compatible with. Soft size is the radius for point
    and spot lights, the diameter for area lights and the angle for suns. Exposure and
    temperature are set only where the light has them (Blender 4.4+ and 5.0+). The color tints
    the temperature, so a light switched to Kelvin gets white instead of the RGB fallback.
    Lights from a library or a system override are left alone.
    Returns how many lights were changed, skipped as incompatible and skipped as read-only."""
    editable = [obj.data for obj in lights if not is_read_only(obj.data)]
    changed = [light for light in editable if light.type in preset.type_compat]
    for light in changed:
        light.energy = preset.power
        light.color = preset.color
        if has_property(light, "exposure"):
            light.exposure = preset.exposure
        if has_property(light, "use_temperature"):
            light.use_temperature = preset.use_temperature
            light.temperature = preset.temperature
            if preset.use_temperature:
                light.color = WHITE
        if light.type == 'AREA':
            light.size = 2 * preset.radius
        elif light.type == 'SUN':
            light.angle = preset.radius
        else:
            light.shadow_soft_size = preset.radius
    return len(changed), len(editable) - len(changed), len(lights) - len(editable)


def preset_summary(preset, changed, incompatible, read_only=0):
    """Status bar message after applying, e.g.
    "Applied Candle to 2 lights (1 skipped: incompatible type, 1 skipped: read-only)"."""
    message = f"Applied {preset.label} to {changed} light{'' if changed == 1 else 's'}"
    reasons = [f"{count} skipped: {reason}" for count, reason in
               ((incompatible, "incompatible type"), (read_only, "read-only")) if count]
    return message + (f" ({', '.join(reasons)})" if reasons else "")
