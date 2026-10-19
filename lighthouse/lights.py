from collections import Counter
from typing import NamedTuple


class RowState(NamedTuple):
    dimmed: bool
    read_only: bool
    muted: bool
    soloed: bool


def id_key(id):
    """(name, library filepath) of an ID, with "" for local IDs. Names are only unique per library."""
    return (id.name, id.library.filepath if id.library else "")


def _lookup(ids, name, library):
    # bpy.data collections take (name, library filepath) keys, with None (not "") for local IDs.
    # With no library and no local match, fall back to the first ID with that name,
    # so name-only calls still reach linked data that has no local namesake.
    found = ids.get((name, library or None))
    return found if found is not None or library else ids.get(name)


def find_object(view_layer, name, library=""):
    """The object with this name from this library ("" for local, see _lookup), only if it is in the view layer."""
    import bpy
    obj = _lookup(bpy.data.objects, name, library)
    return obj if obj is not None and obj in view_layer.objects[:] else None


def find_collection(name, library=""):
    """The collection with this name from this library ("" for local, see _lookup)."""
    import bpy
    return _lookup(bpy.data.collections, name, library)


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


def empty_message(view_layer, name_filter="", type_filter='ALL'):
    """Why the Lights panel draws no rows, or None when list_entries() has rows to draw
    (a listed light inside a collapsed group still draws its group header)."""
    if listed_lights(view_layer, name_filter, type_filter):
        return None
    if light_objects(view_layer):
        return "No lights match the filter(s)"
    return "No lights in this view layer"


def tree_under_message(grouped, name_filter, show_empty):
    """True when the panel draws the collection tree under the empty-list message, so collections stay
    reachable as targets. Only in the grouped, unsearched list with empty collections shown."""
    return grouped and not name_filter and show_empty


class GroupEntry(NamedTuple):
    """A collection header. foldable: something is listed under it (own lights or sub-collections)."""
    collection: object
    depth: int
    count: int
    foldable: bool = True


class SceneEntry(NamedTuple):
    """The Scene Collection's header, first in the grouped list. count is its own listed lights."""
    collection: object
    count: int


class LightsEntry(NamedTuple):
    """The foldable row above a collection's own lights, when it also has listed sub-collections."""
    collection: object
    depth: int
    count: int


class LightEntry(NamedTuple):
    obj: object
    depth: int
    other_collections: int


def list_entries(view_layer, name_filter="", type_filter='ALL', grouped=True, show_empty=False):
    """The rows the Lights panel draws, in order: collections nested as in the outliner
    (only those on the path to a listed light), each followed by its own lights sorted by name
    ignoring case, then its sub-collections. A collapsed collection keeps its header and count but
    nothing below it. A collection with both its own lights and sub-collections puts its lights under a
    foldable LightsEntry row; folding it drops only those lights. A SceneEntry header comes first,
    then the Scene Collection's own lights (unless its lights are folded) at depth 0, so top-level
    collections stay at depth 0.
    With show_empty, every non-excluded collection is listed, those without listed lights with count 0.
    When not grouped, or while searching, it is the flat listed_lights() order with no headers."""
    if not grouped or name_filter:
        return [LightEntry(obj, 0, 0) for obj in listed_lights(view_layer, name_filter, type_filter)]
    listed = set(listed_lights(view_layer, type_filter=type_filter))
    scene_collection = view_layer.layer_collection.collection
    entries = _collection_entries(view_layer.layer_collection, listed, 0, show_empty)[0]
    own = [entry for entry in entries if isinstance(entry, LightEntry) and entry.depth == 0]
    if is_lights_folded(scene_collection):
        entries = entries[len(own):]
    entries = [SceneEntry(scene_collection, len(own))] + entries
    places = Counter(entry.obj for entry in entries if isinstance(entry, LightEntry))
    return [
        entry._replace(other_collections=places[entry.obj] - 1) if isinstance(entry, LightEntry) else entry
        for entry in entries
    ]


def group_lights(view_layer, collection, type_filter='ALL'):
    """The listed lights in a collection and its sub-collections, each once, in list order.
    The same lights its header counts."""
    layer_collection = find_layer_collection(view_layer.layer_collection, collection)
    if layer_collection is None:
        return []
    listed = set(listed_lights(view_layer, type_filter=type_filter))
    return list(_collection_entries(layer_collection, listed, 0)[1])


def listed_groups(view_layer, type_filter='ALL', show_empty=False, foldable_only=False):
    """Every collection holding a listed light, directly or in a sub-collection, in list order
    (every non-excluded collection with show_empty). foldable_only leaves out those with nothing
    listed under them. Collapse state is ignored, so a collapsed parent does not hide its sub-collections."""
    listed = set(listed_lights(view_layer, type_filter=type_filter))
    groups = []

    def walk(layer_collection):
        for child in layer_collection.children:
            if child.exclude:
                continue
            if show_empty or listed.intersection(child.collection.all_objects):
                foldable = (listed.intersection(child.collection.objects)
                            or any(not grandchild.exclude for grandchild in child.children) if show_empty else True)
                if foldable or not foldable_only:
                    groups.append(child.collection)
                walk(child)

    walk(view_layer.layer_collection)
    return groups


def find_layer_collection(layer_collection, collection):
    """The non-excluded layer collection of the collection below this one, or None."""
    for child in layer_collection.children:
        if child.exclude:
            continue
        if child.collection == collection:
            return child
        found = find_layer_collection(child, collection)
        if found is not None:
            return found
    return None


def _collection_entries(layer_collection, listed, depth, show_empty=False):
    """The entries inside a layer collection, at the given depth, and the listed lights they hold
    (a dict used as an ordered set, in list order)."""
    own = sorted((obj for obj in layer_collection.collection.objects if obj in listed),
                 key=lambda obj: obj.name.casefold())
    lights = dict.fromkeys(own)
    groups = []
    for child in layer_collection.children:
        if child.exclude:
            continue
        child_entries, child_lights = _collection_entries(child, listed, depth + 1, show_empty)
        if child_lights or show_empty:
            groups.append(GroupEntry(child.collection, depth, len(child_lights), bool(child_entries)))
            if not is_collapsed(child.collection):
                groups += child_entries
            lights |= child_lights
    # Depth 0 is the Scene Collection (or group_lights()' own collection): its lights get no row.
    if own and groups and depth > 0:
        collection = layer_collection.collection
        entries = [LightsEntry(collection, depth, len(own))]
        if not is_lights_folded(collection):
            entries += [LightEntry(obj, depth + 1, 0) for obj in own]
    else:
        entries = [LightEntry(obj, depth, 0) for obj in own]
    return entries + groups, lights


def is_collapsed(collection):
    """True when the collection is collapsed in the list. False while the add-on's property is
    unregistered."""
    return getattr(collection, "lighthouse_collapsed", False)


def is_lights_folded(collection):
    """True when the collection's lights row is folded. False while the add-on's property is
    unregistered."""
    return getattr(collection, "lighthouse_lights_collapsed", False)


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


def light_scope(view_layer, obj):
    """The lights a right-click entry acts on, as in the Outliner: every selected light when the
    clicked light is selected, otherwise only the clicked light."""
    if not obj.select_get(view_layer=view_layer):
        return [obj]
    return [other for other in view_layer.objects if other.type == 'LIGHT' and other.select_get(view_layer=view_layer)]


def scope_label(verb, count):
    """A right-click entry's text: "Delete" for one light, "Delete 3 Lights" for more."""
    return verb if count == 1 else f"{verb} {count} Lights"


def delete_lights(objects):
    """Remove the objects, skipping read-only ones. Light data left with no users is purged by
    Blender, as with the Outliner's Delete. Returns how many were deleted and how many skipped."""
    import bpy
    deletable = [obj for obj in objects if not is_read_only(obj)]
    for obj in deletable:
        bpy.data.objects.remove(obj)
    return len(deletable), len(objects) - len(deletable)


def duplicate_lights(objects, linked, solo):
    """Copy each editable object into the same collections as its original, with its own copy of
    the light data, or sharing it when linked. During solo the copies are shown.
    Returns {original: copy} and how many were skipped as read-only."""
    copies = {}
    for obj in objects:
        if is_read_only(obj):
            continue
        copy = obj.copy()
        if not linked:
            copy.data = obj.data.copy()
        for collection in obj.users_collection:
            collection.objects.link(copy)
        if solo.active:
            copy.hide_viewport = copy.hide_render = False
        copies[obj] = copy
    return copies, len(objects) - len(copies)


def scope_summary(verb, done, skipped):
    """Status bar message after a bulk light action, e.g. "Deleted 2 lights, skipped 1 read-only"."""
    message = f"{verb} {done} light{'' if done == 1 else 's'}"
    return message + (f", skipped {skipped} read-only" if skipped else "")


def row_state(obj, view_layer, scene=None):
    """How a light's row is drawn: dimmed when hidden in the render or not visible in the view layer
    (its own flags, or a hidden or excluded collection); read-only when its light data comes from a
    library or a non-editable (system) override; muted when its own flags hide it in both the viewport and the render; soloed when it is the
    scene's soloed light."""
    light = obj.data
    return RowState(
        dimmed=obj.hide_render or not obj.visible_get(view_layer=view_layer),
        read_only=is_read_only(light),
        muted=obj.hide_render and obj.hide_viewport,
        soloed=scene is not None and is_solo_target(scene.lighthouse_solo, obj),
    )


def group_soloed(scene, collection):
    """True when the collection is the scene's soloed group (its header's solo icon is pressed)."""
    return is_solo_target(scene.lighthouse_solo, collection)


def is_solo_target(solo, id):
    """True while solo is on and the light object or collection is one of its targets."""
    return solo.active and any(id in (target.object, target.collection) for target in solo.targets)


def solo_target_ids(solo):
    """The soloed lights and collections still around, in the order they were soloed."""
    return [id for id in (target.object or target.collection for target in solo.targets) if id is not None]


def set_solo_targets(solo, ids):
    """Make the light objects and collections solo's targets, replacing the list."""
    solo.targets.clear()
    for id in ids:
        target = solo.targets.add()
        if id.id_type == 'OBJECT':
            target.object = id
        else:
            target.collection = id


def set_solo_target(solo, id):
    """Make the light object or collection solo's only target."""
    set_solo_targets(solo, [id])


def toggle_solo(solo, view_layer, id, extend=False):
    """Solo a light (object) or group (collection).
    Plain: solo only it, or end solo if it is the only target.
    Extend (Shift+click): add it to the targets, or remove it if soloed; removing the last ends solo.
    A light shows itself and unhides the collections holding it with their ancestors; a group shows
    every light in it and its sub-collections and unhides them with its ancestors. With several
    targets, both are the union. Leaves a World solo (the World stays exclusive)."""
    current = solo_target_ids(solo) if solo.active and not solo.world_soloed else []
    if not extend:
        if current == [id]:
            unsolo(solo)
            return
        ids = [id]
    elif id in current:
        ids = [other for other in current if other != id]
        if not ids:
            unsolo(solo)
            return
    else:
        ids = current + [id]
    _leave_world_solo(solo)
    shown, inside = set(), set()
    for target in ids:
        if target.id_type == 'OBJECT':
            shown.add(target)
            inside.update(target.users_collection)
        else:
            shown.update(target.all_objects)
            inside.update((target, *target.children_recursive))
    _solo(solo, view_layer, shown, _collection_paths(view_layer, lambda c: c in inside))
    set_solo_targets(solo, ids)


def toggle_solo_light(solo, view_layer, obj, extend=False):
    """Solo a light, or add it to / remove it from the solo with extend (see toggle_solo)."""
    toggle_solo(solo, view_layer, obj, extend)


def toggle_solo_group(solo, view_layer, collection, extend=False):
    """Solo a group, or add it to / remove it from the solo with extend (see toggle_solo)."""
    toggle_solo(solo, view_layer, collection, extend)


def toggle_solo_world(solo, view_layer, scene):
    """Solo the World: hide every light and un-mute the World's node, snapshotting its mute.
    A scene with no world, or no node to mute, only hides the lights. Pressing it again while
    the World is soloed restores the snapshot (see unsolo)."""
    if solo.active and solo.world_soloed:
        unsolo(solo)
        return
    _solo(solo, view_layer, [], [])
    solo.world_soloed = True
    node = world_mute_node(world_setup(scene))
    if node is not None:
        solo.world, solo.world_node, solo.world_muted = scene.world, node.name, node.mute
        solo.world_saved = True
        node.mute = False


def _world_snapshot_node(solo):
    """The node the World snapshot points at, or None when there is no snapshot or it is gone."""
    if not solo.world_saved or solo.world is None or solo.world.node_tree is None:
        return None
    return solo.world.node_tree.nodes.get(solo.world_node)


def _restore_world(solo):
    node = _world_snapshot_node(solo)
    if node is not None:
        node.mute = solo.world_muted
    solo.world = None
    solo.world_node = ""
    solo.world_saved = solo.world_soloed = False


def _leave_world_solo(solo):
    """Switching from World solo to a lamp or group: put the World's mute back right away."""
    if solo.world_soloed:
        _restore_world(solo)


def _solo(solo, view_layer, shown, collections):
    """Show the given lights, hide every other light and unhide the given collections.
    The first solo snapshots every light's flags; a collection's flags are snapshotted the
    first time solo unhides it. Switching target keeps the snapshot and only adds new items.
    Lights muted during the solo stay hidden (see update_snapshot)."""
    if not solo.active:
        solo.objects.clear()
        solo.collections.clear()
        solo.active = True
    solo.targets.clear()
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
    muted = {item.object for item in solo.objects if item.muted}
    for obj in lights:
        obj.hide_render = obj.hide_viewport = obj not in shown or obj in muted


def unsolo(solo):
    """Restore every snapshotted light and collection still around, then clear the snapshot."""
    for item in solo.objects:
        if item.object is not None:
            item.object.hide_render, item.object.hide_viewport = item.hide_render, item.hide_viewport
    for item in solo.collections:
        if item.collection is not None:
            item.collection.hide_render, item.collection.hide_viewport = item.hide_render, item.hide_viewport
    _restore_world(solo)
    solo.objects.clear()
    solo.collections.clear()
    solo.targets.clear()
    solo.active = False


def update_snapshot(solo, id, hide):
    """While solo is on, record `hide` as the flags un-solo restores for a light or collection
    that has a snapshot item, so a choice made during solo survives it. Others are left alone.
    A light's item also remembers it was muted during solo, so target changes keep it hidden.
    For the World's mute node, `hide` is its new mute (only recorded during a World solo)."""
    if not solo.active:
        return
    if solo.world_saved and id is not None and id == _world_snapshot_node(solo):
        solo.world_muted = hide
        return
    for item in solo.objects:
        if item.object == id:
            item.hide_render = item.hide_viewport = item.muted = hide
    for item in solo.collections:
        if item.collection == id:
            item.hide_render = item.hide_viewport = hide


def solo_label(solo):
    """The soloed lights' and collections' names (at most SHARED_NAMES, then "…"), "World" for a
    World solo, or "deleted" when every target is gone."""
    if solo.world_soloed:
        return "World"
    names = [id.name for id in solo_target_ids(solo)]
    if not names:
        return "deleted"
    return ", ".join(names[:SHARED_NAMES]) + (", …" if len(names) > SHARED_NAMES else "")


def reveal(view_layer, obj):
    """Expand every non-excluded collection holding obj directly, with its ancestors, and
    unfold those collections' lights rows (the Scene Collection's fold for its own lights)."""
    holders = set(obj.users_collection)
    for collection in _collection_paths(view_layer, lambda c: c in holders):
        collection.lighthouse_collapsed = False
        if collection in holders:
            collection.lighthouse_lights_collapsed = False
    master = view_layer.layer_collection.collection
    if master in holders:
        master.lighthouse_lights_collapsed = False


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


def new_light_mode(scene_value, default):
    """The mode new lights start in, 'COLOR' or 'KELVIN'. A scene value of 'FOLLOW' uses the default."""
    return default if scene_value == 'FOLLOW' else scene_value


def toggled_mode(scene_value, default):
    """The scene value after one flip of the mode. It is 'FOLLOW' when the flip lands on the default,
    so a file only stores a mode that differs from it."""
    mode = 'COLOR' if new_light_mode(scene_value, default) == 'KELVIN' else 'KELVIN'
    return 'FOLLOW' if mode == default else mode


def supports_temperature():
    """Whether lights have a color temperature (Blender 5.0+)."""
    import bpy
    return "use_temperature" in bpy.types.Light.bl_rna.properties


class WorldSetup(NamedTuple):
    state: str  # 'NONE' (no world), 'CUSTOM' or 'SIMPLE'
    source: object  # the node linked to the active World Output's Surface, or None
    background: object  # source, when it is a Background node whose Strength isn't linked
    environment: object  # the Environment Texture linked to the Background's Color, or None
    mapping: object = None  # the Mapping node linked to the environment's Vector, or None
    rotation: str = None  # 'MAPPING', 'ADDABLE' (Vector unlinked), 'CUSTOM' or None (no environment)


def _linked_node(socket):
    return socket.links[0].from_node if socket.is_linked else None


def world_setup(scene):
    """How the scene's world is built. SIMPLE when World Output > Surface reaches a Background node
    directly and its Strength is a plain value (a linked Strength would make the slider do nothing)."""
    world = scene.world
    if world is None:
        return WorldSetup('NONE', None, None, None)
    tree = world.node_tree if world.use_nodes else None
    output = tree.get_output_node('ALL') if tree else None
    source = _linked_node(output.inputs["Surface"]) if output else None
    if source is None or source.bl_idname != 'ShaderNodeBackground' or source.inputs["Strength"].is_linked:
        return WorldSetup('CUSTOM', source, None, None)
    environment = _linked_node(source.inputs["Color"])
    if environment is not None and environment.bl_idname != 'ShaderNodeTexEnvironment':
        environment = None
    if environment is None:
        return WorldSetup('SIMPLE', source, source, None)
    vector = _linked_node(environment.inputs["Vector"])
    if vector is None:
        return WorldSetup('SIMPLE', source, source, environment, None, 'ADDABLE')
    if vector.bl_idname == 'ShaderNodeMapping':
        return WorldSetup('SIMPLE', source, source, environment, vector, 'MAPPING')
    return WorldSetup('SIMPLE', source, source, environment, None, 'CUSTOM')


def environment_textures(world):
    """The Environment Texture nodes in the world's node tree (not inside node groups)."""
    tree = world.node_tree if world is not None and world.use_nodes else None
    return [node for node in tree.nodes if node.bl_idname == 'ShaderNodeTexEnvironment'] if tree else []


def hdri_target(world):
    """The Environment Texture Load HDRI swaps the image of: the world's only one, or None when it
    has none or several (Load HDRI never guesses, and never adds nodes here)."""
    textures = environment_textures(world)
    return textures[0] if len(textures) == 1 else None

def add_world_rotation(node_tree, environment):
    """Texture Coordinate (Generated) > Mapping > the environment's Vector, placed left of the texture.
    Returns the Mapping node."""
    coords = node_tree.nodes.new('ShaderNodeTexCoord')
    mapping = node_tree.nodes.new('ShaderNodeMapping')
    x, y = environment.location
    mapping.location = (x - 200, y)
    coords.location = (x - 400, y)
    node_tree.links.new(coords.outputs["Generated"], mapping.inputs["Vector"])
    node_tree.links.new(mapping.outputs["Vector"], environment.inputs["Vector"])
    return mapping


def world_mute_node(setup):
    """The node World mute acts on: the Background of a SIMPLE setup, else None.
    Muting a Mix Shader passes its first shader through instead of turning the world off
    (checked by rendering, see ARCHITECTURE.md), so CUSTOM setups can't be muted."""
    return setup.background if setup.state == 'SIMPLE' else None


def world_muted(setup):
    node = world_mute_node(setup)
    return node is not None and node.mute


class Receiver(NamedTuple):
    id: object
    kind: str  # 'OBJECT' or 'COLLECTION'
    state: str  # 'INCLUDE' or 'EXCLUDE'
    link: object  # the CollectionObject / CollectionChild whose light_linking.link_state this is


def receivers(obj):
    """The light's receiver collection: child collections first, then objects, each sorted by name
    ignoring case. Empty without a receiver collection."""
    collection = obj.light_linking.receiver_collection
    if collection is None:
        return []
    # collection_children / collection_objects take only indices, in the same order as children / objects.
    def listed(members, links, kind):
        return [Receiver(id, kind, link.light_linking.link_state, link)
                for id, link in sorted(zip(members, links), key=lambda pair: pair[0].name.lower())]
    return (listed(collection.children, collection.collection_children, 'COLLECTION')
            + listed(collection.objects, collection.collection_objects, 'OBJECT'))


def link_receivers(light_obj, ids, state):
    """Link each object or collection into the light's receiver collection (created like Blender's,
    "Light Linking for <light>", when missing) and set its link state. The light itself is skipped.
    Returns (added, updated)."""
    import bpy
    collection = light_obj.light_linking.receiver_collection
    if collection is None:
        collection = bpy.data.collections.new(f"Light Linking for {light_obj.name}")
        light_obj.light_linking.receiver_collection = collection
    added = updated = 0
    for id in ids:
        if id == light_obj:
            continue
        is_collection = isinstance(id, bpy.types.Collection)
        members, links = ((collection.children, collection.collection_children) if is_collection
                          else (collection.objects, collection.collection_objects))
        if id in members[:]:
            updated += 1
        else:
            members.link(id)
            added += 1
        links[members[:].index(id)].light_linking.link_state = state
    return added, updated


def remove_receiver(light_obj, id):
    """Unlink one object or child collection from the light's receiver collection."""
    import bpy
    collection = light_obj.light_linking.receiver_collection
    if collection is None:
        return
    members = collection.children if isinstance(id, bpy.types.Collection) else collection.objects
    if id in members[:]:
        members.unlink(id)


def clear_receivers(light_obj):
    """Unlink every object and child collection from the light's receiver collection, which stays
    assigned. Every light sharing it changes too."""
    collection = light_obj.light_linking.receiver_collection
    if collection is None:
        return
    for child in list(collection.children):
        collection.children.unlink(child)
    for member in list(collection.objects):
        collection.objects.unlink(member)


def receiver_users(collection):
    """The light objects using this collection as their receiver collection, sorted by name."""
    import bpy
    return sorted((obj for obj in bpy.data.objects
                   if obj.type == 'LIGHT' and obj.light_linking.receiver_collection == collection),
                  key=lambda obj: obj.name)


SHARED_NAMES = 3


def shared_label(obj):
    """"Shared with Key, Rim (3 lights)" when other lights use this light's receiver collection
    (at most SHARED_NAMES names, then "…"); "" otherwise."""
    collection = obj.light_linking.receiver_collection
    if collection is None:
        return ""
    users = receiver_users(collection)
    others = [user.name for user in users if user != obj]
    if not others:
        return ""
    names = ", ".join(others[:SHARED_NAMES]) + (", …" if len(others) > SHARED_NAMES else "")
    return f"Shared with {names} ({len(users)} lights)"


def _counted(objects, collections):
    """ "3 objects", "1 collection" or "2 objects and 1 collection"."""
    parts = [f"{count} {noun}{'' if count == 1 else 's'}"
             for count, noun in ((objects, "object"), (collections, "collection")) if count]
    return " and ".join(parts)


def linking_tooltip(included, excluded, included_collections=0, excluded_collections=0):
    """Tooltip for a row's light linking icon, from receivers() counts: "Lights only 3 objects, excludes 1",
    "Excludes 2 objects", … Child collections are named separately. Empty without receivers (no icon)."""
    if included or included_collections:
        summary = f"Lights only {_counted(included, included_collections)}"
        if excluded_collections:
            return f"{summary}, excludes {_counted(excluded, excluded_collections)}"
        return f"{summary}, excludes {excluded}" if excluded else summary
    if excluded or excluded_collections:
        return f"Excludes {_counted(excluded, excluded_collections)}"
    return ""


def linking_counts(obj):
    """(included objects, excluded objects, included collections, excluded collections) of receivers(obj),
    in linking_tooltip()'s argument order."""
    listed = receivers(obj)
    return tuple(sum(1 for r in listed if r.kind == kind and r.state == state)
                 for kind, state in (('OBJECT', 'INCLUDE'), ('OBJECT', 'EXCLUDE'),
                                     ('COLLECTION', 'INCLUDE'), ('COLLECTION', 'EXCLUDE')))


# Render probe (ARCHITECTURE.md, v5 task 12): EEVEE renders light linking on 5.2.2 but not on 4.2.23.
# Versions in between weren't checked, so EEVEE counts from 5.0.
EEVEE_LIGHT_LINKING = (5, 0)


ENGINE_NAMES = {"CYCLES": "Cycles", "BLENDER_EEVEE": "EEVEE", "BLENDER_EEVEE_NEXT": "EEVEE",
                "BLENDER_WORKBENCH": "Workbench"}


def engine_name(engine):
    """Display name of a render engine id: built-ins from ENGINE_NAMES (RenderSettings' engine enum
    only lists some of them headless), others from their registered RenderEngine's bl_label."""
    import bpy
    if engine in ENGINE_NAMES:
        return ENGINE_NAMES[engine]
    registered = {getattr(cls, "bl_idname", None): getattr(cls, "bl_label", None)
                  for cls in bpy.types.RenderEngine.__subclasses__()}
    return registered.get(engine) or engine


def light_linking_note(engine):
    """"Not rendered in <engine>, Cycles only" for a render engine that doesn't render light linking,
    or None for one that does. Unknown (third-party) engines get the note."""
    import bpy
    renders = ["CYCLES"]
    if bpy.app.version >= EEVEE_LIGHT_LINKING:
        renders.append("BLENDER_EEVEE")
    if engine in renders:
        return None
    name = engine_name(engine)
    supported = " and ".join(engine_name(e) for e in renders)
    return f"Not rendered in {name}, {supported} only"
