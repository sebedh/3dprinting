# 19" rack, 5U, vertical mini-PC holder (HP EliteDesk G9 Mini / Lenovo Tiny).
# Run in FreeCAD: Macro > Macros..., or: FreeCAD.AppImage --console rack_minipc.py
# Axes: X = left/right (centered), Y = depth (0 = rack front face), Z = up.
#
# Printed as two halves (Bambu P2S, 256 x 256 x 256 bed), split at X = 0 through
# a central keystone bay. The halves bolt together through a double rib at the seam.
# Print orientation = as modelled (floor + panel bottom edge on the bed, Z up):
# layer lines then run along the load path from PCs -> floor -> front panel -> ears.
import os
import FreeCAD as App
import Part
from FreeCAD import Vector as V

# ---------------- parameters (mm) ----------------
# Device (use the largest one you want to fit)
device_t = 37.0        # thickness (left-right when standing). Lenovo Tiny ~37, HP Mini ~34
device_h = 183.0       # height when standing
device_d = 183.0       # depth (front to back)
foam_t = 1.5           # soft foam/felt per side, stuck onto divider walls

# Fit tolerances
height_clear = 3.0     # extra vertical room inside
depth_extra = 10.0     # extra depth behind device (cables / rear clearance)

# Rack (EIA-310, 19")
rack_units = 5
panel_w = 482.6
u_h = 44.45
panel_h = rack_units * u_h - 0.8   # 221.45
opening_w = 450.8                  # usable width between rails
hole_pitch_x = 465.1               # horizontal hole spacing
hole_d = 6.8                       # M6 clearance (also fits 10-32 / 12-24 rack screws)
hole_slot = 3.0                    # extra horizontal length of each hole (0 = round holes)
u_hole_offsets = (6.35, 22.225, 38.1)  # hole positions inside each U
# (u index, hole index) used on each side -- all 3 holes in every U = max support
hole_set = tuple((u, k) for u in range(rack_units) for k in range(3))

# Layout
slots_per_side = 4     # PCs per half (8 total)
center_w = 77.0        # keystone bay width (between the two bay walls)

# Structure (beefed up for ~8 x 1.3 kg)
plate_t = 5.0          # front plate thickness
wall = 3.0             # divider wall thickness between PCs
outer_wall = 5.0       # outermost side walls (carry load into the ears)
bay_wall = 4.0         # walls either side of the keystone bay
floor_t = 4.0
divider_h = 110.0      # wall/divider height above floor (open top; PC lifts straight out)
vent_margin = 8.0      # floor vent: margin to dividers
vent_front = 20.0      # floor vent: distance from front plate
vent_rear = 20.0       # floor vent: distance from rear edge
lip_side = 4.0         # front lip overlap per side (stops device sliding out)
lip_vert = 12.0        # front lip overlap top/bottom

# Seam joint (double rib at X = 0, bolted through)
rib_t = 5.0            # rib thickness per half
joint_bolt_d = 5.5     # M5 clearance
joint_bolt_y = (30.0, 95.0, 160.0)   # from rear face of front plate
joint_bolt_z = (25.0, 85.0)          # above top of floor

# Keystones (standard cutout 14.86 x 19.3 mm; jack clips want ~1.5-2.2 mm panel)
ks_cols_x = (-19.0, 19.0)              # column centers
ks_rows = 4
ks_pitch_z = 30.0
ks_w, ks_h = 14.9, 19.4                # cutout (vertical, latch at top)
ks_panel_t = 2.0                       # plate thinned to this around each jack
ks_recess_w, ks_recess_h = 19.0, 26.0  # rear pocket that thins the plate

export_dir = None      # None = next to this script
# --------------------------------------------------

slot_w = device_t + 2 * foam_t
half_body = outer_wall + slots_per_side * slot_w + (slots_per_side - 1) * wall + bay_wall
inner_w = 2 * half_body + center_w
inner_h = device_h + height_clear
body_h = floor_t + divider_h
envelope_h = floor_t + inner_h
depth = device_d + depth_extra

assert envelope_h <= panel_h, "body taller than panel; use more U"
assert inner_w <= opening_w - 2, "body wider than rack opening"
assert center_w / 2 > rib_t + 2, "keystone bay too narrow for joint rib"

x0 = -inner_w / 2.0
z0 = 0.0               # body flush with panel bottom -> prints without supports


def box(dx, dy, dz, x, y, z):
    return Part.makeBox(dx, dy, dz, V(x, y, z))


panel = box(panel_w, plate_t, panel_h, -panel_w / 2, 0, 0)
body = box(inner_w, depth, body_h, x0, plate_t, z0)
shape = panel.fuse(body)

# slot x positions (left half, then mirrored)
left = [x0 + outer_wall + i * (slot_w + wall) for i in range(slots_per_side)]
slots = left + [-sx - slot_w for sx in left]

win_h = inner_h - 2 * lip_vert
win_w = slot_w - 2 * lip_side
for sx in slots:
    # cavity, open at the back
    shape = shape.cut(box(slot_w, depth + 1, divider_h + 1, sx, plate_t, z0 + floor_t))
    # floor vent (airflow from below)
    shape = shape.cut(box(slot_w - 2 * vent_margin, depth - vent_front - vent_rear,
                          floor_t + 2, sx + vent_margin, plate_t + vent_front, z0 - 1))
    # front window (airflow + power button access)
    shape = shape.cut(box(win_w, plate_t + 2, win_h,
                          sx + lip_side, -1, z0 + floor_t + lip_vert))

# keystone bay: open top/back, solid floor, joint rib down the middle
shape = shape.cut(box(center_w, depth + 1, divider_h + 1, -center_w / 2, plate_t, z0 + floor_t))
rib = box(2 * rib_t, depth, divider_h, -rib_t, plate_t, z0 + floor_t)
for y in joint_bolt_y:
    for z in joint_bolt_z:
        rib = rib.cut(Part.makeCylinder(joint_bolt_d / 2, 2 * rib_t + 2,
                                        V(-rib_t - 1, plate_t + y, z0 + floor_t + z),
                                        V(1, 0, 0)))
shape = shape.fuse(rib)

# keystone cutouts
ks_z0 = panel_h / 2 - (ks_rows - 1) * ks_pitch_z / 2
for cx in ks_cols_x:
    for r in range(ks_rows):
        cz = ks_z0 + r * ks_pitch_z
        shape = shape.cut(box(ks_w, plate_t + 2, ks_h, cx - ks_w / 2, -1, cz - ks_h / 2))
        shape = shape.cut(box(ks_recess_w, plate_t - ks_panel_t + 1, ks_recess_h,
                              cx - ks_recess_w / 2, ks_panel_t, cz - ks_recess_h / 2))

# rack ear holes
for side in (-1, 1):
    for u, k in hole_set:
        z = 0.4 + u * u_h + u_hole_offsets[k]
        cx = side * hole_pitch_x / 2
        r = hole_d / 2
        # horizontal slot: absorbs seam gap / print shrinkage between the two halves
        for dx in (-hole_slot / 2, hole_slot / 2):
            shape = shape.cut(Part.makeCylinder(r, plate_t + 2, V(cx + dx, -1, z), V(0, 1, 0)))
        if hole_slot > 0:
            shape = shape.cut(box(hole_slot, plate_t + 2, hole_d, cx - hole_slot / 2, -1, z - r))

shape = shape.removeSplitter()

# split into two printable halves at X = 0
big = 1000.0
half_l = shape.common(box(big, big, big, -big, -big / 2, -big / 2)).removeSplitter()
half_r = shape.common(box(big, big, big, 0, -big / 2, -big / 2)).removeSplitter()

doc = App.ActiveDocument or App.newDocument("rack_minipc")
objs = []
for name, s in (("RackMiniPC_L", half_l), ("RackMiniPC_R", half_r)):
    o = doc.addObject("Part::Feature", name)
    o.Shape = s
    objs.append(o)
doc.recompute()

try:
    out = export_dir or os.path.dirname(os.path.realpath(__file__))
except NameError:
    out = export_dir or "/var/home/sebbe/src/3dprinting"
import Mesh
for o, tag in zip(objs, ("left", "right")):
    Mesh.export([o], os.path.join(out, "rack_minipc_%s.stl" % tag))
    o.Shape.exportStep(os.path.join(out, "rack_minipc_%s.step" % tag))
doc.saveAs(os.path.join(out, "rack_minipc.FCStd"))

for o in objs:
    bb = o.Shape.BoundBox
    print("%s: %.1f x %.1f x %.1f mm, volume %.0f cm3, solids %d"
          % (o.Name, bb.XLength, bb.YLength, bb.ZLength,
             o.Shape.Volume / 1000, len(o.Shape.Solids)))
print("slots: %d, slot width: %.1f, body: %.1f x %.1f x %.1f, keystones: %d"
      % (len(slots), slot_w, inner_w, depth, body_h, len(ks_cols_x) * ks_rows))
