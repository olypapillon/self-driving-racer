# Current Code Explainer

Learning goal: follow one frame of `src/3D-game.py` from track data through fixed-step state updates, camera projection, curve accumulation, and final drawing.

Sections:

1. Track data and curve values
2. Fixed-step updates to `position` and `player_x`
3. Projection of one world point
4. Projection of the visible segment list
5. `curve_offset` and `curve_velocity`
6. Far-to-near road drawing and the anchored car

Render commands, run from this directory:

```bash
manim -ql current_code_explainer.py CurrentCodeExplainer
manim -qh current_code_explainer.py CurrentCodeExplainer
```

## Relative Position Explainer

Learning goal: understand why steering changes `player_x`, why projection moves
the road in the opposite screen direction, and why `car_rect` remains fixed.

Sections:

1. Road coordinates versus camera coordinates
2. Steering updates to `player_x`
3. Conversion from `player_x` to `camera_x` and `screen_x`
4. Per-segment `curve_offset` accumulation
5. Final road-first, anchored-car rendering

```bash
manim -ql relative_position_explainer.py RelativePositionExplainer
manim -qh relative_position_explainer.py RelativePositionExplainer
```
