# Luanti Nodebox & Texture Editor

A visual editor for creating [Luanti](https://www.luanti.org/) node box definitions and textures by painting on three orthogonal 2D grid views. The intersection of the three projections (a visual hull) defines a 3D voxel shape, which is automatically decomposed into minimal axis-aligned cuboids for Lua output. Painted colors are exported as PNG textures for each face.

![Nodebox Editor screenshot](https://github.com/user-attachments/assets/9c406166-d437-482f-9575-410eb8bdda37)

## How it works

You paint filled cells on three views -- Top (XZ), Front (XY), and Side (ZY). A voxel at position (x, y, z) is considered solid only when it is filled in all three views. The resulting shape updates live in the 3D preview pane and as ready-to-use Lua code that you can copy straight into your node definition.

Each grid is 64x64 pixels. The center 32x32 region represents the node itself (1 pixel = 1/16 of a node unit), with a 16-pixel border on each side for node boxes that extend beyond the standard node boundary.

## Features

- Three-view pixel painting with pencil and flood-fill tools
- Live 3D preview with click-and-drag rotation and per-face shading
- Greedy meshing algorithm produces a minimal cuboid count for the Lua output
- Layer system for shapes that cannot be unambiguously defined by a single set
  of projections (solves the phantom volume problem)
- Color painting with a built-in palette and custom color picker
- Texture export to PNG for each face direction
- Undo/redo support
- Save/load projects in the .nbx format

## Controls

| Input | Action |
|---|---|
| Left click / drag | Paint cells |
| Right click / drag | Erase cells |
| Alt + Left click | Pick color from grid |
| Y | Pencil tool |
| F | Fill tool |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+S | Save |
| Drag on 3D preview | Rotate view |

## Download

Pre-built standalone executables (no Python required) are available on the
[Releases](https://github.com/ZenonSeth/luanti-nodebox-editor/releases) page for Windows and Linux.

## Building from source

Requires Python 3.10+ and pypng (https://pypi.org/project/pypng/):

    pip install pypng
    python src/main.py

### Packaging with PyInstaller

    pip install pyinstaller
    pyinstaller nodebox_editor.spec

The output goes to dist/nodebox-editor/. You need to build on each target
platform separately since PyInstaller does not cross-compile.

## License

LGPL 2.1 -- see LICENSE file.

Third-party licenses (Python, pypng) are listed in THIRD_PARTY_LICENSES.
