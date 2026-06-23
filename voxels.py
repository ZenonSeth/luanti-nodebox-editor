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


def grids_to_cuboids(top, front, side):
    voxels = visual_hull(top, front, side)
    return greedy_mesh(voxels)
