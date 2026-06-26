import png
from voxels import _has_node_pixels, _effective_reverse

NODE_START = 16
NODE_END = 48
GRID_SIZE = 64


def hex_to_rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def composite_grid(layers):
    merged = {}
    for layer in reversed(layers):
        if not layer.get("visible", True):
            continue
        merged.update(layer)
    return merged


TEXTURE_SIZE = NODE_END - NODE_START  # 32


def grid_to_png(grid, path):
    rows = []
    for py in range(TEXTURE_SIZE):
        row = []
        for px in range(TEXTURE_SIZE):
            color = grid.get((NODE_START + px, NODE_START + py))
            if color:
                r, g, b = hex_to_rgb(color)
                row.extend([r, g, b, 255])
            else:
                row.extend([0, 0, 0, 255])
        rows.append(row)
    writer = png.Writer(width=TEXTURE_SIZE, height=TEXTURE_SIZE, alpha=True, greyscale=False)
    with open(path, "wb") as f:
        writer.write(f, rows)


def png_to_grid(path):
    reader = png.Reader(filename=path)
    w, h, rows_iter, info = reader.asRGBA8()
    rows = list(rows_iter)
    offset_x = NODE_START + (NODE_END - NODE_START - w) // 2
    offset_y = NODE_START + (NODE_END - NODE_START - h) // 2
    grid = {}
    for py in range(h):
        row = rows[py]
        for px in range(w):
            idx = px * 4
            red, green, blue, alpha = row[idx], row[idx + 1], row[idx + 2], row[idx + 3]
            if alpha < 128:
                continue
            col = offset_x + px
            rw = offset_y + py
            if 0 <= col < GRID_SIZE and 0 <= rw < GRID_SIZE:
                grid[(col, rw)] = rgb_to_hex(red, green, blue)
    return grid


_OPPOSITE_PRIMARY = {"back": "front", "right": "side", "bottom": "top"}


def layers_to_png(layers, view, path):
    primary_key = _OPPOSITE_PRIMARY.get(view)
    if primary_key is not None:
        any_opposite = any(_has_node_pixels(l.get(view, {})) for l in layers if l.get("visible", True))
    else:
        any_opposite = False

    composite = {}
    for layer in reversed(layers):
        if not layer.get("visible", True):
            continue
        if any_opposite:
            composite.update(_effective_reverse(layer[primary_key], layer.get(view, {})))
        else:
            composite.update(layer[view])
    return grid_to_png(composite, path)
