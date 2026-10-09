"""Run a snippet inside headless Blender and return the JSON it reports."""

import json
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


def run_in_blender(snippet):
    script = PRELUDE + textwrap.dedent(snippet)
    result = subprocess.run(
        ["blender", "--background", "--factory-startup",
         "--python-exit-code", "1", "--python-expr", script],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    lines = [l for l in result.stdout.splitlines() if l.startswith(MARKER)]
    assert lines, output
    return json.loads(lines[-1][len(MARKER):])
