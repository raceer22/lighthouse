from blender_runner import run_in_blender

PANELS = ("LIGHTHOUSE_PT_intensity", "LIGHTHOUSE_PT_presets", "LIGHTHOUSE_PT_lights")


def test_intensity_presets_and_lights_are_top_level_panels_in_the_lights_tab():
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
