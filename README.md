# 5U 19" rack mount for mini PCs

Holds 8 mini PCs (Lenovo Tiny / HP Mini, up to 37 × 183 × 183 mm) plus 8 keystone jacks.
Prints as two halves (241 × 198 × 221 mm) that fit a 256 mm bed.

## Print
- Files: `rack_minipc_left.stl`, `rack_minipc_right.stl` (STEP versions also included)
- Print standing as modelled, floor on the bed, no supports, with a brim
- PETG, not PLA (~10 kg load). Use 5–6 walls and 30–40 % gyroid infill
- Test-print one keystone hole first

## Assemble
- Bolt the halves together with 6 × M5×20 bolts, nuts and washers
- Use as many rack screws as possible, and support the back if your rack allows it

## Build
Edit the parameters in `rack_minipc.py`, then:

```
make          # regenerate STL + STEP files
make clean    # remove generated files
make FREECAD=/path/to/freecadcmd   # use a specific FreeCAD
```

Needs FreeCAD 1.x. By default `make` uses a `FreeCAD*.AppImage` in this folder, else `freecadcmd` from PATH.
