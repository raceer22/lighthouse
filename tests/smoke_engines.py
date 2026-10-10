"""Headless smoke run for AC 13 and PRD-v2 AC 21: every Lighthouse operator on every light
type, under Cycles and then EEVEE. Needs Lighthouse installed as bl_ext.user_default.lighthouse.

    BLENDER_USER_RESOURCES=<profile> blender -b --python-exit-code 1 --python tests/smoke_engines.py

Exits non-zero if any operator fails. Read the output for Lighthouse warnings or errors.
"""

import bpy
from bl_ext.user_default.lighthouse import lights

TYPES = ('POINT', 'SUN', 'SPOT', 'AREA')

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)
group = bpy.data.collections.new("Smoke Group")
bpy.context.scene.collection.children.link(group)
other = bpy.data.collections.new("Smoke Other")
bpy.context.scene.collection.children.link(other)
objs = []
for light_type in TYPES:
    obj = bpy.data.objects.new(light_type, bpy.data.lights.new(light_type, light_type))
    group.objects.link(obj)
    objs.append(obj)
bpy.context.view_layer.update()
objs[0].data.keyframe_insert("energy", frame=1)

settings = bpy.context.window_manager.lighthouse


def preset_ids():
    return [item[0] for item in type(settings).__annotations__["preset"].keywords["items"](settings, bpy.context)]


def select_all_lights():
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


# BLENDER_EEVEE_NEXT on Blender 4.2
eevee = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE'
for engine in ('CYCLES', eevee):
    bpy.context.scene.render.engine = engine

    # Rows: the details each type shows and the color slot, with temperature off and on.
    for obj in objs:
        for use_temperature in (False, True):
            if lights.has_property(obj.data, "use_temperature"):
                obj.data.use_temperature = use_temperature
            getattr(obj.data, lights.color_control(obj.data))
            for path in lights.detail_properties(obj.data, engine):
                owner, prop = lights.detail_target(obj.data, path)
                getattr(owner, prop)

    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
    for light_type in TYPES:
        assert bpy.ops.lighthouse.add_light(type=light_type) == {'FINISHED'}, light_type
        bpy.data.objects.remove(bpy.context.view_layer.objects.active)

    select_all_lights()
    for scope in ('ALL', 'SELECTED'):
        assert bpy.ops.lighthouse.scale_lights(factor=0.5, scope=scope) == {'FINISHED'}
        for steps in (1, -1, 0.5, -0.5, 0.25, -0.25):
            assert bpy.ops.lighthouse.step_exposure(steps=steps, scope=scope) == {'FINISHED'}
    bpy.context.scene.frame_set(2)

    for obj in objs:
        for action in ('SELECT', 'TOGGLE', 'TOGGLE', 'RANGE', 'FRAME'):
            assert bpy.ops.lighthouse.select_light(name=obj.name, action=action) == {'FINISHED'}, action
        name = obj.name
        assert bpy.ops.lighthouse.select_light(name=name, action='RENAME', new_name=name + " R") == {'FINISHED'}
        assert bpy.ops.lighthouse.select_light(name=name + " R", action='RENAME', new_name=name) == {'FINISHED'}
        for op in (bpy.ops.lighthouse.mute_light, bpy.ops.lighthouse.mute_light,
                   bpy.ops.lighthouse.solo_light, bpy.ops.lighthouse.solo_light):
            assert op(name=obj.name) == {'FINISHED'}
        for keep_others in (False, True, False):
            assert bpy.ops.lighthouse.toggle_details(name=obj.name, keep_others=keep_others) == {'FINISHED'}

    # Each toggle runs twice in a row, so it ends where it started.
    for op in (bpy.ops.lighthouse.toggle_group, bpy.ops.lighthouse.toggle_lights_row,
               bpy.ops.lighthouse.hide_group, bpy.ops.lighthouse.solo_group):
        for _ in range(2):
            assert op(name=group.name) == {'FINISHED'}
    assert bpy.ops.lighthouse.solo_group(name=group.name) == {'FINISHED'}
    assert bpy.ops.lighthouse.exit_solo() == {'FINISHED'}
    assert bpy.ops.lighthouse.set_active_collection(name=group.name) == {'FINISHED'}
    assert bpy.ops.lighthouse.set_active_collection(name="") == {'FINISHED'}
    old_name = group.name
    assert bpy.ops.lighthouse.set_active_collection(name=old_name, action='RENAME', new_name=old_name + " R") == {'FINISHED'}
    assert bpy.ops.lighthouse.set_active_collection(name=group.name, action='RENAME', new_name=old_name) == {'FINISHED'}
    assert bpy.ops.lighthouse.toggle_new_light_mode() == {'FINISHED'}
    assert bpy.ops.lighthouse.add_light(type='POINT') == {'FINISHED'}
    bpy.data.objects.remove(bpy.context.view_layer.objects.active)
    assert bpy.ops.lighthouse.toggle_new_light_mode() == {'FINISHED'}
    assert bpy.ops.lighthouse.new_collection() == {'FINISHED'}
    bpy.data.collections.remove(bpy.context.view_layer.active_layer_collection.collection)
    # With a target, as the right-click group menu calls them: name "" is the Scene Collection.
    for name in (group.name, ""):
        assert bpy.ops.lighthouse.add_light(type='AREA', name=name, use_active=False) == {'FINISHED'}, name
        bpy.data.objects.remove(bpy.context.view_layer.objects.active)
        assert bpy.ops.lighthouse.new_collection(name=name, use_active=False, new_name="Smoke New") == {'FINISHED'}
        bpy.data.collections.remove(bpy.context.view_layer.active_layer_collection.collection)
    assert bpy.ops.lighthouse.set_active_collection(name="") == {'FINISHED'}
    for _ in range(2):
        assert bpy.ops.lighthouse.toggle_all_groups() == {'FINISHED'}
    bpy.context.view_layer.objects.active = next(o for o in bpy.context.view_layer.objects if o.type == 'LIGHT')
    assert bpy.ops.lighthouse.reveal_active_light() == {'FINISHED'}
    assert bpy.ops.lighthouse.clear_filters() == {'FINISHED'}
    for collection in (group, other):
        collection.lighthouse_collapsed = False
    for extend in (False, True):
        assert bpy.ops.lighthouse.select_group(name=group.name, extend=extend) == {'FINISHED'}
    select_all_lights()
    assert bpy.ops.lighthouse.move_to_group(name=other.name) == {'FINISHED'}
    assert bpy.ops.lighthouse.move_to_group(name="") == {'FINISHED'}
    select_all_lights()
    assert bpy.ops.lighthouse.move_to_group(name=group.name) == {'FINISHED'}

    select_all_lights()
    for preset in preset_ids():
        assert bpy.ops.lighthouse.apply_preset(preset=preset) == {'FINISHED'}, preset
    assert bpy.ops.lighthouse.save_preset(name="Smoke " + engine) == {'FINISHED'}
    saved = "USER:Smoke " + engine
    assert saved in preset_ids()
    assert bpy.ops.lighthouse.apply_preset(preset=saved) == {'FINISHED'}
    assert bpy.ops.lighthouse.delete_preset(preset=saved) == {'FINISHED'}
    assert bpy.ops.lighthouse.restore_default_presets() == {'FINISHED'}
    world = lights.world_setup(bpy.context.scene)
    assert world.state == 'SIMPLE'
    tree = bpy.context.scene.world.node_tree
    if world.environment is None:
        env = tree.nodes.new('ShaderNodeTexEnvironment')
        tree.links.new(env.outputs["Color"], world.background.inputs["Color"])
    if lights.world_setup(bpy.context.scene).rotation == 'ADDABLE':
        assert bpy.ops.lighthouse.add_world_rotation() == {'FINISHED'}
    assert lights.world_setup(bpy.context.scene).rotation == 'MAPPING'
    print("SMOKE ok", bpy.context.scene.render.engine)
