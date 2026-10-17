from blender_runner import run_in_blender

PANELS = ("LIGHTHOUSE_PT_lights", "LIGHTHOUSE_PT_world", "LIGHTHOUSE_PT_intensity", "LIGHTHOUSE_PT_presets",
          "LIGHTHOUSE_PT_active_light")


def test_every_panel_is_a_top_level_panel_in_the_lights_tab():
    panels = run_in_blender("""
        import lighthouse
        lighthouse.register()
        report({
            name: {
                "category": getattr(bpy.types, name).bl_category,
                "space": getattr(bpy.types, name).bl_space_type,
                "region": getattr(bpy.types, name).bl_region_type,
                "parent": getattr(getattr(bpy.types, name), "bl_parent_id", ""),
            }
            for name in %r
        })
    """ % (PANELS,))

    top_level = {"category": "Lights", "space": "VIEW_3D", "region": "UI", "parent": ""}
    assert panels == {name: top_level for name in PANELS}


def test_presets_panel_header_is_only_its_label():
    header = run_in_blender("""
        import lighthouse
        lighthouse.register()
        panel = bpy.types.LIGHTHOUSE_PT_presets
        report([panel.bl_label, hasattr(panel, "draw_header")])
    """)

    assert header == ["Presets", False]


def test_panels_are_ordered_active_light_world_intensity_presets_lights():
    order = run_in_blender("""
        import lighthouse
        panels = [cls for cls in lighthouse.classes if cls.__name__.startswith("LIGHTHOUSE_PT_")]
        report([cls.__name__ for cls in sorted(panels, key=lambda cls: cls.bl_order)])
    """)

    assert order == ["LIGHTHOUSE_PT_active_light", "LIGHTHOUSE_PT_world", "LIGHTHOUSE_PT_intensity",
                     "LIGHTHOUSE_PT_presets", "LIGHTHOUSE_PT_lights"]


def test_presets_starts_closed_and_intensity_open():
    options = run_in_blender("""
        import lighthouse
        report(["DEFAULT_CLOSED" in getattr(lighthouse.LIGHTHOUSE_PT_presets, "bl_options", set()),
                "DEFAULT_CLOSED" in getattr(lighthouse.LIGHTHOUSE_PT_intensity, "bl_options", set())])
    """)

    assert options == [True, False]
