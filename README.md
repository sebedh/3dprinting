# 5U 19" rack mount for mini PCs

Holds 8 mini PCs (Lenovo Tiny / HP Mini, up to 37 × 183 × 183 mm) plus 8 keystone jacks.
Prints as two halves (241 × 221 × 201 mm as printed) that fit a 256 mm bed.

## Print
- Files: `rack_minipc_left.stl`, `rack_minipc_right.stl` (STEP versions also included)
- The STLs are already rotated: front face flat on the bed, no supports needed
- PETG or ASA, not PLA (~10 kg load). Use 4–5 walls and 20–25 % gyroid infill
- Turn on elephant-foot compensation (~0.15–0.2 mm), because the keystone and ear holes sit in the first layers
- Test-print one keystone hole first

## Assemble
- Put M5 nuts in the hex pockets on the right half's seam face
- Bolt the halves together with 6 × M5×14–16 screws from the left half's bay side
- Use as many rack screws as possible, and support the back if your rack allows it

## Build
Edit the parameters in `rack_minipc.py`, then:

```
make          # regenerate STL + STEP files
make clean    # remove generated files
make FREECAD=/path/to/freecadcmd   # use a specific FreeCAD
```

Needs FreeCAD 1.x. By default `make` uses a `FreeCAD*.AppImage` in this folder, else `freecadcmd` from PATH.
