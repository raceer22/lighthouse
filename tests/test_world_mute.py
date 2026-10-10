import textwrap

from blender_runner import RECORDER, run_in_blender

SETUP = """
    import lighthouse
    lighthouse.register()
    from lighthouse.lights import world_setup
    tree = bpy.context.scene.world.node_tree
    output = tree.get_output_node('ALL')
    background = world_setup(bpy.context.scene).background
"""


def run(snippet):
    return run_in_blender(textwrap.dedent(SETUP) + textwrap.dedent(snippet))


def test_mute_world_mutes_the_background_and_a_second_call_clears_it():
    result = run("""
        background.inputs["Strength"].default_value = 2.0
        first = sorted(bpy.ops.lighthouse.mute_world())
        muted = background.mute
        second = sorted(bpy.ops.lighthouse.mute_world())
        report([first, muted, second, background.mute, background.inputs["Strength"].default_value])
    """)

    assert result == [["FINISHED"], True, ["FINISHED"], False, 2.0]


def test_mute_world_cancels_for_a_mix_shader_setup_and_changes_nothing():
    result = run("""
        mix = tree.nodes.new('ShaderNodeMixShader')
        tree.links.new(mix.outputs[0], output.inputs["Surface"])
        outcome = sorted(bpy.ops.lighthouse.mute_world())
        report([outcome, [n.mute for n in tree.nodes]])
    """)

    assert result[0] == ["CANCELLED"] and not any(result[1])


def test_mute_world_cancels_without_a_world_or_a_surface_link():
    result = run("""
        for link in list(output.inputs["Surface"].links):
            tree.links.remove(link)
        unlinked = sorted(bpy.ops.lighthouse.mute_world())
        bpy.context.scene.world = None
        report([unlinked, sorted(bpy.ops.lighthouse.mute_world())])
    """)

    assert result == [["CANCELLED"], ["CANCELLED"]]


def test_mute_survives_save_and_reopen(tmp_path):
    path = str(tmp_path / "muted.blend")
    muted = run(f"""
        bpy.ops.lighthouse.mute_world()
        bpy.ops.wm.save_as_mainfile(filepath={path!r})
        bpy.ops.wm.open_mainfile(filepath={path!r})
        from lighthouse.lights import world_muted
        report(world_muted(world_setup(bpy.context.scene)))
    """)

    assert muted is True


def test_panel_draws_mute_pressed_and_strength_inactive_when_muted():
    log = run_in_blender(RECORDER + textwrap.dedent(SETUP) + textwrap.dedent("""
        background.mute = True
        report(drawn(bpy.types.LIGHTHOUSE_PT_world.draw))
    """))

    assert ["label", "World"] in log
    assert ["operator", "lighthouse.mute_world", "", "pressed"] in log
    assert ["prop", "default_value", "inactive"] in log


def test_muted_background_renders_black_but_a_muted_mix_shader_passes_through(tmp_path):
    # The verify step behind the rule: muting a Mix Shader doesn't turn the world off.
    result = run_in_blender(f"""
        scene = bpy.context.scene
        for obj in [o for o in bpy.data.objects if o.type != 'CAMERA']:
            bpy.data.objects.remove(obj)
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 1
        scene.render.resolution_x = scene.render.resolution_y = 8
        scene.render.filepath = {str(tmp_path / "probe.png")!r}
        tree = scene.world.node_tree
        output = tree.get_output_node('ALL')
        background = next(n for n in tree.nodes if n.bl_idname == 'ShaderNodeBackground')
        background.inputs["Color"].default_value = (1, 1, 1, 1)
        mix = tree.nodes.new('ShaderNodeMixShader')
        tree.links.new(background.outputs[0], mix.inputs[1])

        def brightness(node):
            tree.links.new(node.outputs[0], output.inputs["Surface"])
            node.mute = True
            bpy.ops.render.render(write_still=True)
            node.mute = False
            image = bpy.data.images.load(scene.render.filepath, check_existing=False)
            pixels = image.pixels[:]
            return max(v for i, v in enumerate(pixels) if i % 4 != 3)

        report([brightness(background) < 0.05, brightness(mix) > 0.5])
    """)

    assert result == [True, True]
