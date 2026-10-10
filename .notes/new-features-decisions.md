# New features: decisions

Settled while reviewing `new-features.md`. Each item gives the decision and, where it wasn't obvious, why. Items marked **Verify** depend on Blender behavior that must be checked before building on it.

## Right-click group menu

1. **Right-click on a group header** adds **New Light ▸** and **New Collection** to Blender's button context menu (`UI_MT_button_context_menu`). Lighthouse's entries go at the **top**, above Blender's own entries (Copy Python Command, Assign Shortcut, …), with a separator between them. They only appear when the button under the cursor is a Lighthouse group header.
   - Why: an add-on can't replace the right-click on a panel button, only add entries to Blender's menu. The entries go first because they're the reason to right-click there.
   - **Verify**: the menu can tell which group was clicked (`context.button_operator`).
2. **Left click is unchanged**: click makes the collection active, Ctrl+click renames it.
3. **New Light from a group's menu** adds the light into that group and **makes the group active**, as if it had been left-clicked first. **New Collection** creates the collection inside the group and makes the **new** collection active, as the header button does today.
   - Why: the active highlight should always point at where the last thing went.
4. **The Scene Collection row** gets the same menu and behaves the same: it adds to the Scene Collection and makes it active.
5. **Read-only (library) collections**: the menu items are greyed out.
6. **Header**: the separate `+ Light` and `New Collection` buttons are replaced by **one compact `+`**. It opens a menu with New Light ▸ and New Collection and adds to the active collection.
   - Why: in flat mode, while searching, or when a type filter hides everything, there are no group headers to right-click. The single `+` keeps adding possible there and still frees one slot for item 7.

## Color/Kelvin toggle

7. An **icon toggle in the header**, in the slot freed by item 6, sets whether lights created by Lighthouse start in **Color** (`use_temperature` off) or **Kelvin** (`use_temperature` on).
   - Why it's not in the New Light menu: some artists only ever use one mode, so it should be visible and stay set. A checkbox in a menu would also close the menu each time it's clicked.
8. **Persistence works on two levels**:
   - An **Add-on Preferences** default (Color or Kelvin) applies to every file.
   - A file that has never been toggled **follows the default**, including later changes to it.
   - Flipping the header toggle **pins** the file to its own value (a scene property). Flipping it back to match the default **un-pins it automatically**, so a file only stores a value while it differs from the default.
9. **It only affects Lighthouse's New Light** (the header `+` and the group right-click menu). Shift+A, the viewport Add menu, duplicates and appends are left alone.
   - Why: catching new lights with a depsgraph handler can't reliably tell a new light from a duplicated or appended one, and would quietly change lights the user copied.
10. **Kelvin mode** starts lights at **Blender's default temperature** (read from the RNA, not hardcoded) with a **white color**, so the tint doesn't skew the temperature, as presets already do. Color mode keeps Blender's default color.
    - A configurable starting temperature can come later. Presets already cover "start at 2700K".
11. On **Blender older than 5.0** (no light temperature), both the header toggle and the Preferences default are hidden.

## World panel

12. A **World sub-panel**, ordered **Lights → World → Intensity → Presets**, open by default.
    - Why right after Lights: World solo interacts with the lamps in the list.
13. **Controls**: Strength, Rotation, Mute and Solo.
14. **Detection**: follow *World Output → Surface*. If it reaches a **Background** node directly, that node's Strength is the World strength. Rotation applies to the **Environment Texture** feeding that Background's Color, if there is one.
    - Anything else (Mix Shader, node groups, …) shows *"Custom world setup, edit in Shader Editor"* and no Strength/Rotation controls.
    - No world assigned to the scene shows a short message.
    - Why: predictable, and it covers most setups. Per-Background sliders for mixed trees can come later.
15. **Rotation**:
    - Driven by the Z rotation of a **Mapping** node feeding the Environment Texture's Vector input.
    - With no Mapping node, an **Add Rotation** button inserts *Texture Coordinate (Generated) → Mapping*. After that it's a plain slider.
    - If the Vector input is already wired to something other than a Mapping node, rotation is hidden (custom coordinates).
    - Why a button: a slider that rewires the node tree when touched would be a surprise.
16. **Mute** mutes the node feeding *World Output → Surface* (`node.mute`), whatever its type, so it also works for custom setups. Strength is left untouched, and the mute shows in the Shader Editor and is saved with the file, like a muted lamp.
    - **Verify**: a muted Mix Shader or node group renders black rather than passing its first input through. If it doesn't, fall back to muting the detected Background node (simple setups only).
17. **Solo**:
    - Soloing a lamp or group **leaves the World alone**. For a full solo, mute the World yourself.
    - The **World can be soloed itself**, which darkens every lamp and un-mutes the World if it was muted. Exit Solo restores its mute.
    - Switching from World solo to a lamp or group solo restores the World's mute right away. Muting the World during World solo is kept after Exit Solo.
    - Only one thing is soloed at a time, as now, and the existing exit-solo header button ends World solo too.
    - Why: the World Mute toggle already gives a full solo in one click, and lamp solo stays predictable. "Only the HDRI" is still useful for judging the World.
    - (Changed 2026-10-10: lamp solo used to mute the World as well.)
18. **The Intensity tools (scale, EV steps) never affect the World**. It has its own Strength.

## Light linking

19. **Scope**: receiver linking only (`light_linking.receiver_collection`). No shadow linking (blocker collection) and no reverse "which lights affect this object" view for now.
20. **In a light's details**, as a section at the bottom:
    - The receiver list shows **objects and child collections**, each with an **Include/Exclude** toggle and a remove `×`.
    - **Link Selected** (Include), **Exclude Selected** and **Clear** buttons sit above the list.
    - Selected items already in the list only get their state updated, with no duplicates.
    - **Verify**: Link Selected can also pick up collections selected in the Outliner, as Blender's own operator does.
21. **Adding is selection-only**. No picker and no drag & drop for now.
22. **Sharing follows Blender's model**: actions apply to the light whose details are open. If its receiver collection is shared with other lights, the details say *"Shared with Key, Rim (3 lights)"*, so editing it there changes all of them, knowingly.
    - Why: files then behave the same as in the Properties editor.
23. **Row indicator**: a **link icon** next to ⓘ, after the name, on lights with a non-empty receiver collection. Like ⓘ, it's drawn only when needed and the name button shrinks to make room, so columns don't shift. Its tooltip summarizes the linking ("Lights only 3 objects, excludes 1"), and clicking it opens the light's details.
24. **Engines without light linking**: the section is always shown, with a note such as *"Not rendered in EEVEE, Cycles only"*. Links stay editable, because they're saved and take effect when you switch engines.
    - Why: hiding the editor while the row icon says "linked" would contradict itself.
    - **Verify**: which engines and versions render light linking (EEVEE from 4.2 onwards?).

## Delivery

25. **One v5 release**, in this order:
    1. Right-click group menu and compact header `+` (items 1–6)
    2. Color/Kelvin toggle (items 7–11). It depends on the slot freed in step 1.
    3. World panel, split into tickets: detection and Strength → Add Rotation → Mute and Solo integration
    4. Light linking, split into tickets: list and actions → row icon → engine note

## Out of scope (atm)
- Batch rename selected objects
- Duplicate object (middle mouse click)
- Menu for custom bindings (also where Shift+A following the Color/Kelvin toggle would belong)
- World: camera visibility, swapping the HDRI image, per-Background sliders for mixed setups
- Light linking: shadow linking, reverse view, picker / drag & drop for receivers
- Configurable starting temperature for new Kelvin lights
