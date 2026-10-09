import pytest

from blender_runner import run_in_blender


def test_plus_one_ev_doubles_a_100_w_light():
    energy = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        light = add_light("A")
        light.data.energy = 100
        bpy.ops.lighthouse.step_exposure(steps=1.0, scope='ALL')
        report(light.data.energy)
    """)

    assert energy == 200


def test_minus_one_ev_halves_a_100_w_light():
    energy = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        light = add_light("A")
        light.data.energy = 100
        bpy.ops.lighthouse.step_exposure(steps=-1.0, scope='ALL')
        report(light.data.energy)
    """)

    assert energy == 50


def test_ev_steps_work_on_every_light_type():
    energies = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        lights = [add_light(t, t) for t in ("POINT", "SPOT", "AREA", "SUN")]
        for obj in lights:
            obj.data.energy = 100
        bpy.ops.lighthouse.step_exposure(steps=1.0, scope='ALL')
        doubled = {obj.name: obj.data.energy for obj in lights}
        for obj in lights:
            obj.data.energy = 100
        bpy.ops.lighthouse.step_exposure(steps=-1.0, scope='ALL')
        report([doubled, {obj.name: obj.data.energy for obj in lights}])
    """)

    assert energies == [
        {"POINT": 200, "SPOT": 200, "AREA": 200, "SUN": 200},
        {"POINT": 50, "SPOT": 50, "AREA": 50, "SUN": 50},
    ]


def test_selected_scope_steps_only_the_selected_lights():
    energies = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        lights = [add_light(name) for name in ("A", "B", "C")]
        for obj in lights:
            obj.data.energy = 100
        lights[0].select_set(True)
        lights[2].select_set(True)
        bpy.ops.lighthouse.step_exposure(steps=1.0, scope='SELECTED')
        report({obj.name: obj.data.energy for obj in lights})
    """)

    assert energies == {"A": 200, "B": 100, "C": 200}


def test_plus_quarter_ev_raises_a_100_w_light_to_about_118_92_w():
    energy = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        light = add_light("A")
        light.data.energy = 100
        bpy.ops.lighthouse.step_exposure(steps=0.25, scope='ALL')
        report(light.data.energy)
    """)

    assert energy == pytest.approx(118.92, abs=0.01)


def test_each_ev_button_multiplies_power_by_two_to_the_steps():
    energies = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        light = add_light("A")
        energies = {}
        for steps in (-1.0, -0.5, -0.25, 0.5, 1.0):
            light.data.energy = 100
            bpy.ops.lighthouse.step_exposure(steps=steps, scope='ALL')
            energies[steps] = light.data.energy
        report(energies)
    """)

    assert energies == {
        "-1.0": pytest.approx(50),
        "-0.5": pytest.approx(70.7107, abs=1e-3),
        "-0.25": pytest.approx(84.0896, abs=1e-3),
        "0.5": pytest.approx(141.4214, abs=1e-3),
        "1.0": pytest.approx(200),
    }


def test_ev_steps_never_change_a_lights_own_exposure():
    exposure = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        light = add_light("A")
        light.data.exposure = 0.5
        bpy.ops.lighthouse.step_exposure(steps=0.25, scope='ALL')
        bpy.ops.lighthouse.step_exposure(steps=-1.0, scope='ALL')
        report(light.data.exposure)
    """)

    assert exposure == 0.5
