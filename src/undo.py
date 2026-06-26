UNDO_LIMIT = 50

_undo_stack = []
_redo_stack = []


def _snap(layers, active_idx):
    layer = layers[active_idx]
    return (
        active_idx,
        dict(layer["top"]),
        dict(layer["front"]),
        dict(layer["side"]),
        dict(layer.get("bottom", {})),
        dict(layer.get("back", {})),
        dict(layer.get("right", {})),
    )


def _restore(layers, grids, snap, select_layer_fn):
    idx, top, front, side, bottom, back, right = snap
    layers[idx]["top"] = top
    layers[idx]["front"] = front
    layers[idx]["side"] = side
    layers[idx]["bottom"] = bottom
    layers[idx]["back"] = back
    layers[idx]["right"] = right
    select_layer_fn(idx)


def push(layers, active_idx):
    _undo_stack.append(_snap(layers, active_idx))
    if len(_undo_stack) > UNDO_LIMIT:
        _undo_stack.pop(0)
    _redo_stack.clear()


def undo(layers, active_idx, grids, select_layer_fn):
    if not _undo_stack:
        return False
    _redo_stack.append(_snap(layers, active_idx))
    _restore(layers, grids, _undo_stack.pop(), select_layer_fn)
    return True


def redo(layers, active_idx, grids, select_layer_fn):
    if not _redo_stack:
        return False
    _undo_stack.append(_snap(layers, active_idx))
    _restore(layers, grids, _redo_stack.pop(), select_layer_fn)
    return True


def clear():
    _undo_stack.clear()
    _redo_stack.clear()
