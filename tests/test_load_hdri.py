import textwrap

from blender_runner import RECORDER, run_in_blender

# The factory world plus an image file written by the test, so nothing depends on downloads.
WORLD = """
import os, tempfile
import lighthouse
lighthouse.register()
world = bpy.context.scene.world
nodes, links = world.node_tree.nodes, world.node_tree.links
output = world.node_tree.get_output_node('ALL')
background = next(n for n in nodes if n.bl_idname == 'ShaderNodeBackground')

def image_file(name):
    image = bpy.data.images.new(name, 4, 2, float_buffer=True)
    image.filepath_raw = os.path.join(tempfile.mkdtemp(), name + ".hdr")
    image.file_format = 'HDR'
    image.save()
    path = image.filepath_raw
    bpy.data.images.remove(image)
    return path

def environment(old="Old"):
    env = nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.new(old, 2, 1)
    return env

def load(path):
    return sorted(bpy.ops.lighthouse.load_hdri(filepath=path))

def hdri_button():
    return [e for e in drawn(lighthouse.LIGHTHOUSE_PT_world.draw) if e[1:3] == ["lighthouse.load_hdri", "Load HDRI…"]]
"""


def run(snippet):
    return run_in_blender(WORLD + RECORDER + textwrap.dedent(snippet))


def test_a_simple_setup_gets_the_image_on_its_environment_texture_without_new_nodes():
    result = run("""
        env = environment()
        links.new(env.outputs["Color"], background.inputs["Color"])
        count = len(nodes)
        path = image_file("Sky")
        outcome = load(path)
        report({"outcome": outcome, "image": bpy.path.abspath(env.image.filepath) == path,
                "nodes added": len(nodes) - count, "button": len(hdri_button())})
    """)

    assert result == {"outcome": ["FINISHED"], "image": True, "nodes added": 0, "button": 1}


def test_a_custom_setup_with_one_environment_texture_is_swapped_too():
    result = run("""
        env = environment()
        mix = nodes.new('ShaderNodeMixShader')
        links.new(env.outputs["Color"], background.inputs["Color"])
        links.new(background.outputs[0], mix.inputs[1])
        links.new(mix.outputs[0], output.inputs["Surface"])
        count = len(nodes)
        load(image_file("Sky"))
        report({"image": env.image.name, "nodes added": len(nodes) - count, "button": len(hdri_button())})
    """)

    assert result == {"image": "Sky.hdr", "nodes added": 0, "button": 1}


def test_a_custom_setup_with_none_or_two_environment_textures_gets_no_button_and_cancels():
    result = run("""
        mix = nodes.new('ShaderNodeMixShader')
        links.new(mix.outputs[0], output.inputs["Surface"])
        path = image_file("Sky")
        none = [hdri_button(), load(path)]
        environment("A"), environment("B")
        report({"none": none, "two": [hdri_button(), load(path)]})
    """)

    assert result == {"none": [[], ["CANCELLED"]], "two": [[], ["CANCELLED"]]}


def test_the_previous_image_loses_a_user_and_gets_no_fake_user():
    result = run("""
        env = environment()
        old = env.image
        users = old.users
        load(image_file("Sky"))
        report([users - old.users, old.use_fake_user])
    """)

    assert result == [1, False]


def test_a_library_world_cancels():
    result = run("""
        environment()
        library = os.path.join(tempfile.mkdtemp(), "library.blend")
        bpy.data.libraries.write(library, {world})
        with bpy.data.libraries.load(library, link=True) as (source, target):
            target.worlds = [world.name]
        bpy.context.scene.world = target.worlds[0]
        report(load(image_file("Sky")))
    """)

    assert result == ["CANCELLED"]
