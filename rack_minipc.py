# 19" rack, 5U, vertical mini-PC holder (HP EliteDesk G9 Mini / Lenovo Tiny).
# Run in FreeCAD: Macro > Macros..., or: FreeCAD.AppImage --console rack_minipc.py
# Axes (model): X = left/right (centered), Y = depth (0 = rack front face), Z = up.
#
# Printed as two halves (Bambu P2S, 256 x 256 x 256 bed), split at X = 0 through
# a central keystone bay. The halves bolt together through a double rib at the seam.
#
# PRINT ORIENTATION: front face of the plate flat on the bed, the body grows upward
# from it (print height = plate + depth ~ 201 mm). The STLs are exported already rotated.
#   The rack-ear holes, keystone cutouts, keystone pockets and windows are all plain
#   vertical holes (round, accurate, no overhangs), the 2 mm keystone web is printed
#   flat, the visible face is the bed side, and there is no tall free-standing plate.
#   Only the M5 seam holes (horizontal) and the floor vents need a 45-degree shape,
#   and both have one.
#
# Seam joint: ribs are 7 mm per half; the right half has hex pockets on the seam face
# so M5 nuts are captive (insert the nuts, then bolt the halves together with
# M5 x 14..16 screws from the left half's bay side).
#
# Suggested slicer settings: PETG / ASA (PLA creeps under ~10 kg), 0.2 mm layers,
# 4-5 walls, 20-25% gyroid, elephant-foot compensation ~0.15-0.2 mm (the first layers
# sit on the keystone cutouts and ear holes), textured PEI + glue stick for adhesion
# of the large flat plate. Print a small keystone/ear-hole coupon first.
#
# STRUCTURE: the weak path is the thin, windowed front plate, which has to pass the
# cantilever torque of the loaded trays sideways to the ears. Stiffeners:
#  * rim + chamfers (one piece): a flange along the top edge of the plate, bent back
#    like sheet metal, and a 45-degree chamfer on top of every wall (outer walls,
#    dividers, bay walls, seam rib) that climbs the rear face of the plate and runs
#    flush into the rear edge of the rim. Wall + chamfer + rim form one continuous web.
#    The rim only spans the body width, so it clears both the PCs and the rack rails.
#    Printed front-down the chamfers taper as they grow, so no supports.
#  * plate_t 8 mm: out-of-plane stiffness of the plate goes with thickness cubed.
#  * floor_t 16 mm: the slot floor is the bottom flange of the whole structure. The
#    panel has spare height above the PCs (none below), so the floor is thickened
#    upward: the PCs sit higher, the rack envelope (5U x 482.6) is unchanged.
#    pc_top_margin keeps the rim clear of the PC tops.
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
plate_t = 8.0          # front plate thickness. Check rack screw length.
wall = 3.0             # divider wall thickness between PCs
outer_wall = 5.0       # outermost side walls (carry load into the ears)
bay_wall = 4.0         # walls either side of the keystone bay
floor_t = 16.0         # slot floor thickness; grows upward into the spare panel height
divider_h = 110.0      # wall/divider height above floor (open top; PC lifts straight out)
vent_margin = 8.0      # floor vent: margin to dividers
vent_front = 20.0      # floor vent: distance from front plate
vent_rear = 20.0       # floor vent: distance from rear edge
vent_flat = 6.0        # floor vent: width of the flat tip at each 45-degree end
lip_side = 4.0         # front lip overlap per side (stops device sliding out)
lip_vert = 12.0        # front lip overlap top/bottom

# Rim + chamfers
rim_d = 30.0           # how far the rim reaches back from the plate
rim_t = 8.0            # rim thickness (vertical)
pc_top_margin = 10.0   # required clearance between the PC tops and the rim

# Printer
bed = 256.0            # Bambu P2S bed edge / max height

# Seam joint (double rib at X = 0, bolted through)
rib_t = 7.0            # rib thickness per half (room for the nut pocket)
joint_bolt_d = 5.5     # M5 clearance
joint_bolt_y = (30.0, 95.0, 160.0)   # from rear face of front plate
joint_bolt_z = (25.0, 85.0)          # above top of floor
nut_af = 8.0           # M5 nut across flats
nut_t = 4.0            # M5 nut thickness
nut_clear = 0.4        # clearance added to the across-flats size and the depth

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

win_h = inner_h - 2 * lip_vert
win_w = slot_w - 2 * lip_side

assert envelope_h <= panel_h, "body taller than panel; use more U"
assert inner_w <= opening_w - 2, "body wider than rack opening"
assert center_w / 2 > rib_t + 2, "keystone bay too narrow for joint rib"
assert rim_d < depth, "rim deeper than the body"
top_room = panel_h - rim_t - envelope_h
assert top_room >= pc_top_margin, \
    "only %.1f mm above the PCs (need %.1f): lower floor_t or rim_t" % (top_room, pc_top_margin)
assert (slot_w - 2 * vent_margin) - vent_flat > 0, "vent_flat wider than the vent"
assert ks_pitch_z >= ks_recess_h + 3.0, "keystone rows too close"

x0 = -inner_w / 2.0
z0 = 0.0               # body flush with panel bottom


# ---------------- helpers ----------------
def box(dx, dy, dz, x, y, z):
    return Part.makeBox(dx, dy, dz, V(x, y, z))


def prism(pts, vec):
    """Extrude the closed polygon `pts` (list of Vectors) along `vec`."""
    solid = Part.Face(Part.makePolygon(list(pts) + [pts[0]])).extrude(vec)
    if solid.Volume < 0:
        solid = solid.reversed()
    return solid


def fuse_all(parts):
    out = parts[0]
    for p in parts[1:]:
        out = out.fuse(p)
    return out


def ear_hole(cx, z):
    """Rack-screw slot through the plate (axis Y)."""
    r = hole_d / 2.0
    hs = hole_slot / 2.0
    length = plate_t + 2
    offsets = (-hs, hs) if hs > 0 else (0.0,)
    parts = [Part.makeCylinder(r, length, V(cx + dx, -1, z), V(0, 1, 0)) for dx in offsets]
    if hs > 0:
        parts.append(box(hole_slot, length, hole_d, cx - hs, -1, z - r))
    return fuse_all(parts)


def bolt_hole(y, z):
    """M5 clearance hole through the seam ribs (axis X), pointed toward +Y (print 'up')."""
    r = joint_bolt_d / 2.0
    k = r / 2 ** 0.5
    x = -rib_t - 1
    length = 2 * rib_t + 2
    tip = prism([V(x, y + k, z - k), V(x, y + k, z + k), V(x, y + 2 * k, z)],
                V(length, 0, 0))
    return Part.makeCylinder(r, length, V(x, y, z), V(1, 0, 0)).fuse(tip)


def nut_pocket(y, z):
    """Hex pocket opening onto the seam face; a flat faces print 'up' (+Y), so the
    top is only a ~5 mm bridge."""
    a = (nut_af + nut_clear) / 2.0
    R = 2.0 * a / 3 ** 0.5
    x = -1.0
    pts = [V(x, y, z + R), V(x, y + a, z + R / 2), V(x, y + a, z - R / 2),
           V(x, y, z - R), V(x, y - a, z - R / 2), V(x, y - a, z + R / 2)]
    return prism(pts, V(1.0 + nut_t + nut_clear, 0, 0))


def window(sx):
    """Front window of one slot."""
    return box(win_w, plate_t + 2, win_h, sx + lip_side, -1, z0 + floor_t + lip_vert)


def ks_recess(cx, cz):
    """Rear pocket that thins the plate around a keystone."""
    return box(ks_recess_w, plate_t + 1.0 - ks_panel_t, ks_recess_h,
               cx - ks_recess_w / 2.0, ks_panel_t, cz - ks_recess_h / 2.0)


def vent(sx):
    """Floor vent. Printed front-down the floor is a standing wall, so both ends get a
    45-degree point (no wide bridge)."""
    w = slot_w - 2 * vent_margin
    ln = depth - vent_front - vent_rear
    xl = sx + vent_margin
    ya = plate_t + vent_front
    yb = ya + ln
    f = vent_flat
    rise = (w - f) / 2.0
    xc = xl + w / 2.0
    zz = z0 - 1
    pts = [V(xl, ya + rise, zz), V(xc - f / 2, ya, zz), V(xc + f / 2, ya, zz),
           V(xl + w, ya + rise, zz), V(xl + w, yb - rise, zz), V(xc + f / 2, yb, zz),
           V(xc - f / 2, yb, zz), V(xl, yb - rise, zz)]
    return prism(pts, V(0, 0, floor_t + 2))


# ---------------- model ----------------
panel = box(panel_w, plate_t, panel_h, -panel_w / 2, 0, 0)
body = box(inner_w, depth, body_h, x0, plate_t, z0)
shape = panel.fuse(body)

# slot x positions (left edge of each cavity): left half, then mirrored right half
left = [x0 + outer_wall + i * (slot_w + wall) for i in range(slots_per_side)]
slots = left + [-sx - slot_w for sx in left]

# wall x-ranges (x start, thickness): outer wall, dividers, bay wall; then mirrored
walls_l = ([(x0, outer_wall)]
           + [(left[i] + slot_w, wall) for i in range(slots_per_side - 1)]
           + [(left[-1] + slot_w, bay_wall)])
walls = walls_l + [(-wx - ww, ww) for wx, ww in walls_l] + [(-rib_t, 2 * rib_t)]

# rim + chamfers: 45-degree chamfer from the top of each wall up the plate's rear face,
# running flush into the rear edge of the rim
z_rb = panel_h - rim_t                  # underside of the rim
y_re = plate_t + rim_d                  # rear edge of the rim
y_bot = y_re + (z_rb + 0.5) - (body_h - 0.5)   # exactly 45 degrees
assert y_bot <= plate_t + depth, "chamfer longer than the body"
for wx, ww in walls:
    pts = [V(wx, plate_t - 0.5, body_h - 0.5), V(wx, y_bot, body_h - 0.5),
           V(wx, y_re, z_rb + 0.5), V(wx, plate_t - 0.5, z_rb + 0.5)]
    shape = shape.fuse(prism(pts, V(ww, 0, 0)))
shape = shape.fuse(box(inner_w, rim_d + 0.5, rim_t, x0, plate_t - 0.5, z_rb))

for sx in slots:
    # cavity, open at the back
    shape = shape.cut(box(slot_w, depth + 1, divider_h + 1, sx, plate_t, z0 + floor_t))
    # floor vent (airflow from below)
    shape = shape.cut(vent(sx))
    # front window (airflow + power button access)
    shape = shape.cut(window(sx))

# keystone bay: open top/back, solid floor, joint rib down the middle
shape = shape.cut(box(center_w, depth + 1, divider_h + 1, -center_w / 2, plate_t, z0 + floor_t))
rib = box(2 * rib_t, depth, divider_h, -rib_t, plate_t, z0 + floor_t)
for y in joint_bolt_y:
    for z in joint_bolt_z:
        rib = rib.cut(bolt_hole(plate_t + y, z0 + floor_t + z))
shape = shape.fuse(rib)

# keystone cutouts
ks_z0 = panel_h / 2 - (ks_rows - 1) * ks_pitch_z / 2
for cx in ks_cols_x:
    for r in range(ks_rows):
        cz = ks_z0 + r * ks_pitch_z
        shape = shape.cut(box(ks_w, plate_t + 2, ks_h, cx - ks_w / 2, -1, cz - ks_h / 2))
        shape = shape.cut(ks_recess(cx, cz))

# rack ear holes (horizontal slot absorbs seam gap / print shrinkage between the halves)
for side in (-1, 1):
    for u, k in hole_set:
        z = 0.4 + u * u_h + u_hole_offsets[k]
        shape = shape.cut(ear_hole(side * hole_pitch_x / 2, z))

shape = shape.removeSplitter()

# split into two printable halves at X = 0
big = 1000.0
half_l = shape.common(box(big, big, big, -big, -big / 2, -big / 2)).removeSplitter()
half_r = shape.common(box(big, big, big, 0, -big / 2, -big / 2)).removeSplitter()

# captive-nut pockets: cut after the split so they open cleanly onto the seam face
for y in joint_bolt_y:
    for z in joint_bolt_z:
        half_r = half_r.cut(nut_pocket(plate_t + y, z0 + floor_t + z))
half_r = half_r.removeSplitter()


def to_print(s):
    """Rotate a half so the front face (Y = 0) lies on the bed, back facing up."""
    p = s.copy()
    p.rotate(V(0, 0, 0), V(1, 0, 0), 90)     # (x, y, z) -> (x, -z, y)
    p.translate(V(0, panel_h, 0))            # keep Y positive
    return p


doc = App.ActiveDocument or App.newDocument("rack_minipc")
objs = []
pobjs = []
for name, s in (("RackMiniPC_L", half_l), ("RackMiniPC_R", half_r)):
    o = doc.addObject("Part::Feature", name)
    o.Shape = s
    objs.append(o)
    po = doc.addObject("Part::Feature", name + "_print")
    po.Shape = to_print(s)
    pobjs.append(po)
doc.recompute()

for po in pobjs:
    bb = po.Shape.BoundBox
    assert max(float(bb.XLength), float(bb.YLength)) <= bed and float(bb.ZLength) <= bed, \
        "%s does not fit the bed in print orientation" % po.Name

try:
    out = export_dir or os.path.dirname(os.path.realpath(__file__))
except NameError:
    out = export_dir or "/var/home/sebbe/src/3dprinting"
import Mesh
for o, po, tag in zip(objs, pobjs, ("left", "right")):
    Mesh.export([po], os.path.join(out, "rack_minipc_%s.stl" % tag))   # print orientation
    o.Shape.exportStep(os.path.join(out, "rack_minipc_%s.step" % tag))  # model orientation
doc.saveAs(os.path.join(out, "rack_minipc.FCStd"))

for po in pobjs:
    bb = po.Shape.BoundBox
    print("%s (print orientation): %.1f x %.1f x %.1f mm, volume %.0f cm3, solids %d"
          % (po.Name, bb.XLength, bb.YLength, bb.ZLength,
             po.Shape.Volume / 1000, len(po.Shape.Solids)))
print("slots: %d, slot width: %.1f, body: %.1f x %.1f x %.1f, keystones: %d, room above PCs: %.1f"
      % (len(slots), slot_w, inner_w, depth, body_h, len(ks_cols_x) * ks_rows, top_room))
