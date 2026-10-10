# Marketplace Listing Strategy & Production Plan: Lighthouse

## 1. Executive Summary & Positioning

* **Product**: Lighthouse (Blender Lighting Management Extension)

* **Target Audience**: 3D Generalists, ArchViz Artists, and Lookdev/Cinematic Artists who handle complex, multi-light scenes and suffer from Blender's fragmented native lighting workflow.

* **Core Value Proposition**: A zero-dependency, native 3D Viewport dashboard that centralizes light inspection, filtering, bulk exposure adjustment (EV steps), collection sync, and non-destructive solo/mute management into one unified N-panel.

* **Listing Aesthetic Strategy**: **Workflow & Tool-First**. Prioritizing speed, functional proof, and UI clarity over abstract glamour renders.

## 2. Marketplace Asset Production Blueprint

### A. Hero Thumbnail (16:9 / Platform Specific)

* **Visual Concept**: Split/comparison tool-first layout.

  * **Left Side (The Friction)**: Cluttered Blender workspace with multiple open Properties tabs, deeply nested Outliner rows, and scattered light sources.

  * **Right Side (The Solution)**: Clean, high-contrast crop of the Lighthouse N-panel docked in the 3D Viewport showing grouped collections, real-time light status, and EV adjustment controls.

* **Key Visual Elements**:

  * Crisp UI callout badges: `"Dedicated N-Panel Dashboard"`, `"1-Click Solo"`, `"EV Stops"`.

  * High-contrast dark theme consistent with modern Blender releases.

  * Legible typography at small thumbnail preview scales.

### B. Product Video Trailer (Zero-Fluff Speed Run Montage)

* **Duration**: 30–45 seconds.

* **Pacing**: Ultra-rapid, cuts every 2–4 seconds, synced to a clean electronic/ambient beat. No talking head or slow introductions.

* **Timeline Breakdown**:

  * **0:00 – 0:05 (Instant Context)**: Open directly in a complex production scene (40+ lamps, interior or cinematic lookdev set). Show the Lighthouse panel scanning and displaying every active light in the view layer instantly.

  * **0:05 – 0:12 (Batch Intensity & EV Arithmetic)**: Rapid demonstration of adjusting selected lights by factor scaling and fractional EV steps (`+1`, `-1/2`, `+1/4 EV`) with direct viewport exposure changes. Quick caption: *“Non-Destructive Exposure & EV Stepping”*.

  * **0:12 – 0:20 (1-Click Solo & Mute State Machine)**: Solo key and rim lights in real time; toggle visibility across collections; turn off solo and show instantaneous recovery of the previous scene state. Caption: *“State-Preserving Solo & Mute”*.

  * **0:20 – 0:28 (Outliner Sync & Organization)**: Filter by light type (Sun, Spot, Point, Area), search by name, and move lights between collection groups directly from the N-panel.

  * **0:28 – 0:35 (Physical Presets & Inspector)**: Apply real-world presets (Candle, 60W Bulb, Daylight) and expand custom detail drawers.

  * **0:35 – 0:40 (Technical Reassurance & Outro)**: Quick demonstration of keyframe curve preservation and native undo integration (`Ctrl+Z`). Closing logo and compatibility badges (Cycles & EEVEE).

### C. Carousel Gallery Images (Micro-Feature Focus Cards)

Deliver 4 to 6 focused graphic slides tailored for skimmability:

* **Slide 1: Bulk Exposure & EV Control**

  * *Visual*: Close-up of the intensity toolbar showcasing factor sliders and EV buttons (`-1`, `-1/2`, `-1/4`, `+1/4`, `+1/2`, `+1`).

  * *Callout*: “Adjust scene lighting ratios intuitively using photographic EV stops.”

  * *Technical Proof*: Badge stating *“Keyframe Safe: Scales existing animation curves accurately.”*

* **Slide 2: Instant Solo & Mute Engine**

  * *Visual*: Viewport before/after split showing a specific fill light isolated instantly.

  * *Callout*: “Audit and lookdev isolated lights without destroying your visibility setup.”

  * *Key Feature*: Preserves and restores prior visibility states on un-solo.

* **Slide 3: Scene Organization & Outliner Sync**

  * *Visual*: Lighthouse collection view alongside Blender’s native Outliner hierarchy.

  * *Callout*: “Mirror collection hierarchies, filter by lamp type, and search large scenes instantly.”

  * *Key Feature*: Inline selection, framing, and bulk collection management.

* **Slide 4: Physical Reference Presets & Inspector**

  * *Visual*: Detail drawer open showing preset selection (Candle, 60W Bulb, Daylight) and context-aware light parameters.

  * *Callout*: “Standardize lighting values with built-in physical presets or save custom studio setups.”

* **Slide 5: Performance & Architecture (Technical Proof)**

  * *Visual*: Clean infographic showing native integration points.

  * *Callout*: “Zero dependencies. Native RNA operators. Full undo history compatibility.”

  * *Engines*: Fully compatible with Cycles and EEVEE.

## 3. Product Description Copy (Task-Oriented Benefit Blocks)

```
# Lighthouse — Lighting Command Center for Blender

Stop hunting through the Properties panel and Outliner just to balance your lights. **Lighthouse** turns your 3D Viewport N-panel into an interactive lighting dashboard, giving you instant visual control over every light in your scene.

Built purely on native Blender RNA operators with zero external dependencies, Lighthouse keeps your lighting workflow fast, non-destructive, and integrated directly into your viewport.

---

### ⚡ Balance Complex Scenes in Seconds
* **EV Stepping**: Adjust individual or selected lights in standard photographic stops (`-1`, `-1/2`, `-1/4`, `+1/4`, `+1/2`, `+1 EV`).
* **Bulk Scaling**: Scale entire collections or multi-light selections by custom multipliers.
* **Keyframe-Safe Math**: When scaling animated lights, Lighthouse automatically scales existing keyframe curves without flattening animation data.
* **Native Undo Stack**: Every adjustment operates through standard Blender operators for seamless `Ctrl+Z` recovery.

### 🎯 Isolate & Lookdev Without Friction
* **State-Preserving Solo**: Solo any light or collection to audit its direct contribution. Lighthouse remembers your prior visibility state and restores it perfectly when solo is disabled.
* **Inline Mute & Visibility**: Toggle light states without leaving the working view or opening collection menus.
* **Read-Only Awareness**: Library overrides and linked data remain protected with visual dimming and read-only flags.

### 📁 Organize Massive Production Scenes
* **Collection Sync**: Automatically mirrors your Outliner's collection structure, with an optional flat-list mode for rapid searching.
* **Instant Filtering & Search**: Find lights by name or isolate specific types (Point, Sun, Spot, Area) with one click.
* **Direct Navigation**: Select, frame in viewport (`Numpad .`), rename, or reassign light collections directly from the panel rows.

### 💡 Physical Real-World Presets
* **Studio Standards**: Quickly apply built-in reference baselines including **Candle**, **60W Bulb**, and **Daylight**.
* **Custom Preset Storage**: Save custom studio profiles directly to your Blender extension directory for cross-project reuse.
* **Smart Parameter Mapping**: Automatically maps power, color, and size to compatible light types while skipping invalid properties.

---

### 🛠 Technical Specifications & Compatibility
* **Render Engines**: Fully compatible with both **Cycles** and **EEVEE**.
* **Architecture**: 100% native Python/RNA extension (Zero external dependencies or background processes).
* **Blender Version**: Blender 4.2+ (Extension ecosystem compliant).
* **Workflow Support**: Multi-selection, range selection (`Shift`), toggle selection, and Outliner synchronization.

```

## 4. Production Checklist & Asset Deliverables

| **Deliverable** | **Format / Specs** | **Core Focus** | 
| **Hero Cover Thumbnail** | 1920x1080 (16:9), PNG | Side-by-side UI vs. scene mess; high contrast. | 
| **Trailer Video** | 1080p, 60fps, MP4 (\~30–45s) | High-speed feature montage with real-time viewport feedback. | 
| **Feature Card 1** | 1920x1080, PNG | Bulk EV stops & keyframe-safe curve scaling. | 
| **Feature Card 2** | 1920x1080, PNG | Solo/mute engine & state restoration. | 
| **Feature Card 3** | 1920x1080, PNG | Collection hierarchy & Outliner synchronization. | 
| **Feature Card 4** | 1920x1080, PNG | Physical presets & expandable inspector drawer. | 
| **Listing Copy** | Markdown formatted text | Task-oriented benefit blocks, tech specs, and feature tables. | 
