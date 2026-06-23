## Next up

- [ ] 3D preview: use per-cell colors from grids instead of flat BASE_COLOR
      (each face's color comes from the corresponding view's grid cell)
- [ ] Lua output generation: convert cuboids/AABB to n/16 notation
- [ ] Export UI: button/panel for exporting Lua snippet (greedy mesh vs single AABB option)
- [ ] Labels on the 3 grid views (Top, Front, Side)

## Polish

- [ ] Undo/redo
- [ ] Dirty indicator in title bar (e.g. asterisk when unsaved)
- [ ] Keyboard shortcuts (Ctrl+S save, Ctrl+Z undo, Ctrl+N new)

## Future features (from design doc)

- [ ] Layers (behind "Advanced: Layers" checkbox)
- [ ] Texture painting (color per cell, PNG export via Pillow)
- [ ] Custom color picker ("+" button on palette)
- [ ] Import existing Lua node_box definitions
- [ ] 3D preview: scanline back-to-front rendering optimization
- [ ] Packaging with PyInstaller
