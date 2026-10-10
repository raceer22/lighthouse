from collections import Counter
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


class GroupEntry(NamedTuple):
    collection: object
    depth: int
    count: int


class LightEntry(NamedTuple):
    obj: object
    depth: int
    other_collections: int


def list_entries(view_layer, name_filter="", type_filter='ALL', grouped=True):
    """The rows the Lights panel draws, in order: collections nested as in the outliner
    (only those on the path to a listed light), each followed by its own lights sorted by name
    ignoring case, then its sub-collections. A collapsed collection keeps its header and count but
    nothing below it. Scene Collection lights come first, with no header.
    When not grouped, or while searching, it is the flat listed_lights() order with no headers."""
    if not grouped or name_filter:
        return [LightEntry(obj, 0, 0) for obj in listed_lights(view_layer, name_filter, type_filter)]
    listed = set(listed_lights(view_layer, type_filter=type_filter))
    entries = _collection_entries(view_layer.layer_collection, listed, 0)[0]
    places = Counter(entry.obj for entry in entries if isinstance(entry, LightEntry))
    return [
        entry._replace(other_collections=places[entry.obj] - 1) if isinstance(entry, LightEntry) else entry
        for entry in entries
    ]


def group_lights(view_layer, collection, type_filter='ALL'):
    """The listed lights in a collection and its sub-collections, each once, in list order.
    The same lights its header counts."""
    layer_collection = _find_layer_collection(view_layer.layer_collection, collection)
    if layer_collection is None:
        return []
    listed = set(listed_lights(view_layer, type_filter=type_filter))
    return list(_collection_entries(layer_collection, listed, 0)[1])


def _find_layer_collection(layer_collection, collection):
    for child in layer_collection.children:
        if child.exclude:
            continue
        if child.collection == collection:
            return child
        found = _find_layer_collection(child, collection)
        if found is not None:
            return found
    return None


def _collection_entries(layer_collection, listed, depth):
    """The entries inside a layer collection, at the given depth, and the listed lights they hold
    (a dict used as an ordered set, in list order)."""
    own = sorted((obj for obj in layer_collection.collection.objects if obj in listed),
                 key=lambda obj: obj.name.casefold())
    entries = [LightEntry(obj, depth, 0) for obj in own]
    lights = dict.fromkeys(own)
    for child in layer_collection.children:
        if child.exclude:
            continue
        child_entries, child_lights = _collection_entries(child, listed, depth + 1)
        if child_lights:
            entries.append(GroupEntry(child.collection, depth, len(child_lights)))
            if not is_collapsed(child.collection):
                entries += child_entries
            lights |= child_lights
    return entries, lights


def is_collapsed(collection):
    """True when the collection is collapsed in the list. False while the add-on's property is
    unregistered."""
    return getattr(collection, "lighthouse_collapsed", False)


MAX_INDENT = 3


def indent_level(depth):
    """How many indent steps a row at this nesting depth gets: one per level, at most MAX_INDENT."""
    return min(depth, MAX_INDENT)


def light_info_tooltip(other_users, other_collections):
    """Tooltip for a row's info icon, naming whichever case applies: light data shared with other
    objects, and the object listed in other collections. Empty when neither applies (no icon)."""
    parts = []
    if other_users:
        parts.append(f"Light data is shared with {other_users} other object{'' if other_users == 1 else 's'}")
    if other_collections:
        parts.append(f"Also in {other_collections} other collection{'' if other_collections == 1 else 's'}")
    return ". ".join(parts)


def power_unit(light):
    """Display unit for a light's power: irradiance for sun, watts otherwise."""
    return "W/m²" if light.type == 'SUN' else "W"


# Added after Blender 4.2: exposure in 4.4, temperature in 5.0. Shown only when the light has them.
NEWER_DETAILS = ("exposure", "use_temperature", "temperature")
SOFT_SIZE = {'POINT': "shadow_soft_size", 'SPOT': "shadow_soft_size", 'SUN': "angle"}
# Labels matching Blender's own light panel where they differ from the RNA name
DETAIL_LABELS = {"shadow_soft_size": "Radius", "use_shadow": "Use Shadow"}
SHARED_DETAILS = ("specular_factor", "diffuse_factor", "volume_factor", "use_shadow")
CYCLES_DETAILS = ("cycles.max_bounces", "cycles.use_multiple_importance_sampling", "cycles.is_caustics_light")


def detail_properties(light, engine):
    """RNA paths, relative to the light data, of the extra settings a row's detail section shows
    for this light's type under the given render engine. Paths the light lacks are left out."""
    paths = [name for name in NEWER_DETAILS if has_property(light, name)]
    paths += [SOFT_SIZE[light.type]] if light.type in SOFT_SIZE else []
    paths += SHARED_DETAILS
    if engine == 'CYCLES':
        paths += CYCLES_DETAILS
        if light.type == 'AREA':
            paths.append("cycles.is_portal")
    return [path for path in paths if _has_path(light, path)]


def detail_target(light, path):
    """The (owner, property name) pair to draw or edit a detail path with, e.g. "cycles.max_bounces"
    gives (light.cycles, "max_bounces")."""
    owner_path, _, prop = path.rpartition(".")
    return (light.path_resolve(owner_path) if owner_path else light), prop


def has_property(rna, name):
    """True when the RNA struct has a property of that name, so properties newer than the
    oldest supported Blender (4.2) can be checked before use."""
    return name in rna.bl_rna.properties


def color_control(light):
    """The light property a row's fixed color slot shows: "temperature" for a light using
    blackbody temperature (Blender 5.0+), "color" otherwise."""
    if has_property(light, "use_temperature") and light.use_temperature:
        return "temperature"
    return "color"


def _has_path(light, path):
    try:
        light.path_resolve(path)
    except ValueError:
        return False
    return True


def details_open(settings, obj):
    """True when the light's details are open in the list (every row of the object shares it)."""
    return any(item.obj == obj for item in settings.expanded)


def toggle_details(settings, obj, keep_others=False):
    """Open the light's details, closing every other light's unless keep_others is set,
    or close them if they are open. Entries of deleted lights are dropped."""
    expanded = settings.expanded
    for index in reversed(range(len(expanded))):
        if expanded[index].obj is None:
            expanded.remove(index)
    if details_open(settings, obj):
        expanded.remove(next(i for i, item in enumerate(expanded) if item.obj == obj))
        return
    if not keep_others:
        expanded.clear()
    expanded.add().obj = obj


def is_read_only(id_data):
    """True when an ID (light data, object, collection) comes from a library or a non-editable (system) override."""
    override = id_data.override_library
    return id_data.library is not None or (override is not None and override.is_system_override)


def move_lights(objects, collection):
    """Link each object into the collection and unlink it from every other one, the Scene
    Collection included. Read-only (library or system override) objects are skipped.
    Returns how many were moved and how many skipped."""
    movable = [obj for obj in objects if not is_read_only(obj)]
    for obj in movable:
        if collection not in obj.users_collection:
            collection.objects.link(obj)
        for owner in list(obj.users_collection):
            if owner != collection:
                owner.objects.unlink(obj)
    return len(movable), len(objects) - len(movable)


def move_summary(moved, skipped, collection_name):
    """Status bar message after moving, e.g. "Moved 3 lights to Key, skipped 1 read-only"."""
    message = f"Moved {moved} light{'' if moved == 1 else 's'} to {collection_name}"
    return message + (f", skipped {skipped} read-only" if skipped else "")


def row_state(obj, view_layer, scene=None):
    """How a light's row is drawn: dimmed when hidden in the render or not visible in the view layer
    (its own flags, or a hidden or excluded collection); read-only when its light data comes from a
    library or a non-editable (system) override; shared when other objects use the same light data;
    muted when its own flags hide it in both the viewport and the render; soloed when it is the
    scene's soloed light."""
    light = obj.data
    return RowState(
        dimmed=obj.hide_render or not obj.visible_get(view_layer=view_layer),
        read_only=is_read_only(light),
        shared=light.users > 1,
        muted=obj.hide_render and obj.hide_viewport,
        soloed=scene is not None and scene.lighthouse_solo.active and scene.lighthouse_solo.light == obj,
    )


def group_soloed(scene, collection):
    """True when the collection is the scene's soloed group (its header's solo icon is pressed)."""
    solo = scene.lighthouse_solo
    return solo.active and solo.group == collection


def toggle_solo_light(solo, view_layer, obj):
    """Solo a light: show it and hide every other light, unhiding the collections that hold it
    and their ancestors. Pressing it again on the soloed light restores the snapshot (see _solo)."""
    if solo.active and solo.light == obj:
        _unsolo(solo)
        return
    holders = set(obj.users_collection)
    _solo(solo, view_layer, [obj], _collection_paths(view_layer, lambda c: c in holders))
    solo.light = obj


def toggle_solo_group(solo, view_layer, collection):
    """Solo a group: show every light in the collection and its sub-collections and hide every
    other light, unhiding the collection, its sub-collections and its ancestors. Pressing it again
    on the soloed group restores the snapshot (see _solo)."""
    if solo.active and solo.group == collection:
        _unsolo(solo)
        return
    inside = {collection, *collection.children_recursive}
    shown = set(collection.all_objects)
    _solo(solo, view_layer, shown, _collection_paths(view_layer, lambda c: c in inside))
    solo.group = collection


def _solo(solo, view_layer, shown, collections):
    """Show the given lights, hide every other light and unhide the given collections.
    The first solo snapshots every light's flags; a collection's flags are snapshotted the
    first time solo unhides it. Switching target keeps the snapshot and only adds new items."""
    if not solo.active:
        solo.objects.clear()
        solo.collections.clear()
        solo.active = True
    solo.light = solo.group = None
    lights = light_objects(view_layer)
    saved = {item.object for item in solo.objects}
    for obj in lights:
        if obj not in saved:
            item = solo.objects.add()
            item.object, item.hide_render, item.hide_viewport = obj, obj.hide_render, obj.hide_viewport
    saved = {item.collection for item in solo.collections}
    for collection in collections:
        if collection not in saved:
            item = solo.collections.add()
            item.collection = collection
            item.hide_render, item.hide_viewport = collection.hide_render, collection.hide_viewport
        collection.hide_render = collection.hide_viewport = False
    for obj in lights:
        obj.hide_render = obj.hide_viewport = obj not in shown


def _unsolo(solo):
    """Restore every snapshotted light and collection still around, then clear the snapshot."""
    for item in solo.objects:
        if item.object is not None:
            item.object.hide_render, item.object.hide_viewport = item.hide_render, item.hide_viewport
    for item in solo.collections:
        if item.collection is not None:
            item.collection.hide_render, item.collection.hide_viewport = item.hide_render, item.hide_viewport
    solo.objects.clear()
    solo.collections.clear()
    solo.light = solo.group = None
    solo.active = False


def _collection_paths(view_layer, wanted):
    """The collections in the view layer tree (excluded ones left out) that wanted() accepts,
    with all their ancestors, each once."""
    found = {}

    def walk(layer_collection, path):
        for child in layer_collection.children:
            if child.exclude:
                continue
            here = path + [child.collection]
            if wanted(child.collection):
                found.update(dict.fromkeys(here))
            walk(child, here)

    walk(view_layer.layer_collection, [])
    return list(found)


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
