# Lighthouse

A Blender extension that adds a **Lights** tab to the 3D Viewport sidebar (N), with three panels:

- **Intensity**: scale all or selected lights by a factor, or step them by −1, −½, −¼, +¼, +½ or +1 EV. Keyframes scale too.
- **Presets**: apply, save, overwrite or delete presets of power, color, radius, exposure and Kelvin temperature. The first run writes three defaults (Candle, 60W Bulb, Daylight) as plain files, which you can change or delete like your own. They use Kelvin on Blender 5.0+ and an RGB color on older versions. A .blend saved by an older version with a built-in preset selected opens with no preset selected.
- **Lights**: every light in the view layer, grouped by collection as in the outliner or as a flat list, with search and type filters. Each row has a details toggle, type, name, power, color (or a Kelvin field for lights using temperature), mute and solo. Click a name to select it, Shift+click to select a range, Ctrl+Shift+click to toggle it in the selection, Ctrl+click to rename and Alt+click to frame it. Group headers count their lights and can select, collapse, hide or solo the group, or move the selected lights into it. `+` adds a light (at the 3D cursor) or a collection to the active collection, and right-clicking a collection's name adds there. On Blender 5.0+, the toggle next to `+` sets whether new lights start in Color or in Kelvin for this file. The default for every file is in Edit › Preferences › Add-ons › Lighthouse ("New lights start in"). A file whose toggle was never flipped follows that default.

- Blender 4.2 or later. Tested on 4.2.23 LTS and 5.2.2 LTS, under Cycles and EEVEE. Kelvin temperature needs 5.0+ and light exposure needs 4.4+. On older versions, presets set the RGB color instead.
- Pure Python, with no dependencies.
- License: GPL-3.0-or-later (see `lighthouse/LICENSE`).

## Install

```sh
./build.sh                # validates the manifest, then writes dist/lighthouse-<version>.zip
```

In Blender, go to Edit › Preferences › Get Extensions › ▾ › Install from Disk… and pick the zip. Or run `make install`.

## Develop

Set up once:

```sh
python -m venv .venv && .venv/bin/pip install pytest
```

```sh
make test                 # pytest, driving headless Blender
make test BLENDER=/path/to/blender   # the same against another Blender binary
make validate             # blender --command extension validate
make build                # same as ./build.sh
```

`tests/acceptance.md` walks every PRD-v2 acceptance criterion, with a manual GUI checklist. `tests/smoke_engines.py` runs every operator under Cycles and EEVEE against an installed copy. `ARCHITECTURE.md` describes the components and the Blender API quirks.

## Permissions

None declared. User presets are JSON files in the extension's own user folder (`bpy.utils.extension_path_user`), which Blender manages. The extension doesn't read or write anything outside Blender's directories, and it uses no network, clipboard, camera or microphone.
