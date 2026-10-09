from blender_runner import run_in_blender


def test_clicking_a_name_selects_only_that_light_and_makes_it_active():
    state = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        key = add_light("Key")
        fill = add_light("Fill")
        cube = add_mesh("Cube")
        key.select_set(True)
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube

        bpy.ops.lighthouse.select_light(name="Fill")

        layer = bpy.context.view_layer
        report({
            "selected": sorted(o.name for o in layer.objects if o.select_get()),
            "active": layer.objects.active.name,
        })
    """)

    assert state == {"selected": ["Fill"], "active": "Fill"}


SELECTION = """
        import lighthouse
        lighthouse.register()
        empty_scene()
        key = add_light("Key")
        fill = add_light("Fill")
        cube = add_mesh("Cube")
        key.select_set(True)
        cube.select_set(True)
        bpy.context.view_layer.objects.active = cube

        def selection():
            layer = bpy.context.view_layer
            return {
                "selected": sorted(o.name for o in layer.objects if o.select_get()),
                "active": layer.objects.active.name,
            }
"""


def test_select_action_selects_only_that_light_and_makes_it_active():
    state = run_in_blender(SELECTION + """
        bpy.ops.lighthouse.select_light(name="Fill", action='SELECT')
        report(selection())
    """)

    assert state == {"selected": ["Fill"], "active": "Fill"}


def test_toggle_adds_an_unselected_light_as_active_and_removes_a_selected_one():
    states = run_in_blender(SELECTION + """
        bpy.ops.lighthouse.select_light(name="Fill", action='TOGGLE')
        added = selection()
        bpy.ops.lighthouse.select_light(name="Key", action='TOGGLE')
        report({"added": added, "removed": selection()})
    """)

    assert states["added"] == {"selected": ["Cube", "Fill", "Key"], "active": "Fill"}
    assert states["removed"]["selected"] == ["Cube", "Fill"]


def test_rename_renames_the_light_and_an_empty_name_leaves_it_unchanged():
    names = run_in_blender(SELECTION + """
        bpy.ops.lighthouse.select_light(name="Key", action='RENAME', new_name="Key Light")
        try:
            bpy.ops.lighthouse.select_light(name="Fill", action='RENAME', new_name="  ")
        except RuntimeError:
            pass
        report(sorted(o.name for o in bpy.data.objects))
    """)

    assert names == ["Cube", "Fill", "Key Light"]


def test_frame_selects_only_that_light_without_a_3d_view():
    state = run_in_blender(SELECTION + """
        bpy.ops.lighthouse.select_light(name="Fill", action='FRAME')
        report(selection())
    """)

    assert state == {"selected": ["Fill"], "active": "Fill"}


def test_changing_the_type_of_shared_light_data_changes_every_object_using_it():
    types = run_in_blender("""
        empty_scene()
        key = add_light("Key")
        twin = bpy.data.objects.new("Twin", key.data)
        bpy.context.scene.collection.objects.link(twin)
        key.data.type = 'SPOT'
        report({o.name: o.data.type for o in bpy.data.objects})
    """)

    assert types == {"Key": "SPOT", "Twin": "SPOT"}


def test_sun_power_is_in_watts_per_square_metre_and_others_in_watts():
    units = run_in_blender("""
        from lighthouse.lights import power_unit
        empty_scene()
        report({
            t: power_unit(add_light(t, t).data)
            for t in ("POINT", "SUN", "SPOT", "AREA")
        })
    """)

    assert units == {"POINT": "W", "SUN": "W/m²", "SPOT": "W", "AREA": "W"}


def test_add_light_puts_each_type_at_the_cursor_in_the_active_collection_selected_and_active():
    added = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        studio = bpy.data.collections.new("Studio")
        bpy.context.scene.collection.children.link(studio)
        lamps = bpy.data.collections.new("Lamps")
        studio.children.link(lamps)
        layer = bpy.context.view_layer
        layer.active_layer_collection = layer.layer_collection.children["Studio"].children["Lamps"]
        bpy.context.scene.cursor.location = (1, 2, 3)
        add_mesh("Cube").select_set(True)

        added = {}
        for light_type in ("POINT", "SUN", "SPOT", "AREA"):
            bpy.ops.lighthouse.add_light(type=light_type)
            obj = layer.objects.active
            added[light_type] = {
                "type": obj.data.type,
                "location": list(obj.location),
                "collections": [c.name for c in obj.users_collection],
                "selected": [o.name for o in layer.objects if o.select_get()] == [obj.name],
            }
        report(added)
    """)

    assert added == {
        light_type: {"type": light_type, "location": [1.0, 2.0, 3.0], "collections": ["Lamps"], "selected": True}
        for light_type in ("POINT", "SUN", "SPOT", "AREA")
    }
