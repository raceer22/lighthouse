import textwrap

from blender_runner import RECORDER, run_in_blender


def test_factory_world_is_simple_with_its_background_and_no_environment():
    setup = run_in_blender("""
        from lighthouse.lights import world_setup
        setup = world_setup(bpy.context.scene)
        report([setup.state, setup.background.bl_idname, setup.source == setup.background, setup.environment])
    """)

    assert setup == ["SIMPLE", "ShaderNodeBackground", True, None]


WORLD = """
        from lighthouse.lights import world_setup
        world = bpy.context.scene.world
        nodes, links = world.node_tree.nodes, world.node_tree.links
        output = world.node_tree.get_output_node('ALL')
        background = next(n for n in nodes if n.bl_idname == 'ShaderNodeBackground')
"""


def test_environment_texture_into_color_is_the_environment():
    setup = run_in_blender(WORLD + """
        env = nodes.new('ShaderNodeTexEnvironment')
        links.new(env.outputs["Color"], background.inputs["Color"])
        setup = world_setup(bpy.context.scene)
        report([setup.state, setup.environment == env])
    """)

    assert setup == ["SIMPLE", True]


def test_mix_shader_group_or_linked_strength_is_custom():
    states = run_in_blender(WORLD + """
        states = {}
        mix = nodes.new('ShaderNodeMixShader')
        links.new(mix.outputs[0], output.inputs["Surface"])
        setup = world_setup(bpy.context.scene)
        states["mix"] = [setup.state, setup.source == mix]

        group = nodes.new('ShaderNodeGroup')
        group.node_tree = bpy.data.node_groups.new("Sky", 'ShaderNodeTree')
        group.node_tree.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
        links.new(group.outputs[0], output.inputs["Surface"])
        setup = world_setup(bpy.context.scene)
        states["group"] = [setup.state, setup.source == group]

        links.new(background.outputs[0], output.inputs["Surface"])
        value = nodes.new('ShaderNodeValue')
        links.new(value.outputs[0], background.inputs["Strength"])
        setup = world_setup(bpy.context.scene)
        states["strength"] = [setup.state, setup.source == background, setup.background]
        report(states)
    """)

    assert states == {"mix": ["CUSTOM", True], "group": ["CUSTOM", True], "strength": ["CUSTOM", True, None]}


def test_nothing_linked_to_surface_is_custom_with_no_source():
    setup = run_in_blender(WORLD + """
        for link in list(output.inputs["Surface"].links):
            links.remove(link)
        setup = world_setup(bpy.context.scene)
        report([setup.state, setup.source])
    """)

    assert setup == ["CUSTOM", None]


def test_no_world_is_none():
    state = run_in_blender("""
        from lighthouse.lights import world_setup
        bpy.context.scene.world = None
        report(world_setup(bpy.context.scene).state)
    """)

    assert state == "NONE"


def drawn_world(setup_code):
    return run_in_blender(RECORDER + textwrap.dedent("""
        import lighthouse
        lighthouse.register()
    """) + textwrap.dedent(setup_code) + textwrap.dedent("""
        report(drawn(bpy.types.LIGHTHOUSE_PT_world.draw))
    """))


def test_panel_draws_strength_for_a_simple_world():
    assert drawn_world("") == [["prop", "default_value"]]


def test_panel_draws_the_custom_label_for_a_custom_world():
    log = drawn_world("""
        tree = bpy.context.scene.world.node_tree
        tree.links.new(tree.nodes.new('ShaderNodeMixShader').outputs[0], tree.get_output_node('ALL').inputs["Surface"])
    """)

    assert log == [["label", "Custom world setup, edit in Shader Editor"]]


def test_panel_draws_the_no_world_label_without_a_world():
    assert drawn_world("bpy.context.scene.world = None") == [["label", "No world in this scene"]]


def test_bulk_actions_on_all_lights_leave_the_world_strength_alone():
    result = run_in_blender("""
        import lighthouse
        lighthouse.register()
        from lighthouse.lights import world_setup
        strength = world_setup(bpy.context.scene).background.inputs["Strength"]
        strength.default_value = 2.0
        sun = add_light("Sun", 'SUN')
        scaled = bpy.ops.lighthouse.scale_lights(factor=0.5, scope='ALL')
        stepped = bpy.ops.lighthouse.step_exposure(steps=1.0, scope='ALL')
        report([strength.default_value, sorted(scaled), sorted(stepped)])
    """)

    assert result == [2.0, ["FINISHED"], ["FINISHED"]]
