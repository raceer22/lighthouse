import bpy

from .common import preset_items, LIGHT_TYPES, SCOPE_ITEMS


class LIGHTHOUSE_PG_expanded(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)


class LIGHTHOUSE_PG_settings(bpy.types.PropertyGroup):
    name_filter: bpy.props.StringProperty(
        name="Search",
        description="Only list lights whose name contains this text",
        options={'TEXTEDIT_UPDATE'},
    )
    type_filter: bpy.props.EnumProperty(
        name="Type",
        description="Only list lights of this type",
        items=(('ALL', "All", "Every light type"),) + LIGHT_TYPES,
    )
    grouped: bpy.props.BoolProperty(
        name="Group by Collection",
        description="Nest lights under their collections, as in the outliner. The list is flat while searching",
        default=True,
    )
    show_empty: bpy.props.BoolProperty(
        name="Show Empty Collections",
        description="List collections without (matching) lights too, so you can make them active or move lights into them",
        default=True,
    )
    scale_factor: bpy.props.FloatProperty(
        name="Factor",
        description="Multiply light power by this value",
        default=1.0,
        min=0.0,
    )
    scale_scope: bpy.props.EnumProperty(name="Scope", description="Which lights to scale", items=SCOPE_ITEMS,
                                       default='SELECTED')
    preset: bpy.props.EnumProperty(name="Preset", description="Light setup to apply to selected lights", items=preset_items)
    # Lights whose details are open. Panel state: not saved, not undoable, kept on rename.
    expanded: bpy.props.CollectionProperty(type=LIGHTHOUSE_PG_expanded)


class LIGHTHOUSE_PG_solo_object(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    hide_render: bpy.props.BoolProperty()
    hide_viewport: bpy.props.BoolProperty()
    # Muted during this solo: kept hidden when the solo's targets change, even inside a target
    muted: bpy.props.BoolProperty()


class LIGHTHOUSE_PG_solo_collection(bpy.types.PropertyGroup):
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)
    hide_render: bpy.props.BoolProperty()
    hide_viewport: bpy.props.BoolProperty()


class LIGHTHOUSE_PG_solo_target(bpy.types.PropertyGroup):
    """One soloed light (object) or group (collection); the other pointer is empty."""
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)


class LIGHTHOUSE_PG_solo(bpy.types.PropertyGroup):
    """The scene's solo targets and the visibility flags to restore on un-solo."""
    active: bpy.props.BoolProperty()
    targets: bpy.props.CollectionProperty(type=LIGHTHOUSE_PG_solo_target)

    @property
    def light(self):
        """The first soloed light, or None: the read side of the 1.3 "light" pointer."""
        return next((target.object for target in self.targets if target.object), None)
    objects: bpy.props.CollectionProperty(type=LIGHTHOUSE_PG_solo_object)
    collections: bpy.props.CollectionProperty(type=LIGHTHOUSE_PG_solo_collection)
    world_soloed: bpy.props.BoolProperty()
    # The World snapshot, taken only by World solo: the node muted and its mute before solo
    world_saved: bpy.props.BoolProperty()
    world: bpy.props.PointerProperty(type=bpy.types.World)
    world_node: bpy.props.StringProperty()
    world_muted: bpy.props.BoolProperty()


classes = (
    LIGHTHOUSE_PG_expanded,
    LIGHTHOUSE_PG_settings,
    LIGHTHOUSE_PG_solo_object,
    LIGHTHOUSE_PG_solo_target,
    LIGHTHOUSE_PG_solo_collection,
    LIGHTHOUSE_PG_solo,
)
