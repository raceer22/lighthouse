import bpy

from .lights import supports_temperature
from .common import NEW_LIGHT_MODES
from .operators.presets import LIGHTHOUSE_OT_restore_default_presets


class LIGHTHOUSE_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    new_light_mode: bpy.props.EnumProperty(
        name="New lights start in",
        description="Whether lights added by Lighthouse start in Color or in Kelvin, "
                    "in every file whose header toggle hasn't been flipped",
        items=NEW_LIGHT_MODES[1:],
        default='COLOR',
    )

    def draw(self, context):
        if supports_temperature():
            row = self.layout.row()
            row.label(text="New lights start in")
            row.prop(self, "new_light_mode", expand=True)
        self.layout.operator(LIGHTHOUSE_OT_restore_default_presets.bl_idname, text="Restore Default Presets")
        self.layout.label(text="Brings back deleted defaults. Defaults you edited are kept.")


classes = (
    LIGHTHOUSE_AP_preferences,
)
