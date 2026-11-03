# Pseudo-3D Curves Logic Explainer

Learning goal: understand how signed per-segment curve values, easing, and the
double accumulation of `curve -> dx -> x` produce a convincing pseudo-3D road
bend without constructing true curved 3D geometry.

The lesson is based on Jake Gordon's article:
https://jakesgordon.com/writing/javascript-racer-v2-curves/

Sections:

1. Shift projected centers instead of constructing full 3D geometry
2. Store a signed curve strength per segment
3. Ease into, hold, and ease out of each bend
4. Accumulate curve into direction (`dx`) and direction into position (`x`)
5. Project the shifted segment centers into perspective
6. Add outward player drift and parallax background motion

Render from this directory:

```bash
manim -ql curve_logic_explainer.py CurveLogicExplainer
manim -qh curve_logic_explainer.py CurveLogicExplainer
```
