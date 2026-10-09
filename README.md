# Lighthouse

A Blender extension that adds a **Lights** tab to the 3D Viewport sidebar (N). It lists every light in the view layer with inline power, color, mute and solo controls. It also has bulk intensity tools (a scale factor and ±1 EV buttons, which also scale keyframes) and power/color/radius presets, built-in and your own.

- Blender 4.2 or later. Tested on 5.2.2 LTS, under Cycles and EEVEE.
- Pure Python, with no dependencies.
- License: GPL-3.0-or-later (see `lighthouse/LICENSE`).

## Install

```sh
./build.sh                # validates the manifest, then writes dist/lighthouse-<version>.zip
```

In Blender, go to Edit › Preferences › Get Extensions › ▾ › Install from Disk… and pick the zip. Or run `make install`.

## Develop

```sh
make test                 # pytest, driving headless Blender
make validate             # blender --command extension validate
make build                # same as ./build.sh
```

`tests/acceptance.md` walks every PRD acceptance criterion. `ARCHITECTURE.md` describes the components and the Blender API quirks.

## Permissions

None declared. User presets are JSON files in the extension's own user folder (`bpy.utils.extension_path_user`), which Blender manages. The extension doesn't read or write anything outside Blender's directories, and it uses no network, clipboard, camera or microphone.
