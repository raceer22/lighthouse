import zlib
from pathlib import Path

import bpy

from .lights import (
    find_collection,
    find_layer_collection,
    new_light_mode,
    id_key,
    is_collapsed,
    light_objects,
    listed_groups,
)
from .presets import seed_default_presets, user_presets


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


# Where Shift+A (object.light_add) starts a light differently from bpy.data.lights.new() (checked in 5.2.2).
# Point and Spot already match.
SHIFT_A_VALUES = {
    'SUN': {"energy": 1.0},
    'AREA': {"size": 1.0, "size_y": 1.0},
}


def light_muted(obj):
    """True when a light is muted: hidden in both the viewport and renders, as the row's mute sets it."""
    return obj.hide_render and obj.hide_viewport


def all_collapsed(view_layer, filters):
    """True when every listed collection with a triangle is collapsed (also when there are none).
    Only collections count: a folded lights row, or an empty collection with nothing to fold, never decides it."""
    groups = listed_groups(view_layer, filters.type_filter, filters.show_empty, foldable_only=True)
    return all(is_collapsed(collection) for collection in groups)


def _lights_in_scope(context, scope):
    """The view layer's lights for scope ALL, or the selected ones for SELECTED,
    and the warning to report if there are none."""
    lights = light_objects(context.view_layer)
    if scope == 'SELECTED':
        return [obj for obj in lights if obj.select_get()], "No lights selected"
    return lights, "No lights in the view layer"


POWER_UNIT_NAMES = {"W": "watts", "W/m²": "watts per square metre"}


EV_STEPS = ((-1.0, "−1"), (-0.5, "−½"), (-0.25, "−¼"), (0.25, "+¼"), (0.5, "+½"), (1.0, "+1"))


def target_collection(op, context, collection):
    """Point an add_light or new_collection button at this collection instead of the active one."""
    op.name, op.library = ("", "") if collection == context.scene.collection else id_key(collection)
    op.use_active = False
