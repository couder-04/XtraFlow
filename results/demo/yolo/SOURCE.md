# YOLO demo source

Input feasibility — not a fuel-saving result

- Dataset: Mixed research CCTV — straight / one-way corridors
- Attribution: Zenodo DOI 10.5281/zenodo.3986141 (CC BY 4.0); Seattle I-5 trafficdb (WSDOT / Chan–Vasconcelos)
- Note: Four independent corridor cameras mapped to N/E/S/W for a mosaic. Not synchronized approaches of one intersection. S is true southbound one-way highway; N/E/W are Zenodo arterial cams.

Clips under `data/video/` are gitignored. Re-run:

```bash
make yolo_demo
# or: python -m demo.run_yolo_demo
python -m demo.yolo_story   # rebuild GO/PAUSE story only
```

Dashboard:

```bash
make yolo_dashboard
```

Outputs:

- `results/demo/yolo/yolo_story.mp4` — **main story**: 2×2 cams; GO plays, other axis PAUSE (frozen)
- `results/demo/yolo/yolo_story.gif` — README-playable loop of the story
- `results/demo/yolo_overlay.mp4` — primary single-cam overlay
- `results/demo/yolo/yolo_mosaic.mp4` — plain 2×2 mosaic
- `results/demo/yolo/overlay_{N,E,S,W}.mp4`
- `results/demo/yolo/counts_*.json`
- `results/demo/yolo/yolo_demo_summary.json` — counts, phase timeline, idle-fuel proxy + published headlines
