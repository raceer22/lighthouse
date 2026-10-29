import bpy
from bpy.app.handlers import persistent

from .lights import set_solo_target


def _is_light(self, obj):
    return obj.type == 'LIGHT'

@persistent
def _track_last_light(scene, depsgraph):
    obj = bpy.context.view_layer.objects.active
    if obj is not None and obj.type == 'LIGHT' and scene.lighthouse_last_light is not obj:
        scene.lighthouse_last_light = obj

def register_last_light():
    bpy.types.Scene.lighthouse_last_light = bpy.props.PointerProperty(
        type=bpy.types.Object, poll=_is_light)
    if _track_last_light not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_track_last_light)

def unregister_last_light():
    if _track_last_light in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_track_last_light)
    del bpy.types.Scene.lighthouse_last_light


@bpy.app.handlers.persistent
def migrate_solo_targets(_):
    """Files saved mid-solo by 1.3 or older keep the soloed light or group in the "light" or "group"
    pointer that targets replaced. Their ID properties still load, so move them into targets."""
    for scene in bpy.data.scenes:
        solo = scene.lighthouse_solo
        for key in ("light", "group"):
            old = solo.get(key)
            if old is not None:
                del solo[key]
                if solo.active and not len(solo.targets):
                    set_solo_target(solo, old)
