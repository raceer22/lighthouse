"""Headless smoke run for AC 13: every Lighthouse operator on every light type,
under Cycles and then EEVEE. Needs Lighthouse installed as bl_ext.user_default.lighthouse.

    BLENDER_USER_RESOURCES=<profile> blender -b --python-exit-code 1 --python tests/smoke_engines.py

Exits non-zero if any operator fails. Read the output for Lighthouse warnings or errors.
"""

import bpy
from bl_ext.user_default.lighthouse import lights

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj)
objs = []
for light_type in ('POINT', 'SUN', 'SPOT', 'AREA'):
    obj = bpy.data.objects.new(light_type, bpy.data.lights.new(light_type, light_type))
    bpy.context.scene.collection.objects.link(obj)
    objs.append(obj)
bpy.context.view_layer.update()
objs[0].data.keyframe_insert("energy", frame=1)

settings = bpy.context.window_manager.lighthouse


def preset_ids():
    return [item[0] for item in type(settings).__annotations__["preset"].keywords["items"](settings, bpy.context)]


for engine in ('CYCLES', 'BLENDER_EEVEE'):
    bpy.context.scene.render.engine = engine
    for obj in objs:
        for path in lights.detail_properties(obj.data, engine):
            owner, prop = lights.detail_target(obj.data, path)
            getattr(owner, prop)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]

    for scope in ('ALL', 'SELECTED'):
        assert bpy.ops.lighthouse.scale_lights(factor=0.5, scope=scope) == {'FINISHED'}
        for steps in (1, -1):
            assert bpy.ops.lighthouse.step_exposure(steps=steps, scope=scope) == {'FINISHED'}
    bpy.context.scene.frame_set(2)

    for obj in objs:
        assert bpy.ops.lighthouse.select_light(name=obj.name) == {'FINISHED'}
        for op in (bpy.ops.lighthouse.mute_light, bpy.ops.lighthouse.mute_light,
                   bpy.ops.lighthouse.solo_light, bpy.ops.lighthouse.solo_light):
            assert op(name=obj.name) == {'FINISHED'}

    for obj in objs:
        obj.select_set(True)
    for preset in preset_ids():
        assert bpy.ops.lighthouse.apply_preset(preset=preset) == {'FINISHED'}, preset
    assert bpy.ops.lighthouse.save_preset(name="Smoke " + engine) == {'FINISHED'}
    user = [p for p in preset_ids() if p.startswith("USER:")]
    assert bpy.ops.lighthouse.delete_preset(preset=user[0]) == {'FINISHED'}
    print("SMOKE ok", bpy.context.scene.render.engine)
