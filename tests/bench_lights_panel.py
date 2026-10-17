"""Time one draw of the Lights panel in a scene with about 500 lights, headless.

Run with `make bench` (BLENDER=/path/to/blender for another Blender). Prints the median of several
passes in ms. Not part of the pytest suite and has no budget: the number is compared by hand.
The panel draws on the suite's Recorder stub layout (blender_runner.RECORDER), so this measures
Lighthouse's own draw code, not Blender's widget layout.
"""

import sys

from blender_runner import RECORDER, blender_binary, blender_version, run_in_blender

LIGHTS = 500
PASSES = 9

BENCH = f"""
import platform, statistics, time
import lighthouse
lighthouse.register()
empty_scene()
scene = bpy.context.scene

# Nested collections: 5 top-level, each with 4 sub-collections, each of those with 2 more.
collections = []
for i in range(5):
    top = bpy.data.collections.new(f"Set {{i}}")
    scene.collection.children.link(top)
    collections.append(top)
    for j in range(4):
        sub = bpy.data.collections.new(f"Set {{i}}.{{j}}")
        top.children.link(sub)
        collections.append(sub)
        for k in range(2):
            leaf = bpy.data.collections.new(f"Set {{i}}.{{j}}.{{k}}")
            sub.children.link(leaf)
            collections.append(leaf)

types = ('POINT', 'SUN', 'SPOT', 'AREA')
lights = []
for n in range({LIGHTS}):
    obj = bpy.data.objects.new(f"Light {{n:03}}", bpy.data.lights.new(f"Light {{n:03}}", types[n % 4]))
    collections[n % len(collections)].objects.link(obj)
    lights.append(obj)
bpy.context.view_layer.update()

settings = bpy.context.window_manager.lighthouse
settings.grouped = True
from lighthouse.lights import toggle_details
for obj in lights[::100]:
    toggle_details(settings, obj, keep_others=True)

panel = bpy.types.LIGHTHOUSE_PT_lights
methods = {{name: value for name, value in vars(panel).items() if name.startswith("draw")}}

def draw_once():
    holder = type("Panel", (), {{**methods, "layout": Recorder([])}})()
    start = time.perf_counter()
    panel.draw(holder, bpy.context)
    return (time.perf_counter() - start) * 1000

draw_once()  # warm-up
times = [draw_once() for _ in range({PASSES})]
report({{"lights": len(lights), "collections": len(collections), "expanded": len(settings.expanded),
        "median_ms": statistics.median(times), "min_ms": min(times), "max_ms": max(times),
        "machine": platform.processor() or platform.machine()}})
"""


def main():
    result = run_in_blender(RECORDER + BENCH)
    version = ".".join(map(str, blender_version()))
    print(f"Lights panel draw, {result['lights']} lights in {result['collections']} collections, "
          f"{result['expanded']} rows expanded (Blender {version}, {blender_binary()})")
    print(f"median {result['median_ms']:.1f} ms over {PASSES} passes "
          f"(min {result['min_ms']:.1f}, max {result['max_ms']:.1f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
