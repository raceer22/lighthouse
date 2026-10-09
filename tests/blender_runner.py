"""Run a snippet inside headless Blender and return the JSON it reports."""

import json
import os
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "@@RESULT@@"

PRELUDE = f"""
import json, sys
sys.path.insert(0, {str(ROOT)!r})
import bpy

def report(value):
    print({MARKER!r} + json.dumps(value))

def empty_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    bpy.context.view_layer.update()
    return bpy.context.scene

def add_light(name, light_type="POINT"):
    data = bpy.data.lights.new(name, light_type)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    return obj

def add_mesh(name):
    obj = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    return obj
"""


INSTALLED_PRELUDE = """
bpy.ops.preferences.addon_enable(module="bl_ext.user_default.lighthouse")

def preset_items():
    \"\"\"(identifier, name, icon) of each entry the panel's preset dropdown offers.\"\"\"
    settings = bpy.context.window_manager.lighthouse
    items = type(settings).__annotations__["preset"].keywords["items"](settings, bpy.context)
    return [[item[0], item[1], item[3]] for item in items]
"""


def run_in_blender(snippet):
    return _run(snippet)[0]


def run_installed(snippet, user_dir):
    """Run a snippet with Lighthouse enabled as an installed extension
    (bl_ext.user_default.lighthouse), using user_dir as Blender's user config folder.
    Separate calls with the same user_dir behave like restarts of the same Blender install.
    Returns the reported value and the full output."""
    extensions = Path(user_dir) / "extensions" / "user_default"
    extensions.mkdir(parents=True, exist_ok=True)
    if not (extensions / "lighthouse").exists():
        (extensions / "lighthouse").symlink_to(ROOT / "lighthouse")
    env = os.environ | {"BLENDER_USER_RESOURCES": str(user_dir)}
    return _run(INSTALLED_PRELUDE + textwrap.dedent(snippet), env)


def run_in_blender_with_reports(snippet):
    """Like run_in_blender, but also return the info messages operators reported."""
    value, output = _run(snippet)
    return value, info_reports(output)


def info_reports(output):
    """The info messages operators reported in a run's output."""
    return [l[len("Info: "):] for l in output.splitlines() if l.startswith("Info: ")]


def _run(snippet, env=None):
    script = PRELUDE + textwrap.dedent(snippet)
    result = subprocess.run(
        ["blender", "--background", "--factory-startup",
         "--python-exit-code", "1", "--python-expr", script],
        capture_output=True,
        text=True,
        env=env,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    lines = [l for l in result.stdout.splitlines() if l.startswith(MARKER)]
    assert lines, output
    return json.loads(lines[-1][len(MARKER):]), output
