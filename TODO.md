## Onboarding

- [x] Tutorial popup: image-based walkthrough showing how the three views
      combine into a 3D shape. Shows on first launch with "Don't show again"
      checkbox. Also accessible from Help/About menu.
- [x] Baked-in starter model: load a simple example (e.g. chair) on first
      launch so users see a working model instead of empty grids

## Planned features

- [x] Opposite-side textures: edit back/bottom/right face colors independently
      (texture-only, does not affect voxel shape -- shape comes from primary side)
      - Toggle via "Edit Bottom/Back/Right" button, reuses the same three views
      - On export: if an opposite texture is empty or identical to its primary,
        show a label like "same as primary" with no export button for that face.
        Only show the export button when the opposite texture actually differs.
      - Export differing opposite textures as separate PNGs
- [x] Copy To buttons on front/side views to copy into the other view
      (useful for symmetrical shapes, with undo support)
- [x] Symmetry drawing: toggle 2-way or 4-way symmetry around center point,
      plus a mirror checkbox. Applies to pencil tool only, not fill.
- [ ] Variable pencil tool: draws the selected color with a random offset
      (e.g. #ff00cc might draw as #f000c0). Controllable via a slider
      for the amount of variation.

## Future features

- [ ] .obj export: export each layer as its own mesh with its own material/texture,
      avoiding the layer compositing limitation of the nodebox format. Each face
      needs correct UV mapping into the layer's texture.

- [x] Import PNG texture: load a 32x32 PNG into any of the three 2D views,
      mapping pixel colors to grid cells (fills the node region only)
- [x] 3D preview: scanline back-to-front rendering optimization
- [x] 3D preview: use per-cell colors from grids instead of flat shading
      (each face's color comes from the corresponding view's grid cell)
