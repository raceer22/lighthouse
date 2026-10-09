# Task 08: Scale keyframed lights (F-curves)

**Depends on:** task-06

## Goal
Scaling and EV changes must not be overwritten by animation on the next frame change.

## Scope
- In the shared scale function, for each affected light datablock with `animation_data.action` containing an F-curve on `energy`, multiply every keyframe's `co.y`, left/right handle y values, then call `fcurve.update()`.
- Handle Blender 4.4+ slotted actions / layered action API as well as legacy actions (Blender 5.2.2 is the test target).
- Leave F-curves on other properties alone.

## Out of scope
Drivers, NLA strips, animated color.

## Done when (testable)
- Light keyframed at 100 W (frame 1) and 300 W (frame 50), scaled by 0.5: keyframes read 50 and 150 (AC 9).
- After changing the frame and returning, the animated `energy` equals the scaled value (AC 9).
- Same result when using +1 EV / -1 EV.
- Non-animated lights are unaffected, and one undo restores both values and keyframes.
