# Pixel ship badge — visual references

Issue **#21**: space-badge SVG art was redesigned by **re-interpreting** free/public pixel spaceship tropes as original `rect`-pixel SVG.  
**No third-party PNG/sprite binaries are embedded or redistributed.**

## Policy

| Rule | Practice |
|------|----------|
| Reference only | Silhouette ratios, part placement, palette *hints* |
| Original draw | All badge geometry is hand-authored SVG rects in `space_badges/ships.py` |
| License | Prefer CC0 / explicit free-for-commercial sources |
| No 1:1 trace | Shape keys (shuttle / rocket / interceptor / lifter) keep game IDs; art is reinterpreted |

## Shape → design intent

| Shape | Silhouette goal | Reinterpreted from (trope) |
|-------|-----------------|----------------------------|
| **shuttle** | Stubby transport, blunt nose, bubble canopy, modest fins | Casual “toy shuttle” / short-range freighter side-views |
| **rocket** | Slim long body, stepped nose cone, stacked tank bands, tall rear fins | Classic missile-style rockets in pixel shmups |
| **interceptor** | Needle nose, large delta wings, twin thrusters | Side-view fighters / interceptors in free pixel ship packs |
| **lifter** | Boxy hull, underslung cargo pods, thick thruster bank, bridge tower | Pixel cargo haulers / industrial freighters |

## Free sources consulted (license re-check before any binary reuse)

These pages informed **composition only**. We did **not** copy pixel data into the repo.

| # | Source | License (as published) | URL | Used for |
|---|--------|------------------------|-----|----------|
| 1 | Kenney — *Space Shooter Redux* | CC0 1.0 | https://kenney.nl/assets/space-shooter-redux | Fighter/rocket part layout cues; chunky outline readability |
| 2 | Kenney — *Pixel Shmup* | CC0 1.0 | https://kenney.nl/assets/pixel-shmup | Side-view ship proportions, wing vs body contrast |
| 3 | OpenGameArt — search “pixel spaceship” (various packs) | **Per-asset** (CC0 / CC-BY / OGA-BY) | https://opengameart.org/art-search-advanced?keys=pixel+spaceship | Silhouette variety; cargo vs fighter differentiation |
| 4 | Kenney asset overview (space / pixel packs) | CC0 (pack-dependent; Kenney free packs are CC0) | https://kenney.nl/assets | Confirm free commercial-use baseline for Kenney packs |

> **Important:** OpenGameArt items each have their own license. If a future PR ever ships an external file, record that file’s exact license and attribution here. This redesign ships **only original SVG**.

## What we took vs what we drew

| From references | How it appears in our SVG |
|-----------------|---------------------------|
| Clear side-view readability | Thick `#050505` outline rects; 8–16px pixel grid |
| Distinct class silhouettes | Four independent hull/wing/pod layouts (not one shared body + tiny fins) |
| Limited game-ready palettes | hull / accent / window / flame hex sets per shape |
| Engine animation hint | 2-frame plume length via `frame_index` |
| Detail density | Drop micro-pixels that vanish at Discord thumbnail size |

## Badge chrome (frame / HUD)

Ship art is only half the look. `generator.py` also rebuilds the **medal shell**:

| Layer | Design |
|-------|--------|
| Background | Radial deep-space gradient + shape-tinted planet limb + vignette |
| Stars | Mixed square / plus / diamond pixel sparkles |
| Rim | Dark outer bevel, metallic gradient ring, dashed orbit track, cardinal studs |
| Name | HUD plate with side wing caps + accent rail |
| Grade | Shield gem (inset lower-left), not a flat corner square |
| Enhance | Bottom chip with side bolts; tier colors unchanged (grey → cyan → gold → pink) |
| Upgrade | Orbit ticks / nodes at stage 2–3 |

## Implementation map

| File | Role |
|------|------|
| `space_badges/ships.py` | Shape renderers + pixel rect art |
| `space_badges/generator.py` | 512×512 circular badge chrome, scene, overlays |
| `space_badges/registry.py` | Variant names / colors / shapes (game data; not art) |
| `docs/assets/pixel_ship_badge_preview.svg` | Single-badge preview |
| `docs/assets/ship_samples/` | Shape / grade / enhance / catalog samples |

## Attribution note

Runtime badges contain **no third-party artwork**. If Kenney or OGA assets are later added as binary samples for docs only, list filename + license + author in this table and keep them under `docs/assets/` (not the badge pipeline).
