"""Run a snippet inside headless Blender and return the JSON it reports."""

import functools
import json
import os
import re
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def blender_binary():
    """The Blender the tests run: $BLENDER, else blender on the PATH."""
    return os.environ.get("BLENDER", "blender")


@functools.cache
def blender_version():
    """(major, minor) of the Blender the tests run, e.g. (4, 2)."""
    output = subprocess.run([blender_binary(), "--version"], capture_output=True, text=True).stdout
    return tuple(int(n) for n in re.search(r"Blender (\d+)\.(\d+)", output).groups())


def needs_blender(major, minor, what):
    """Skip marker for a test of a property Blender added in major.minor."""
    import pytest
    return pytest.mark.skipif(blender_version() < (major, minor),
                              reason=f"{what} needs Blender {major}.{minor}+")


# Properties added after Blender 4.2, the oldest supported version, where the running one has them.
NEWER_DETAILS = (["exposure"] if blender_version() >= (4, 4) else []) + (
    ["use_temperature", "temperature"] if blender_version() >= (5, 0) else [])
MARKER = "@@RESULT@@"

PRELUDE = f"""
import json, sys
sys.path.insert(0, {str(ROOT)!r})
import bpy

# The EEVEE engine id: BLENDER_EEVEE_NEXT on Blender 4.2, BLENDER_EEVEE otherwise.
EEVEE = next(e for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT")
             if e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys())

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


def run_in_blender_with_reports(snippet, level="Info"):
    """Like run_in_blender, but also return the messages operators reported at the level."""
    value, output = _run(snippet)
    return value, reports(output, level)


def reports(output, level="Info"):
    """The messages operators reported at the level in a run's output.
    In --background Blender prints them as "Info: ..." or "Warning: ..."."""
    prefix = f"{level}: "
    return [l[len(prefix):] for l in output.splitlines() if l.startswith(prefix)]


def _run(snippet, env=None):
    script = PRELUDE + textwrap.dedent(snippet)
    result = subprocess.run(
        [blender_binary(), "--background", "--factory-startup",
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
