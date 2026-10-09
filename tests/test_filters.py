from blender_runner import run_in_blender


def test_name_search_keeps_only_lights_containing_it_ignoring_case():
    names = run_in_blender("""
        from lighthouse.lights import listed_lights
        empty_scene()
        add_light("Key")
        add_light("Monkey Rim")
        add_light("KEY_back")
        add_light("Fill")
        layer = bpy.context.view_layer
        report(sorted(o.name for o in listed_lights(layer, name_filter="key")))
    """)

    assert names == ["KEY_back", "Key", "Monkey Rim"]


def test_type_filter_keeps_only_that_type_and_combines_with_search():
    result = run_in_blender("""
        from lighthouse.lights import listed_lights
        empty_scene()
        add_light("Key Spot", "SPOT")
        add_light("Rim Spot", "SPOT")
        add_light("Key Area", "AREA")
        add_light("Sun", "SUN")
        layer = bpy.context.view_layer
        names = lambda **f: sorted(o.name for o in listed_lights(layer, **f))
        report({
            "spot": names(type_filter="SPOT"),
            "spot+key": names(type_filter="SPOT", name_filter="key"),
        })
    """)

    assert result == {
        "spot": ["Key Spot", "Rim Spot"],
        "spot+key": ["Key Spot"],
    }


def test_lights_are_listed_alphabetically_ignoring_case():
    names = run_in_blender("""
        from lighthouse.lights import listed_lights
        empty_scene()
        add_light("Zed")
        add_light("alpha")
        add_light("Beta")
        report([o.name for o in listed_lights(bpy.context.view_layer)])
    """)

    assert names == ["alpha", "Beta", "Zed"]


def test_filters_start_cleared_and_offer_all_or_one_light_type():
    settings = run_in_blender("""
        import lighthouse
        lighthouse.register()
        filters = bpy.context.window_manager.lighthouse
        type_prop = filters.bl_rna.properties["type_filter"]
        report({
            "name_filter": filters.name_filter,
            "type_filter": filters.type_filter,
            "types": [item.identifier for item in type_prop.enum_items],
        })
    """)

    assert settings == {
        "name_filter": "",
        "type_filter": "ALL",
        "types": ["ALL", "POINT", "SUN", "SPOT", "AREA"],
    }
