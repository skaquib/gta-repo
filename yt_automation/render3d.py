"""
render3d.py — Small software 3D renderer for FramedFacts ("facts shown in
3D"), numpy + PIL only: no GPU, no paid API, no downloads.

Meshes are triangle lists in world space. render() back-face culls, shades
each triangle (ambient + Lambert + Blinn-Phong specular), projects with a
perspective camera on the +z axis looking at the origin, sorts far-to-near
(painter's algorithm -- fine for the convex/exploded objects these explainers
use) and rasterizes with PIL at a supersampled size for anti-aliasing.

Geometry helpers:
  football_panels()  32-panel ball (12 pentagons + 20 hexagons) from a
                     truncated icosahedron, each panel a puffed spherical
                     patch with a darker seam band at its edge
  icosphere(n)       smooth sphere for inner layers
  rot_matrix(ax, ay, az)
"""
import math
import numpy as np
from PIL import Image, ImageDraw

PHI = (1 + 5 ** 0.5) / 2


def _unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def icosahedron():
    v = np.array([(-1, PHI, 0), (1, PHI, 0), (-1, -PHI, 0), (1, -PHI, 0),
                  (0, -1, PHI), (0, 1, PHI), (0, -1, -PHI), (0, 1, -PHI),
                  (PHI, 0, -1), (PHI, 0, 1), (-PHI, 0, -1), (-PHI, 0, 1)], dtype=float)
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4),
         (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8),
         (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    return _unit(v), f


def _outward(verts, tris):
    """Flip triangles whose winding points inward (all shapes here are star-shaped)."""
    p = verts[tris]
    n = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    inward = (n * p.mean(1)).sum(1) < 0
    tris = tris.copy()
    tris[inward] = tris[inward][:, [0, 2, 1]]
    return tris


def icosphere(subdiv=3):
    v, f = icosahedron()
    verts = list(map(tuple, v))
    cache = {}

    def mid(a, b):
        key = (min(a, b), max(a, b))
        if key not in cache:
            m = _unit((np.array(verts[a]) + np.array(verts[b])) / 2)
            verts.append(tuple(m))
            cache[key] = len(verts) - 1
        return cache[key]

    faces = f
    for _ in range(subdiv):
        nf = []
        for a, b, c in faces:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = nf
    V = np.array(verts)
    return V, _outward(V, np.array(faces))


def _order_around(pts, c):
    c = _unit(c)
    a = pts[0] - c * np.dot(pts[0], c)
    u = a / np.linalg.norm(a)
    w = np.cross(c, u)
    ang = [math.atan2(np.dot(p, w), np.dot(p, u)) for p in pts]
    return [p for _, p in sorted(zip(ang, pts), key=lambda x: x[0])]


def _panel_mesh(center, boundary, rings=(0, 0.36, 0.63, 0.83, 0.935, 1.0), sub=3, puff=0.035):
    C = _unit(center)
    B = [_unit(p) for p in boundary]
    n = len(B)
    bpts = []
    for k in range(n):
        a, b = B[k], B[(k + 1) % n]
        for s in range(sub):
            bpts.append(_unit(a * (1 - s / sub) + b * (s / sub)))
    m = len(bpts)
    verts = [C * (1 + puff)]
    ring_idx = [[0]]
    for r in rings[1:]:
        idx = []
        for q in bpts:
            p = _unit(C * (1 - r) + q * r)
            verts.append(p * (1 + puff * (1 - r ** 2)))
            idx.append(len(verts) - 1)
        ring_idx.append(idx)
    tris, seam = [], []
    for j in range(m):
        tris.append((0, ring_idx[1][j], ring_idx[1][(j + 1) % m]))
        seam.append(False)
    last = len(rings) - 2
    for ri in range(1, len(rings) - 1):
        A, Bn = ring_idx[ri], ring_idx[ri + 1]
        for j in range(m):
            j2 = (j + 1) % m
            tris += [(A[j], Bn[j], Bn[j2]), (A[j], Bn[j2], A[j2])]
            seam += [ri == last, ri == last]
    V = np.array(verts)
    return V, _outward(V, np.array(tris)), np.array(seam)


def football_panels():
    """32 panels of a classic ball: list of dict(kind, center, V, T, seam)."""
    V, F = icosahedron()
    edges = set()
    for a, b, c in F:
        for x, y in ((a, b), (b, c), (c, a)):
            edges.add((min(x, y), max(x, y)))

    def tp(a, b):  # truncation point on edge a-b, one third from a
        return V[a] + (V[b] - V[a]) / 3.0

    panels = []
    for i in range(12):
        nbrs = [b if a == i else a for a, b in edges if i in (a, b)]
        pts = _order_around([tp(i, n) for n in nbrs], V[i])
        pv, pt, ps = _panel_mesh(V[i], pts)
        panels.append(dict(kind="pent", center=_unit(V[i]), V=pv, T=pt, seam=ps))
    for a, b, c in F:
        ctr = _unit(V[a] + V[b] + V[c])
        pts = _order_around([tp(a, b), tp(b, a), tp(b, c), tp(c, b), tp(c, a), tp(a, c)], ctr)
        pv, pt, ps = _panel_mesh(ctr, pts)
        panels.append(dict(kind="hex", center=ctr, V=pv, T=pt, seam=ps))
    return panels


def rot_matrix(ax=0.0, ay=0.0, az=0.0):
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def axis_rotation(axis, angle):
    k = _unit(axis)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(angle) * K + (1 - math.cos(angle)) * K @ K


class Camera:
    def __init__(self, cx, cy, focal, dist):
        self.cx, self.cy, self.f, self.D = cx, cy, focal, dist


def render(meshes, size, cam, light=(-0.45, 0.65, 0.85), ambient=0.32, diffuse=0.78, ss=2):
    """meshes: dicts with V (N,3) world coords, T (M,3), colors (M,3) 0-255,
    optional spec (0-1), shin, and N (M,3) smooth shading normals per
    triangle (culling still uses the true facet normal), "facet" (0-1, how much
    of the flat facet normal is mixed in; default 0.45), and "layer" (int draw
    order: lower layers are painted first, depth-sorted within a layer --
    avoids jagged seams where overlapping parts intersect). Returns RGBA `size`."""
    W, H = size
    L = _unit(light)
    cam_pos = np.array([0.0, 0.0, cam.D])
    polys, cols, depths, layers = [], [], [], []
    for m in meshes:
        P = m["V"][m["T"]]                       # (M,3,3)
        cen = P.mean(1)
        n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        n = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
        to_cam = cam_pos - cen
        vis = (n * to_cam).sum(1) > 0
        if not vis.any():
            continue
        n, P, cen, to_cam = n[vis], P[vis], cen[vis], to_cam[vis]
        col = np.asarray(m["colors"], dtype=float)[vis]
        if "N" in m:   # optional smooth shading normals (blended with the facet normal;
            fw = m.get("facet", 0.45)           # lower "facet" = smoother, rounder look)
            n = _unit(fw * n + (1 - fw) * np.asarray(m["N"], dtype=float)[vis])
        lam = np.clip(n @ L, 0, 1)
        hv = _unit(L + _unit(to_cam))
        spec = np.clip((n * hv).sum(1), 0, 1) ** m.get("shin", 30) * m.get("spec", 0.3)
        shade = col * (ambient + diffuse * lam)[:, None] + 255 * spec[:, None]
        z = cam.D - P[..., 2]
        x2 = (cam.cx + cam.f * P[..., 0] / z) * ss
        y2 = (cam.cy - cam.f * P[..., 1] / z) * ss
        polys.append(np.stack([x2, y2], -1))
        cols.append(np.clip(shade, 0, 255))
        depths.append(np.linalg.norm(to_cam, axis=1))
        layers.append(np.full(len(z), m.get("layer", 0)))   # optional draw order: lower layers first
    img = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    if not polys:
        return img.resize((W, H), Image.LANCZOS)
    polys = np.concatenate(polys)
    cols = np.concatenate(cols).astype(int)
    order = np.lexsort((-np.concatenate(depths), np.concatenate(layers)))
    d = ImageDraw.Draw(img)
    pl, cl = polys[order].tolist(), cols[order].tolist()
    for poly, c in zip(pl, cl):
        c = (c[0], c[1], c[2], 255)
        d.polygon([tuple(p) for p in poly], fill=c, outline=c)
    return img.resize((W, H), Image.LANCZOS)
