import re

GRID_SIZE = 64


def visual_hull(top, front, side):
    flip = NODE_START + NODE_END - 1
    top_filled = set()
    for (col, row) in top:
        top_filled.add((col, flip - row))

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
                        color = rev_bottom.get((wx, wz)) if use_rev_bottom else top.get((wx, wz))
                    else:
                        color = top.get((wx, flip - wz))
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


def _effective_reverse(primary, opposite):
    """Return opposite if it has any pixels, else fall back to primary."""
    if _has_node_pixels(opposite):
        return opposite
    return primary


def layers_to_colored_faces(layers):
    all_voxels = set()
    merged_top = {}
    merged_front = {}
    merged_side = {}
    eff_right = {}
    eff_back = {}
    eff_bottom = {}
    any_right = any(_has_node_pixels(l.get("right", {})) for l in layers)
    any_back = any(_has_node_pixels(l.get("back", {})) for l in layers)
    any_bottom = any(_has_node_pixels(l.get("bottom", {})) for l in layers)
    for layer in reversed(layers):
        all_voxels |= visual_hull(layer["top"], layer["front"], layer["side"])
        merged_top.update(layer["top"])
        merged_front.update(layer["front"])
        merged_side.update(layer["side"])
        if any_back:
            eff_back.update(_effective_reverse(layer["front"], layer.get("back", {})))
        if any_right:
            eff_right.update(_effective_reverse(layer["side"], layer.get("right", {})))
        if any_bottom:
            eff_bottom.update(_effective_reverse(layer["top"], layer.get("bottom", {})))
    reverse_maps = {}
    if any_right:
        reverse_maps["right"] = eff_right
    if any_back:
        reverse_maps["back"] = eff_back
    if any_bottom:
        reverse_maps["bottom"] = eff_bottom
    return _voxels_to_colored_faces(all_voxels, (merged_top, merged_front, merged_side), reverse_maps)


def layers_to_merged_grids(layers):
    merged_top = {}
    merged_front = {}
    merged_side = {}
    for layer in reversed(layers):
        merged_top.update(layer["top"])
        merged_front.update(layer["front"])
        merged_side.update(layer["side"])
    return merged_top, merged_front, merged_side


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
    all_cuboids = []
    all_entries = []
    methods = []
    for layer in layers:
        cuboids, method = grids_to_cuboids(layer["top"], layer["front"], layer["side"])
        if cuboids:
            all_cuboids.extend(cuboids)
            all_entries.extend(cuboid_to_lua_entry(*c) for c in cuboids)
            methods.append(method)
    if not all_entries:
        return "-- No voxels to export", None, 0, []
    method = methods[0] if len(set(methods)) == 1 else "/".join(methods)
    count = len(all_entries)
    if count == 1:
        fixed = all_entries[0]
    else:
        lines = ",\n        ".join(all_entries)
        fixed = f"{{\n        {lines},\n    }}"
    lua = f"node_box = {{\n    type = \"fixed\",\n    fixed = {fixed},\n}}"
    return lua, method, count, all_cuboids


def _parse_number(tok):
    tok = tok.strip()
    if "/" in tok:
        num, den = tok.split("/")
        return float(num) / float(den)
    return float(tok)


def _extract_brace_groups(s):
    """Return the balanced {...} substrings found at the top level of s."""
    groups = []
    depth = 0
    start = None
    for i, ch in enumerate(s):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                groups.append(s[start:i + 1])
                start = None
    return groups


_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?(?:/-?\d+(?:\.\d+)?)?")


def parse_fixed_boxes(text):
    """Parse pasted Lua text into a list of (x1, y1, z1, x2, y2, z2) boxes in node units.

    Accepts a bare box `{x1,y1,z1,x2,y2,z2}`, a bare array of boxes
    `{{...}, {...}}`, or a full `node_box = {type = "fixed", fixed = {...}}` table.
    Raises ValueError with a human-readable message if nothing usable is found.
    """
    fixed_match = re.search(r"fixed\s*=\s*(\{.*)", text, re.DOTALL)
    body = fixed_match.group(1) if fixed_match else text

    outer_groups = _extract_brace_groups(body)
    if not outer_groups:
        raise ValueError("No box data found (expected Lua table syntax like { ... }).")
    outer = outer_groups[0]

    inner_groups = _extract_brace_groups(outer[1:-1])
    box_strs = inner_groups if inner_groups else [outer]

    boxes = []
    for box_str in box_strs:
        nums = _NUMBER_RE.findall(box_str)
        if len(nums) != 6:
            raise ValueError(f"Expected 6 numbers per box, found {len(nums)} in: {box_str.strip()}")
        boxes.append(tuple(_parse_number(n) for n in nums))
    return boxes


def fixed_box_to_grid_range(box):
    """Inverse of cuboid_to_lua_entry: node-unit box -> voxel grid range, clamped to the grid.

    Returns (grid_range, was_clamped) where was_clamped is True if the box extended
    beyond the representable -1..+1 node-unit range and had to be clipped.
    """
    f1, f2, f3, f4, f5, f6 = box
    lx1, ly1, lz1 = round(f1 * 32), round(f2 * 32), round(f3 * 32)
    lx2, ly2, lz2 = round(f4 * 32), round(f5 * 32), round(f6 * 32)

    x1, x2 = lx1 + 32, lx2 + 32 - 1
    y1, y2 = 32 - ly2, 32 - ly1 - 1
    z1, z2 = lz1 + 32, lz2 + 32 - 1

    cx1, cx2 = max(0, min(GRID_SIZE - 1, x1)), max(0, min(GRID_SIZE - 1, x2))
    cy1, cy2 = max(0, min(GRID_SIZE - 1, y1)), max(0, min(GRID_SIZE - 1, y2))
    cz1, cz2 = max(0, min(GRID_SIZE - 1, z1)), max(0, min(GRID_SIZE - 1, z2))
    if cx1 > cx2 or cy1 > cy2 or cz1 > cz2:
        raise ValueError(f"Box {box} falls outside the representable range and was skipped.")
    was_clamped = (cx1, cx2, cy1, cy2, cz1, cz2) != (x1, x2, y1, y2, z1, z2)
    return (cx1, cy1, cz1, cx2, cy2, cz2), was_clamped


def grid_range_to_layer_grids(x1, y1, z1, x2, y2, z2, color):
    """Build top/front/side grids that reproduce a single axis-aligned voxel box, filled with color."""
    flip = NODE_START + NODE_END - 1
    top = {(x, flip - z): color for x in range(x1, x2 + 1) for z in range(z1, z2 + 1)}
    front = {(x, y): color for x in range(x1, x2 + 1) for y in range(y1, y2 + 1)}
    side = {(z, y): color for z in range(z1, z2 + 1) for y in range(y1, y2 + 1)}
    return top, front, side


def import_fixed_boxes_as_layers(text, color, name_fn):
    """Parse pasted `fixed` node_box Lua into a list of layer dicts, one per box.

    name_fn(index) -> layer name, where index starts at 1.
    Raises ValueError if the text can't be parsed, or if every box is out of range.
    """
    boxes = parse_fixed_boxes(text)
    layers = []
    skipped = []
    for i, box in enumerate(boxes, start=1):
        try:
            grid_range, was_clamped = fixed_box_to_grid_range(box)
        except ValueError as e:
            skipped.append(str(e))
            continue
        if was_clamped:
            skipped.append(f"Box {box} extended beyond the representable range and was clipped to fit.")
        top, front, side = grid_range_to_layer_grids(*grid_range, color)
        layers.append({"name": name_fn(len(layers) + 1), "visible": True,
                        "top": top, "front": front, "side": side,
                        "bottom": {}, "back": {}, "right": {}})
    if not layers:
        raise ValueError("\n".join(skipped) if skipped else "No boxes found.")
    return layers, skipped


def cuboids_to_selection_box_lua(cuboids):
    if not cuboids:
        return None
    bx1 = min(c[0] for c in cuboids)
    by1 = min(c[1] for c in cuboids)
    bz1 = min(c[2] for c in cuboids)
    bx2 = max(c[3] for c in cuboids)
    by2 = max(c[4] for c in cuboids)
    bz2 = max(c[5] for c in cuboids)
    entry = cuboid_to_lua_entry(bx1, by1, bz1, bx2, by2, bz2)
    return f"-- Can also be used for collision_box\nselection_box = {{\n    type = \"fixed\",\n    fixed = {{{entry}}},\n}}"
