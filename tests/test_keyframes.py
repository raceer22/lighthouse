import pytest

from blender_runner import run_in_blender, run_in_blender_with_reports

KEYFRAMED = """
        from bpy_extras import anim_utils
        import lighthouse
        lighthouse.register()
        empty_scene()
        light = add_light("A")
        light.data.energy = 100
        light.data.keyframe_insert("energy", frame=1)
        light.data.energy = 300
        light.data.keyframe_insert("energy", frame=50)

        def fcurve(data_path, index=0):
            animation = light.data.animation_data
            bag = anim_utils.action_get_channelbag_for_slot(animation.action, animation.action_slot)
            return bag.fcurves.find(data_path, index=index)

        def keys(data_path="energy", index=0):
            return [k.co.y for k in fcurve(data_path, index).keyframe_points]
"""


def test_scaling_a_keyframed_light_scales_its_keyframes():
    keys = run_in_blender(KEYFRAMED + """
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        report(keys())
    """)

    assert keys == [50, 150]


def test_after_a_frame_change_the_animated_power_is_the_scaled_value():
    energies = run_in_blender(KEYFRAMED + """
        scene = bpy.context.scene
        scene.frame_set(1)
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        scene.frame_set(25)
        scene.frame_set(1)
        at_first = light.data.energy
        scene.frame_set(50)
        report([at_first, light.data.energy])
    """)

    assert energies == [50, 150]


def test_power_between_keyframes_scales_with_the_curve():
    energies = run_in_blender(KEYFRAMED + """
        scene = bpy.context.scene
        scene.frame_set(10)
        before = light.data.energy
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        scene.frame_set(1)
        scene.frame_set(10)
        report([before, light.data.energy])
    """)

    before, after = energies
    assert after == pytest.approx(before * 0.5)


def test_keyframes_on_other_properties_are_left_unchanged():
    keys = run_in_blender(KEYFRAMED + """
        light.data.color = (0.8, 0.6, 0.4)
        light.data.keyframe_insert("color", frame=1)
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        report([keys("color", i) for i in range(3)])
    """)

    assert keys == [[pytest.approx(0.8)], [pytest.approx(0.6)], [pytest.approx(0.4)]]


def test_ev_steps_scale_keyframes():
    keys = run_in_blender(KEYFRAMED + """
        bpy.ops.lighthouse.step_exposure(steps=1, scope='ALL')
        brighter = keys()
        bpy.ops.lighthouse.step_exposure(steps=-1, scope='ALL')
        bpy.ops.lighthouse.step_exposure(steps=-1, scope='ALL')
        report([brighter, keys()])
    """)

    assert keys == [[200, 600], [50, 150]]


def test_scaling_reports_how_many_lights_were_keyframed():
    _, reports = run_in_blender_with_reports(KEYFRAMED + """
        for name in ("B", "C", "D"):
            add_light(name)
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        bpy.ops.lighthouse.step_exposure(steps=1, scope='ALL')
        report(None)
    """)

    assert reports == [
        "Scaled 4 lights (1 keyframed, whole animation)",
        "Scaled 4 lights (1 keyframed, whole animation)",
    ]


def test_scaling_without_keyframes_reports_only_the_light_count():
    _, reports = run_in_blender_with_reports("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        add_light("A")
        bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        report(None)
    """)

    assert reports == ["Scaled 1 light"]
