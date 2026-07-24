# Perspective homepage proof

This is a separate proof of concept. The original `mockup` directory is untouched.

The hero content is real HTML projected onto the generated left-page writing plane with a calculated CSS `matrix3d()` homography. The upper edge follows the local tangent of the curved page rim rather than the flatter corner-to-corner chord. Add `?debug=1` to the URL to show the four calibration points.

## Perspective alignment requirement

Every book-page design must map its live HTML to a calibrated four-corner plane. The top and bottom edges of headings, controls, dividers, and buttons must run parallel to the corresponding visible writing-frame tangents in the artwork; axis-aligned HTML over a perspective page is not acceptable. Store the calibrated corner coordinates in the page script, expose them through `data-quad`, and add a Cypress regression assertion for both edge slopes. Recalibrate whenever the background artwork changes.

Run from PowerShell:

```powershell
cd "F:\MyProject\Python\2026-07-17-gen-quest\src\gen-quest\vue_frontend\src\assets\ui-concepts\mockup-perspective"
python -m http.server 4175
```

Open `http://localhost:4175/index.html`.
