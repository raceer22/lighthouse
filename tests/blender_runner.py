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


# Prepend to a snippet to check draw code headless.
RECORDER = """
class Recorder:
    \"\"\"A stand-in for bpy's UILayout that records what draw() puts on it, in order.\"\"\"
    def __init__(self, log, parent=None):
        self.log, self.parent, self.enabled, self.active = log, parent, True, True
    def is_enabled(self):
        return self.enabled and (self.parent is None or self.parent.is_enabled())
    def is_active(self):
        return self.active and (self.parent is None or self.parent.is_active())
    def row(self, **kwargs):
        return Recorder(self.log, self)
    column = box = row
    def _add(self, *entry, props=None):
        self.log.append((self, list(entry), props))
        return props
    def operator(self, idname, text="", depress=False, **kwargs):
        return self._add("operator", idname, text, *(["pressed"] if depress else []),
                         props=type("Props", (), {})())
    def operator_menu_enum(self, idname, prop, text="", **kwargs):
        self._add("operator_menu_enum", idname, prop, text)
    def menu(self, idname, text="", icon="NONE", **kwargs):
        self._add("menu", idname, text, *([icon] if icon != "NONE" else []))
    def label(self, text="", **kwargs):
        self._add("label", text)
    def prop(self, data, name, **kwargs):
        self._add("prop", name)
    def separator(self, **kwargs):
        self._add("separator")
    def context_pointer_set(self, name, value):
        self._add("context_pointer_set", name, value.name)

class FakeContext:
    \"\"\"bpy.context with some members added or replaced, such as button_operator.\"\"\"
    def __init__(self, **members):
        self.__dict__.update(members)
    def __getattr__(self, name):
        return getattr(bpy.context, name)

def drawn(draw, context=None):
    \"\"\"What draw(self, context) puts on a layout: one list per call, such as ["operator", idname, text],
    followed by the operator properties draw set (if any), "disabled" if drawn on a disabled layout
    and "inactive" if drawn on an inactive one. A pressed operator (depress=True) gets "pressed" after its text.\"\"\"
    log = []
    holder = type("Holder", (), {"layout": Recorder(log)})()
    draw(holder, context or bpy.context)
    return [entry + ([vars(props)] if props is not None and vars(props) else [])
            + ([] if layout.is_enabled() else ["disabled"])
            + ([] if layout.is_active() else ["inactive"])
            for layout, entry, props in log]
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
