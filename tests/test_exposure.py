from blender_runner import run_in_blender


def test_plus_one_ev_doubles_a_100_w_light():
    energy = run_in_blender("""
        import lighthouse
        lighthouse.register()
        empty_scene()
        light = add_light("A")
        light.data.energy = 100
        bpy.ops.lighthouse.step_exposure(steps=1, scope='ALL')
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
        bpy.ops.lighthouse.step_exposure(steps=-1, scope='ALL')
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
        bpy.ops.lighthouse.step_exposure(steps=1, scope='ALL')
        doubled = {obj.name: obj.data.energy for obj in lights}
        for obj in lights:
            obj.data.energy = 100
        bpy.ops.lighthouse.step_exposure(steps=-1, scope='ALL')
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
        bpy.ops.lighthouse.step_exposure(steps=1, scope='SELECTED')
        report({obj.name: obj.data.energy for obj in lights})
    """)

    assert energies == {"A": 200, "B": 100, "C": 200}
