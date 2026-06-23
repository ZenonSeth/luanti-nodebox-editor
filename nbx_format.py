import json
import string

GRID_SIZE = 64
INDEX_CHARS = string.ascii_letters
MAX_INDEXED_COLORS = len(INDEX_CHARS)

# Based on run-length encoding, creates human-readable json files
# Two formats: indexed and inlined


def _collect_colors(grids):
    colors = set()
    for grid in grids:
        for color in grid.values():
            colors.add(color)
    return colors


def _encode_row_indexed(grid, row, palette_map):
    parts = []
    empty_run = 0
    for col in range(GRID_SIZE):
        color = grid.get((col, row))
        if color is None:
            empty_run += 1
        else:
            if empty_run > 0:
                parts.append(str(empty_run))
                empty_run = 0
            parts.append(palette_map[color])
    if empty_run > 0:
        parts.append(str(empty_run))
    return "".join(parts)


def _encode_row_inline(grid, row):
    parts = []
    empty_run = 0
    for col in range(GRID_SIZE):
        color = grid.get((col, row))
        if color is None:
            empty_run += 1
        else:
            if empty_run > 0:
                parts.append(str(empty_run))
                empty_run = 0
            parts.append(color)
    if empty_run > 0:
        parts.append(str(empty_run))
    return "".join(parts)


def _encode_grid(grid, encode_row_fn):
    rows = []
    for row in range(GRID_SIZE):
        rows.append(encode_row_fn(grid, row))
    return rows


def save_nbx(top, front, side):
    grids = [top, front, side]
    colors = _collect_colors(grids)

    if len(colors) <= MAX_INDEXED_COLORS:
        palette_map = {}
        palette_out = {}
        for i, color in enumerate(sorted(colors)):
            char = INDEX_CHARS[i]
            palette_map[color] = char
            palette_out[char] = color

        data = {
            "version": 1,
            "type": "indexed",
            "palette": palette_out,
            "top": _encode_grid(top, lambda g, r: _encode_row_indexed(g, r, palette_map)),
            "front": _encode_grid(front, lambda g, r: _encode_row_indexed(g, r, palette_map)),
            "side": _encode_grid(side, lambda g, r: _encode_row_indexed(g, r, palette_map)),
        }
    else:
        data = {
            "version": 1,
            "type": "inline",
            "top": _encode_grid(top, _encode_row_inline),
            "front": _encode_grid(front, _encode_row_inline),
            "side": _encode_grid(side, _encode_row_inline),
        }

    return json.dumps(data, indent=2)


def _decode_row_indexed(row_str, reverse_palette):
    grid = {}
    col = 0
    i = 0
    while i < len(row_str):
        ch = row_str[i]
        if ch.isdigit():
            num_str = ch
            while i + 1 < len(row_str) and row_str[i + 1].isdigit():
                i += 1
                num_str += row_str[i]
            col += int(num_str)
        elif ch in reverse_palette:
            grid[(col, None)] = reverse_palette[ch]
            col += 1
        i += 1
    return grid


def _decode_row_inline(row_str):
    grid = {}
    col = 0
    i = 0
    while i < len(row_str):
        ch = row_str[i]
        if ch == '#':
            color = row_str[i:i + 7]
            grid[(col, None)] = color
            col += 1
            i += 7
        elif ch.isdigit():
            num_str = ch
            while i + 1 < len(row_str) and row_str[i + 1].isdigit():
                i += 1
                num_str += row_str[i]
            col += int(num_str)
            i += 1
        else:
            i += 1
    return grid


def _decode_grid(rows, decode_fn):
    grid = {}
    for row_idx, row_str in enumerate(rows):
        row_cells = decode_fn(row_str)
        for (col, _), color in row_cells.items():
            grid[(col, row_idx)] = color
    return grid


def load_nbx(json_str):
    data = json.loads(json_str)

    if data["type"] == "indexed":
        reverse_palette = data["palette"]
        decode_fn = lambda row_str: _decode_row_indexed(row_str, reverse_palette)
    else:
        decode_fn = _decode_row_inline

    top = _decode_grid(data["top"], decode_fn)
    front = _decode_grid(data["front"], decode_fn)
    side = _decode_grid(data["side"], decode_fn)

    return top, front, side
