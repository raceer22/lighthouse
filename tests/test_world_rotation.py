import textwrap

from blender_runner import RECORDER, run_in_blender

ENV = """
        from lighthouse.lights import add_world_rotation, world_setup
        tree = bpy.context.scene.world.node_tree
        background = world_setup(bpy.context.scene).background
        env = tree.nodes.new('ShaderNodeTexEnvironment')
        tree.links.new(env.outputs["Color"], background.inputs["Color"])
"""


def test_add_rotation_turns_an_unlinked_vector_into_a_mapping():
    result = run_in_blender(ENV + """
        before = world_setup(bpy.context.scene).rotation
        count = len(tree.nodes)
        mapping = add_world_rotation(tree, env)
        new = sorted(n.bl_idname for n in tree.nodes)
        coords = next(n for n in tree.nodes if n.bl_idname == 'ShaderNodeTexCoord')
        setup = world_setup(bpy.context.scene)
        report({
            "before": before,
            "added": len(tree.nodes) - count,
            "kinds": [new.count('ShaderNodeTexCoord'), new.count('ShaderNodeMapping')],
            "coords_to_mapping": mapping.inputs["Vector"].links[0].from_socket == coords.outputs["Generated"],
            "mapping_to_env": env.inputs["Vector"].links[0].from_node == mapping,
            "left": coords.location.x < mapping.location.x < env.location.x,
            "after": [setup.rotation, setup.mapping == mapping],
        })
    """)

    assert result == {"before": "ADDABLE", "added": 2, "kinds": [1, 1], "coords_to_mapping": True,
                      "mapping_to_env": True, "left": True, "after": ["MAPPING", True]}


def test_rotation_z_changes_only_z_on_the_found_mapping():
    result = run_in_blender(ENV + """
        mapping = add_world_rotation(tree, env)
        found = world_setup(bpy.context.scene).mapping
        found.inputs["Rotation"].default_value[2] = 1.5
        report([found == mapping, [round(v, 4) for v in mapping.inputs["Rotation"].default_value]])
    """)

    assert result == [True, [0.0, 0.0, 1.5]]


def test_vector_from_texture_coordinate_is_custom_and_add_rotation_refuses():
    result = run_in_blender(ENV + """
        import lighthouse
        lighthouse.register()
        coords = tree.nodes.new('ShaderNodeTexCoord')
        tree.links.new(coords.outputs["Generated"], env.inputs["Vector"])
        count = len(tree.nodes)
        try:
            outcome = sorted(bpy.ops.lighthouse.add_world_rotation())
        except RuntimeError:
            outcome = "refused"
        report([world_setup(bpy.context.scene).rotation, outcome, len(tree.nodes) - count])
    """)

    assert result[0] == "CUSTOM" and result[1] in ("refused", ["CANCELLED"]) and result[2] == 0


def test_add_rotation_operator_adds_the_nodes_for_an_addable_world():
    result = run_in_blender(ENV + """
        import lighthouse
        lighthouse.register()
        outcome = sorted(bpy.ops.lighthouse.add_world_rotation())
        report([outcome, world_setup(bpy.context.scene).rotation])
    """)

    assert result == [["FINISHED"], "MAPPING"]


def test_background_without_environment_has_no_rotation():
    rotation = run_in_blender("""
        from lighthouse.lights import world_setup
        report(world_setup(bpy.context.scene).rotation)
    """)

    assert rotation is None


def drawn_world(setup_code):
    return run_in_blender(RECORDER + textwrap.dedent(ENV) + textwrap.dedent("""
        import lighthouse
        lighthouse.register()
    """) + textwrap.dedent(setup_code) + textwrap.dedent("""
        report(drawn(bpy.types.LIGHTHOUSE_PT_world.draw))
    """))


def test_panel_draws_the_slider_for_a_mapping():
    log = drawn_world("add_world_rotation(tree, env)")

    assert log == [["label", "World"], ["operator", "lighthouse.mute_world", ""], ["operator", "lighthouse.solo_world", ""], ["prop", "default_value"], ["prop", "default_value"]]


def test_panel_draws_add_rotation_when_addable():
    log = drawn_world("")

    assert log == [["label", "World"], ["operator", "lighthouse.mute_world", ""], ["operator", "lighthouse.solo_world", ""], ["prop", "default_value"],
                   ["operator", "lighthouse.add_world_rotation", "Add Rotation"]]


def test_panel_draws_no_rotation_for_a_custom_vector():
    log = drawn_world("""
        tree.links.new(tree.nodes.new('ShaderNodeTexCoord').outputs["Generated"], env.inputs["Vector"])
    """)

    assert log == [["label", "World"], ["operator", "lighthouse.mute_world", ""], ["operator", "lighthouse.solo_world", ""], ["prop", "default_value"]]
