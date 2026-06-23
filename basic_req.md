Project: Luanti Node Box Editor
A desktop Python app for visually building Luanti node box definitions using pixel-painting.

Stack

Pure Python, Tkinter only (stdlib, no external dependencies)
Target: Windows/Linux

Core concept

Instead of editing numeric coordinates directly, the user paints filled/empty cells on
three orthogonal 2D grid views. The intersection of those three projections defines a
3D voxel volume, which is then automatically decomposed into minimal axis-aligned cuboids
for the Lua output. Think pixel art, but in three views that combine into a 3D shape.

Data model

Each 2D grid view is a 64x64 pixel grid
The center 32x32 region represents the node itself (1 pixel = 1/16 of a node unit)
The surrounding 16-pixel border on each side allows node boxes to extend beyond the node boundary
A cell is either filled (dark) or empty (light); toggled by clicking
A voxel at (x, y, z) is considered filled only if it is filled in all three views that project through it
Output coordinates use integer n/16 notation, e.g. { -8/16, -8/16, -8/16, 8/16, 8/16, 8/16 }

Layout

Four panes in a 2x2 grid:

Top-left: Top view (XZ plane, looking down the Y axis)
Top-right: Front view (XY plane, looking down the Z axis)
Bottom-left: Side view (ZY plane, looking down the X axis)
Bottom-right: 3D preview (rotatable by mouse drag)

Additional UI: Lua output text area, "Advanced: Layers" toggle

2D editing views

Each view is a 64x64 grid of toggleable cells
Left-click a cell to fill it, click again to clear it
Click-and-drag to paint or erase multiple cells in one stroke
All three views update the 3D preview and Lua output live as the user paints
The center 32x32 area should be visually distinguished (subtle border or background tint)
  to show the node boundary

Visual hull reconstruction

A voxel (x, y, z) in the 32x32x32 internal grid (or 64x64x64 extended grid) is filled
when all three of these are true:
  - Top view cell (x, z) is filled
  - Front view cell (x, y) is filled
  - Side view cell (z, y) is filled

This is the intersection of three orthogonal projections (visual hull).

Limitation: this can produce phantom volumes when projections overlap ambiguously
(e.g. two small cubes at diagonal corners will generate extra unwanted geometry).
The 3D preview makes this visible. Layers solve it when needed.

Greedy meshing

The filled voxel set is converted to a minimal list of axis-aligned cuboids.
Algorithm: iterate through the voxel grid, greedily expand each unvisited filled voxel
into the largest possible cuboid, mark those voxels as visited, repeat.
This produces the node box 6-tuples for the Lua output.

Layers

Hidden by default behind an "Advanced: Layers" checkbox.
Most use cases need only a single layer.

When enabled:
  - Each layer has its own independent set of three 2D grids
  - The user can add, delete, rename, and reorder layers
  - Greedy meshing runs per-layer to produce cuboids
  - All layers' cuboids are combined in the final Lua output
  - The 3D preview renders all layers together (possibly with per-layer coloring)

Layers solve the phantom volume problem: shapes that can't be unambiguously defined
by three projections in a single layer can be split across multiple layers.

3D preview

Custom software renderer on a Tkinter canvas, no OpenGL
Isometric-style projection with configurable azimuth and elevation, rotated by mouse drag
Geometry: each cuboid is decomposed into its 6 faces (axis-aligned quads)
Backface culling: cull faces whose cardinal normal faces away from the camera
  (reduces to a single component sign check)
Painter's algorithm: sort visible faces by camera-space depth of face center, draw back to front
Per-face shading: hardcoded brightness multiplier per face orientation
  (top lightest, bottom darkest, sides intermediate with slight east/west variation)
Wireframe edges drawn on top of filled faces for crispness
The full node boundary shown as a faint wireframe reference cube

Output

Lua snippet generated live as the user paints
Shows the node_box table in fixed format with n/16 notation
Copyable from a text widget in the UI

Packaging

PyInstaller used to produce standalone executables (dev/build dependency only, not runtime)
Build on each target platform separately (PyInstaller does not cross-compile):
  - Windows: pyinstaller --onefile --windowed main.py -> single .exe
  - Linux: pyinstaller --onefile main.py -> single native binary
No Python installation required by the end user
Only stdlib/Tkinter is used, so no special PyInstaller configuration needed

Future features (low priority)

Texture painting: replace binary filled/empty cells with color/transparent
  - Color = filled, transparent = empty (unifies shape and texture editing, no mode toggle)
  - Preset color palette in the right panel with solid colors + transparent option (no semi-transparency)
  - "+" button at the bottom of the palette to add custom colors via tkinter.colorchooser
  - Each view's colors define the shape AND the texture for the primary face
      (Top->top, Front->front, Side->left)
  - Optional separate texture grids for opposite faces (bottom, back, right)
      These are texture-only — they do not affect voxel shape determination
      If not provided, the opposite face mirrors the primary face's colors
  - 3D preview shades each voxel face with the pixel color from the corresponding view
  - Export textures as PNG using Pillow (acceptable dependency since we're packaging with PyInstaller)

3D preview optimization: scanline back-to-front rendering
  - Determine camera octant from view vector component signs
  - Iterate voxels in axis order matching that octant (e.g. X asc, Y desc, Z asc)
  - Faces are emitted in guaranteed back-to-front order, no sort needed
  - O(n) instead of O(n log n), works because all faces are unit-sized

Import existing Lua node_box definitions: parse n/16 values back into filled grid cells
  (trivial inverse of the output operation)
