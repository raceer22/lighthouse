from blender_runner import run_in_blender


def test_lists_every_light_in_view_layer_and_nothing_else():
    names = run_in_blender("""
        from lighthouse.lights import light_objects
        empty_scene()
        add_light("Key", "AREA")
        add_light("Fill", "POINT")
        add_light("Sun", "SUN")
        add_mesh("Cube")
        report([obj.name for obj in light_objects(bpy.context.view_layer)])
    """)

    assert sorted(names) == ["Fill", "Key", "Sun"]


def test_list_follows_lights_added_and_deleted():
    snapshots = run_in_blender("""
        from lighthouse.lights import light_objects
        names = lambda: sorted(o.name for o in light_objects(bpy.context.view_layer))
        empty_scene()
        add_light("Key")
        fill = add_light("Fill")
        before = names()
        add_light("Rim")
        after_add = names()
        bpy.data.objects.remove(fill)
        bpy.context.view_layer.update()
        report([before, after_add, names()])
    """)

    assert snapshots == [
        ["Fill", "Key"],
        ["Fill", "Key", "Rim"],
        ["Key", "Rim"],
    ]
