# GenQuest Design System

## Visual direction

An illustrated storybook rendered as a usable web interface. Warm ivory paper, deep walnut surroundings, oxblood actions, and restrained antique-gold detail establish the physical-book world without rasterizing interface copy.

## Tokens

| Role | Value |
| --- | --- |
| Ink | `#2b2118` |
| Muted ink | `#685946` |
| Paper | `#f8eed6` |
| Oxblood accent | `#852d2b` |
| Deep oxblood | `#641f1e` |
| Gold detail | `#a6864d` |

## Typography

Use EB Garamond / Georgia for the literary display voice and Inter Tight / system sans-serif for controls, navigation, and explanatory text. All UI lettering remains live text.

## Composition

Desktop pages use a fixed cream header and footer framing an illustrated book scene. The illustration is the background plate; the interactive HTML is mapped onto its writing area with a calibrated four-corner `matrix3d()` plane. The upper and lower edges of controls, dividers, and headings must be parallel to their corresponding visible writing-frame tangents.

Mobile uses a readable single-plane composition rather than forcing the desktop projection into a narrow viewport.

## Components

- Header: wordmark, primary navigation, and account path.
- Footer: `© 2026 GenQuest`, Terms of Service, and Privacy Policy in a consistent position.
- Story action: oxblood rectangular button with thin gold inset detail.
- Form fields: square-cornered, high-contrast paper controls with clear labels.
- Perspective plane: page-specific quadrilateral with its coordinates exposed through `data-quad` and covered by a slope regression test.

## Motion

Book-page transitions should remain subtle and optional. Never use motion to hide content, and provide reduced-motion fallbacks.
