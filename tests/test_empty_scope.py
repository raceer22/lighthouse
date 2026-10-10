from blender_runner import reports, run_in_blender_with_reports, run_installed

SCENE = """
        import lighthouse
        lighthouse.register()
        empty_scene()
        add_light("A").data.energy = 100
"""


def test_scaling_with_nothing_selected_is_cancelled_with_a_warning():
    result, warnings = run_in_blender_with_reports(SCENE + """
        report(sorted(bpy.ops.lighthouse.scale_lights(factor=0.5, scope='SELECTED')))
    """, level="Warning")

    assert result == ["CANCELLED"]
    assert warnings == ["No lights selected"]


def test_scaling_all_in_an_empty_view_layer_warns_there_are_no_lights():
    result, warnings = run_in_blender_with_reports("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        report(sorted(bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')))
    """, level="Warning")

    assert result == ["CANCELLED"]
    assert warnings == ["No lights in the view layer"]


def test_exposure_step_with_nothing_selected_is_cancelled_with_a_warning():
    result, warnings = run_in_blender_with_reports(SCENE + """
        report(sorted(bpy.ops.lighthouse.step_exposure(steps=1.0, scope='SELECTED')))
    """, level="Warning")

    assert result == ["CANCELLED"]
    assert warnings == ["No lights selected"]


def test_applying_a_preset_with_nothing_selected_is_cancelled_with_a_warning(tmp_path):
    result, output = run_installed("""
        empty_scene()
        add_light("A")
        report(sorted(bpy.ops.lighthouse.apply_preset(preset='USER:Candle')))
    """, tmp_path)

    assert result == ["CANCELLED"]
    assert reports(output, "Warning") == ["No lights selected"]


def test_applying_a_preset_that_skips_every_selected_light_is_cancelled_with_a_warning(tmp_path):
    result, output = run_installed("""
        empty_scene()
        add_light("A").select_set(True)
        add_light("B").select_set(True)
        report(sorted(bpy.ops.lighthouse.apply_preset(preset='USER:Daylight')))
    """, tmp_path)

    assert result == ["CANCELLED"]
    assert reports(output, "Warning") == ["Applied Daylight to 0 lights (2 skipped: incompatible type)"]


def test_moving_with_nothing_selected_is_cancelled_with_a_warning():
    result, warnings = run_in_blender_with_reports(SCENE + """
        key = bpy.data.collections.new("Key")
        bpy.context.scene.collection.children.link(key)
        report(sorted(bpy.ops.lighthouse.move_to_group(name="Key")))
    """, level="Warning")

    assert result == ["CANCELLED"]
    assert warnings == ["No lights selected"]


def test_moving_only_read_only_lights_is_cancelled_with_a_warning(tmp_path):
    result, warnings = run_in_blender_with_reports(f"""
        import lighthouse
        lighthouse.register()
        empty_scene()
        library_light = add_light("Library")
        path = {str(tmp_path / "library.blend")!r}
        bpy.data.libraries.write(path, {{library_light}})
        bpy.data.objects.remove(library_light)
        with bpy.data.libraries.load(path, link=True) as (src, dst):
            dst.objects = ["Library"]
        bpy.context.scene.collection.objects.link(dst.objects[0])
        key = bpy.data.collections.new("Key")
        bpy.context.scene.collection.children.link(key)
        bpy.data.objects["Library"].select_set(True)
        report(sorted(bpy.ops.lighthouse.move_to_group(name="Key")))
    """, level="Warning")

    assert result == ["CANCELLED"]
    assert warnings == ["Moved 0 lights to Key, skipped 1 read-only"]


def test_scaling_only_read_only_lights_is_cancelled_with_a_warning(tmp_path):
    result, warnings = run_in_blender_with_reports(f"""
        import lighthouse
        lighthouse.register()
        empty_scene()
        library_light = add_light("Library")
        path = {str(tmp_path / "library.blend")!r}
        bpy.data.libraries.write(path, {{library_light}})
        bpy.data.objects.remove(library_light)
        with bpy.data.libraries.load(path, link=True) as (src, dst):
            dst.objects = ["Library"]
        bpy.context.scene.collection.objects.link(dst.objects[0])
        report(sorted(bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')))
    """, level="Warning")

    assert result == ["CANCELLED"]
    assert warnings == ["Scaled 0 lights"]


def test_scaling_by_one_is_cancelled_silently_and_leaves_power_unchanged():
    (result, energy), infos = run_in_blender_with_reports(SCENE + """
        result = sorted(bpy.ops.lighthouse.scale_lights(factor=1.0, scope='ALL'))
        report([result, bpy.data.objects["A"].data.energy])
    """)

    assert result == ["CANCELLED"]
    assert energy == 100
    assert infos == []
