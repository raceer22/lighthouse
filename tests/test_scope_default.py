from blender_runner import run_in_blender

REGISTER = """
import lighthouse
lighthouse.register()
"""


def test_a_fresh_session_starts_with_selected_scope():
    scope = run_in_blender(REGISTER + "report(bpy.context.window_manager.lighthouse.scale_scope)")

    assert scope == "SELECTED"


def test_a_file_saved_with_scope_all_opens_with_selected(tmp_path):
    path = str(tmp_path / "scope.blend")
    run_in_blender(REGISTER + f"""
bpy.context.window_manager.lighthouse.scale_scope = 'ALL'
bpy.ops.wm.save_as_mainfile(filepath={path!r})
report(True)
""")

    scope = run_in_blender(REGISTER + f"""
bpy.ops.wm.open_mainfile(filepath={path!r})
report(bpy.context.window_manager.lighthouse.scale_scope)
""")

    assert scope == "SELECTED"
