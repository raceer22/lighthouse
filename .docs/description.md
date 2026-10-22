# Lighthouse

Lighthouse is a Blender extension designed to make light management fast, visual, and scene-aware. Instead of opening the Properties editor and editing one light at a time, it adds a dedicated Lights tab to the 3D Viewport sidebar so the user can inspect, filter, scale, solo, mute, and preset lights directly from the working view.

## What problem it tries to solve

Blender's default light workflow is fragmented and tedious for scenes with many lights:

- each light has to be selected and inspected in a separate editor section
- intensity, color, and visibility are spread across different controls
- adjusting many lights together is awkward and error-prone
- there is no quick way to compare a light setup to a known reference like a 60W bulb
- soloing, hiding, and managing grouping is slow when a scene contains many lamps

This becomes especially painful in interior lighting, lookdev, and cinematic setup work where lighting choices must be tuned quickly and iteratively.

## How the addon solves it

Lighthouse turns the N-panel into a lighting dashboard:

- it lists every light in the current view layer in a single place
- it supports search and type filters so the user can narrow the scene quickly
- it provides inline controls for power, color, mute, and solo states
- it supports bulk scaling of selected or all lights with factors and EV steps
- it offers reusable presets for common lighting values
- it groups lights by collection to mirror scene structure and make organization easier
- it keeps direct actions like select, rename, frame, and group management close to each light row

The result is a more direct workflow: users can manage scene lighting in context without constantly navigating the Properties editor.

## Current feature set

### Light list and navigation
- shows all lights in the current view layer
- supports search by name and filtering by light type
- groups lights by collection, with optional flat-list mode
- lists hidden lights in a dimmed state and keeps library lights read-only
- shows linked/shared lights and collection membership clearly
- click a light name to select it; additional modifiers support range selection, toggling, renaming, and framing

### Intensity controls
- scale all lights or only selected lights by a factor
- apply EV steps such as -1, -1/2, -1/4, +1/4, +1/2, +1
- supports keyframed lights by scaling their keyframes along with the value
- keeps edits in Blender's normal undo stack

### Solo and mute
- mute individual lights without hiding them from the render layer settings
- solo single lights or groups while preserving previous visibility state
- restore prior visibility when solo is turned off
- group-level hide and solo options are available in the collection headers

### Presets
- includes built-in presets such as Candle, 60W Bulb, and Daylight
- lets users save custom presets in Blender's extension user folder
- applies presets to compatible lights and skips incompatible ones
- stores typical lighting values like power, color, and radius/size settings

### Group and collection workflow
- lights can be grouped by collection in the panel
- each collection header can select, hide, solo, and move selected lights into the group
- the panel reflects the visibility of the collection hierarchy in the outliner
- the add-on keeps the light list aligned with the user's current view layer and collection structure

### Details and inspector behavior
- expandable detail rows show additional property controls for each light
- details are filtered so only properties relevant to the selected light type appear
- the panel is compatible with Blender's Cycles and EEVEE render engines

## Design philosophy

Lighthouse is built as a Blender extension with no external dependencies. It relies on native Blender RNA and operator patterns so that operations remain undo-friendly, work in the standard UI, and fit naturally into the application's existing workflow.

## Summary

Lighthouse is a focused lighting-management extension for Blender. It addresses the pain of editing many lights one by one by putting the entire scene's lighting state into a single, filterable, bulk-editable panel. Its central value is fast control over power, visibility, collection structure, and repeatable lighting setups without leaving the 3D viewport.
