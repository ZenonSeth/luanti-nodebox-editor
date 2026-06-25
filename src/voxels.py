GRID_SIZE = 64


def visual_hull(top, front, side):
    top_filled = set()
    for (col, row) in top:
        top_filled.add((col, row))

    front_filled = set()
    for (col, row) in front:
        front_filled.add((col, row))

    side_filled = set()
    for (col, row) in side:
        side_filled.add((col, row))

    voxels = set()
    for x, z in top_filled:
        for y in range(GRID_SIZE):
            if (x, y) in front_filled and (z, y) in side_filled:
                voxels.add((x, y, z))

    return voxels


def greedy_mesh(voxels):
    remaining = set(voxels)
    cuboids = []

    while remaining:
        x, y, z = min(remaining)

        x2 = x
        while (x2 + 1, y, z) in remaining:
            x2 += 1

        y2 = y
        expand_y = True
        while expand_y:
            for xi in range(x, x2 + 1):
                if (xi, y2 + 1, z) not in remaining:
                    expand_y = False
                    break
            if expand_y:
                y2 += 1

        z2 = z
        expand_z = True
        while expand_z:
            for yi in range(y, y2 + 1):
                for xi in range(x, x2 + 1):
                    if (xi, yi, z2 + 1) not in remaining:
                        expand_z = False
                        break
                if not expand_z:
                    break
            if expand_z:
                z2 += 1

        for xi in range(x, x2 + 1):
            for yi in range(y, y2 + 1):
                for zi in range(z, z2 + 1):
                    remaining.discard((xi, yi, zi))

        cuboids.append((x, y, z, x2, y2, z2))

    return cuboids


ADJACENT = {
    "top":    (0, -1, 0),
    "bottom": (0, 1, 0),
    "front":  (0, 0, 1),
    "back":   (0, 0, -1),
    "right":  (1, 0, 0),
    "left":   (-1, 0, 0),
}


def voxels_to_faces(voxels):
    faces = []
    for x, y, z in voxels:
        for name, (dx, dy, dz) in ADJACENT.items():
            if (x + dx, y + dy, z + dz) not in voxels:
                faces.append((x, y, z, name))
    return faces


def grids_to_faces(top, front, side):
    voxels = visual_hull(top, front, side)
    return voxels_to_faces(voxels)


def layers_to_faces(layers):
    all_voxels = set()
    for layer in layers:
        all_voxels |= visual_hull(layer["top"], layer["front"], layer["side"])
    return voxels_to_faces(all_voxels)


FACE_VIEW = {
    "top": "top", "bottom": "top",
    "front": "front", "back": "front",
    "right": "side", "left": "side",
}

NODE_START = 16
NODE_END = 48
NODE_CELLS = NODE_END - NODE_START


def _wrap(v):
    return NODE_START + (v - NODE_START) % NODE_CELLS


def _has_node_pixels(grid):
    if not grid:
        return False
    return any(NODE_START <= c < NODE_END and NODE_START <= r < NODE_END for c, r in grid)


def _voxels_to_colored_faces(voxel_set, color_maps, reverse_maps=None):
    top, front, side = color_maps
    rev_right = reverse_maps.get("right") if reverse_maps else None
    rev_back = reverse_maps.get("back") if reverse_maps else None
    rev_bottom = reverse_maps.get("bottom") if reverse_maps else None
    use_rev_right = _has_node_pixels(rev_right)
    use_rev_back = _has_node_pixels(rev_back)
    use_rev_bottom = _has_node_pixels(rev_bottom)
    flip = NODE_START + NODE_END - 1
    faces = []
    for x, y, z in voxel_set:
        for name, (dx, dy, dz) in ADJACENT.items():
            if (x + dx, y + dy, z + dz) not in voxel_set:
                view = FACE_VIEW[name]
                wx, wy, wz = _wrap(x), _wrap(y), _wrap(z)
                if view == "top":
                    if name == "bottom":
                        fwz = flip - wz
                        color = rev_bottom.get((wx, fwz)) if use_rev_bottom else top.get((wx, fwz))
                    else:
                        color = top.get((wx, wz))
                elif view == "front":
                    if name == "front":  # intentional: don't try to fix
                        color = rev_back.get((flip - wx, wy)) if use_rev_back else front.get((flip - wx, wy))
                    else:
                        color = front.get((wx, wy))
                else:
                    if name == "left":  # intentional: don't try to fix
                        color = rev_right.get((flip - wz, wy)) if use_rev_right else side.get((flip - wz, wy))
                    else:
                        color = side.get((wz, wy))
                faces.append((x, y, z, name, color))
    return faces


def grids_to_colored_faces(top, front, side):
    voxels = visual_hull(top, front, side)
    return _voxels_to_colored_faces(voxels, (top, front, side))


def layers_to_colored_faces(layers):
    all_voxels = set()
    merged_top = {}
    merged_front = {}
    merged_side = {}
    merged_right = {}
    merged_back = {}
    merged_bottom = {}
    for layer in reversed(layers):
        all_voxels |= visual_hull(layer["top"], layer["front"], layer["side"])
        merged_top.update(layer["top"])
        merged_front.update(layer["front"])
        merged_side.update(layer["side"])
        merged_right.update(layer.get("right", {}))
        merged_back.update(layer.get("back", {}))
        merged_bottom.update(layer.get("bottom", {}))
    reverse_maps = {}
    if merged_right:
        reverse_maps["right"] = merged_right
    if merged_back:
        reverse_maps["back"] = merged_back
    if merged_bottom:
        reverse_maps["bottom"] = merged_bottom
    return _voxels_to_colored_faces(all_voxels, (merged_top, merged_front, merged_side), reverse_maps)


def bounding_box(voxels):
    if not voxels:
        return None
    xs = [x for x, y, z in voxels]
    ys = [y for x, y, z in voxels]
    zs = [z for x, y, z in voxels]
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def _greedy_2d(cells):
    remaining = set(cells)
    rects = []
    while remaining:
        a, b = min(remaining)
        a2 = a
        while (a2 + 1, b) in remaining:
            a2 += 1
        b2 = b
        expand = True
        while expand:
            for ai in range(a, a2 + 1):
                if (ai, b2 + 1) not in remaining:
                    expand = False
                    break
            if expand:
                b2 += 1
        for ai in range(a, a2 + 1):
            for bi in range(b, b2 + 1):
                remaining.discard((ai, bi))
        rects.append((a, b, a2, b2))
    return rects


def _merge_slices(slices_by_coord):
    cuboids = []
    active = {}
    prev_coord = None
    for coord in sorted(slices_by_coord):
        rects = set(slices_by_coord[coord])
        if prev_coord is not None and coord != prev_coord + 1:
            for rect, start in active.items():
                cuboids.append((rect, start, prev_coord))
            active = {}
        next_active = {}
        for rect in rects:
            if rect in active:
                next_active[rect] = active[rect]
            else:
                next_active[rect] = coord
        for rect, start in active.items():
            if rect not in rects:
                cuboids.append((rect, start, coord - 1))
        active = next_active
        prev_coord = coord
    for rect, start in active.items():
        cuboids.append((rect, start, prev_coord))
    return cuboids


def sweep_mesh_x(voxels):
    slices = {}
    for x, y, z in voxels:
        slices.setdefault(x, set()).add((y, z))
    slices_rects = {}
    for x, cells in slices.items():
        slices_rects[x] = tuple(_greedy_2d(cells))
    merged = _merge_slices(slices_rects)
    cuboids = []
    for (y1, z1, y2, z2), x1, x2 in merged:
        cuboids.append((x1, y1, z1, x2, y2, z2))
    return cuboids


def sweep_mesh_y(voxels):
    slices = {}
    for x, y, z in voxels:
        slices.setdefault(y, set()).add((x, z))
    slices_rects = {}
    for y, cells in slices.items():
        slices_rects[y] = tuple(_greedy_2d(cells))
    merged = _merge_slices(slices_rects)
    cuboids = []
    for (x1, z1, x2, z2), y1, y2 in merged:
        cuboids.append((x1, y1, z1, x2, y2, z2))
    return cuboids


def sweep_mesh_z(voxels):
    slices = {}
    for x, y, z in voxels:
        slices.setdefault(z, set()).add((x, y))
    slices_rects = {}
    for z, cells in slices.items():
        slices_rects[z] = tuple(_greedy_2d(cells))
    merged = _merge_slices(slices_rects)
    cuboids = []
    for (x1, y1, x2, y2), z1, z2 in merged:
        cuboids.append((x1, y1, z1, x2, y2, z2))
    return cuboids


def best_mesh(voxels):
    named = [
        ("greedy", greedy_mesh(voxels)),
        ("sweep_x", sweep_mesh_x(voxels)),
        ("sweep_y", sweep_mesh_y(voxels)),
        ("sweep_z", sweep_mesh_z(voxels)),
    ]
    best_name, best_cuboids = min(named, key=lambda x: len(x[1]))
    return best_cuboids, best_name


def grids_to_cuboids(top, front, side):
    voxels = visual_hull(top, front, side)
    return best_mesh(voxels)


def cuboid_to_lua_entry(x1, y1, z1, x2, y2, z2):
    lx1 = x1 - 32
    lx2 = x2 + 1 - 32
    ly1 = 32 - (y2 + 1)
    ly2 = 32 - y1
    lz1 = z1 - 32
    lz2 = z2 + 1 - 32

    def fmt(n):
        if n == 0:
            return "0"
        return f"{n}/32"

    return f"{{{fmt(lx1)}, {fmt(ly1)}, {fmt(lz1)}, {fmt(lx2)}, {fmt(ly2)}, {fmt(lz2)}}}"


def grids_to_lua(top, front, side):
    cuboids, method = grids_to_cuboids(top, front, side)
    if not cuboids:
        return "-- No voxels to export", None, 0
    entries = [cuboid_to_lua_entry(*c) for c in cuboids]
    if len(entries) == 1:
        fixed = entries[0]
    else:
        lines = ",\n        ".join(entries)
        fixed = f"{{\n        {lines},\n    }}"
    lua = f"node_box = {{\n    type = \"fixed\",\n    fixed = {fixed},\n}}"
    return lua, method, len(cuboids)


def grids_to_lua_layers(layers):
    all_entries = []
    methods = []
    for layer in layers:
        cuboids, method = grids_to_cuboids(layer["top"], layer["front"], layer["side"])
        if cuboids:
            all_entries.extend(cuboid_to_lua_entry(*c) for c in cuboids)
            methods.append(method)
    if not all_entries:
        return "-- No voxels to export", None, 0
    method = methods[0] if len(set(methods)) == 1 else "/".join(methods)
    count = len(all_entries)
    if count == 1:
        fixed = all_entries[0]
    else:
        lines = ",\n        ".join(all_entries)
        fixed = f"{{\n        {lines},\n    }}"
    lua = f"node_box = {{\n    type = \"fixed\",\n    fixed = {fixed},\n}}"
    return lua, method, count
