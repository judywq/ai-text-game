# GenQuest UI Redesign Plan: "The Living Storybook"

Status: PLAN + STATIC MOCKUP. No Vue app code has been changed yet.

A clickable HTML mockup of this plan lives in `mockup/` (all 16 screens,
light + dark themes, shared `styles.css` implementing the token table in
Section 3). Every route in the concept map has a screen; `signup` is
deliberately absent (see 5b). View it with:
`python -m http.server 8137 --directory vue_frontend/src/assets/ui-concepts/mockup`
then open http://localhost:8137/ (or just open `mockup/index.html` directly).

Design read: redesign-overhaul of the Vue 3 + shadcn-vue app toward the
illuminated-manuscript / storybook language defined by the concept images in
this folder. Content, routes, and information architecture are preserved.

Dials: DESIGN_VARIANCE 7 / MOTION_INTENSITY 5 / VISUAL_DENSITY 3.

---

## 1. What the concepts establish (the brand)

Extracted from the 21 concept images:

- **Surface**: warm parchment paper, subtle fiber texture, aged edge vignette.
- **Type**: classic ink serif for everything reader-facing; small-caps serif
  for section labels ("MY LIBRARY", "READER SETTINGS", "WELCOME BACK").
- **Accent**: a single deep burgundy (ribbon / wax-seal red) for CTAs, active
  states, and links. Gold is *ornament only* (hairlines, flourishes, corners),
  never text or buttons.
- **Metaphor**: the open book. Story pages are book spreads; the library is a
  ledger inside the book; auth forms sit on the left page with a watercolor
  illustration on the right page.
- **Buttons**: burgundy "ribbon banner" primary CTA with gold leaf glyph;
  secondary actions are inked text links with arrow or underline.
- **Choices in gameplay**: not web buttons - inked lines with a fleuron
  hairline underneath, the hovered/active one turning burgundy with a small
  arrow marker (see `pages/gameplay.png`). This is the signature interaction.
- **Status language**: stamped small-caps words (IN PROGRESS / COMPLETED /
  ABANDONED) with an underline, like ink stamps in a ledger
  (see `pages/history.png`).
- **Illustrations**: muted watercolor, sage green / sepia / slate blue,
  generated per story (the backend already generates story images).

Palette and serif justification: the beige+burgundy family and serif display
are normally banned defaults, but here they are the explicit brand brief -
every concept image uses them, and the product genuinely is a
manuscript/storybook. Gold-as-ornament-only and a single burgundy accent keep
it away from generic "AI vintage" slop.

---

## 2. Changes to the concept itself ("more beautiful" = translate, don't trace)

The concepts are photographic mockups. Rendering them literally (full-bleed
photos of a desk, 3D book, candle) would be heavy, unresponsive, and would
bury the text contrast. These adjustments keep the soul and fix the craft:

1. **The open book is the interface, literally.** Every in-app page is a real
   book: leather cover with a gilded inner line, two facing parchment pages
   with a shaded centre gutter, stacked page edges, a ribbon bookmark, and
   journal tabs on the fore-edge. It sits on the **desk from the concepts,
   props intact** (quill, inkpot, brass stamp, candle, plant, papers, compass)
   at a light 5px blur: the scene stays readable, the book stays the focus.
   Three backdrops, ~90-100 KB each: `desk-day` (scenario, history, profile),
   `desk-night` (gameplay, quiz), `desk-map` (404). Painted on a fixed,
   composited `body::before` layer, never `background-attachment: fixed`,
   which repaints the whole image on every scroll.

2. **The book spread collapses honestly on mobile.** Two-page spreads become
   a single page with the illustration above the text. No fake miniature
   spread. Breakpoint: `md` (768px).

3. **Contrast discipline.** Concept ink is sometimes low-contrast on the
   aged-paper wash. Tokens below force WCAG AA: body ink ~#2b2118 on
   parchment ~#f4ecd9 (≈9:1), burgundy #7c2128 on parchment (≈7:1), and
   status colors are darkened stamp tones, not tailwind-500 brights.

4. **Kill the remaining slop in concepts.** The gameplay concept's "Prev /
   Next" corners duplicate scroll; drop them (story is a continuous scroll
   with paragraph reveal, which the app already has). Keep "Options" as a
   quiet gear-less text link. Star ratings for difficulty become the
   concept's own "A2 Wayfarer / B1 Storyteller / B2 Chronicler" level cards -
   name + CEFR badge + sample sentence in that register (the scenario view
   already streams per-level scene text; this is a straight mapping).

5. **Dark mode: "candlelit library".** Concepts are light-only. Define a
   second theme now, not later: deep umber surfaces (#221a14 range), warm
   ivory ink, same burgundy shifted lighter (#b0424a) for contrast, gold
   ornaments dimmed. Same texture tile, multiplied. Auto via
   `prefers-color-scheme`, manual toggle later if wanted.

6. **Motion, sparingly (MOTION 5).**
   - Paragraph reveal: soft ink-fade-up (opacity + 8px translate), already a
     natural fit for the existing "Proceed" flow. Rename button "Continue
     reading".
   - Choice select: chosen line gets a burgundy underline draw (SVG stroke),
     others fade. One purposeful moment.
   - Route transitions between game pages: a subtle page-corner fade, NOT a
     full 3D page turn (heavy, gimmicky after the third time).
   - All gated behind `prefers-reduced-motion`.

---

## 3. Design tokens (target `index.css` values)

Keep the shadcn HSL variable contract so every existing `ui/` component picks
the theme up for free. Values below are the light "Reading room" theme and
dark "Candlelit" theme.

| Token | Light (Reading room) | Dark (Candlelit) | Notes |
| --- | --- | --- | --- |
| `--background` | `43 45% 91%` (#f4ecd9 parchment) | `26 24% 11%` (#221a14) | body gets texture tile on top |
| `--foreground` | `30 25% 13%` (#2b2118 ink) | `40 30% 88%` (warm ivory) | |
| `--card` | `45 50% 95%` (#faf5e6 lighter page) | `26 20% 15%` | "page on page" |
| `--muted` | `42 30% 85%` | `26 15% 20%` | |
| `--muted-foreground` | `30 15% 35%` | `40 15% 65%` | AA on background |
| `--primary` | `355 58% 31%` (#7c2128 burgundy) | `355 45% 48%` (#b0424a) | the ONE accent |
| `--primary-foreground` | `45 50% 95%` | `45 50% 95%` | |
| `--secondary` | `42 30% 85%` | `26 15% 20%` | quiet parchment chip |
| `--accent` | same as secondary | same | do NOT add a second hue |
| `--destructive` | `0 60% 38%` | `0 55% 45%` | darker than default |
| `--border` | `38 25% 72%` (#c9b globe faded ink line) | `26 12% 26%` | |
| `--ring` | same as primary | same | focus ring = burgundy |
| `--radius` | `0.375rem` | same | pages are near-square; ribbon CTAs 4-6px |

New non-shadcn additions:

- `--gold: 40 45% 55%` - ornament hairlines, fleurons, corner flourishes
  ONLY. Never text, never fills.
- `--status-progress`, `--status-complete`, `--status-abandoned`: amber-ink
  `#8a6116`, moss-ink `#4a6741`, oxide `#7c2128` - stamp colors for the
  ledger, AA-checked on parchment.
- Shape lock: radius 6px everywhere interactive; illustrations and pages
  0-4px. No pills.

### Typography

Self-hosted via `@fontsource` (no Google `<link>`):

- **Display + headings**: `EB Garamond` (600 for H1/H2, small-caps via
  `font-variant-caps` for eyebrows/labels). Fits the manuscript brand and is
  not on the banned-serif list.
- **Body / story text**: `EB Garamond` 400 at 1.125rem / 1.75 line-height for
  the reading column (max-width 65ch); this is a reading app, the story text
  IS the product.
- **UI micro-copy & forms**: `Inter Tight` or system sans at 0.8125-0.875rem
  for labels, helper text, table meta - serif below ~13px on textured paper
  smears. Two families total, roles locked.
- Numerals in history table: `font-variant-numeric: tabular-nums`.

Eyebrow budget: small-caps labels are already the concept's language
(WELCOME BACK, MY LIBRARY). Cap at one per page, as in the concepts.

### Texture & ornament assets (to produce once)

- `paper-texture.webp` tileable ~512px, opacity ~0.35 overlay.
- `ornament-divider.svg` (the fleuron hairline used everywhere).
- `corner-flourish.svg` (4 rotations by CSS).
- `ribbon-bookmark.svg` (nav active marker / decorative).
- Generated watercolor placeholders for stories without images yet
  (backend image gen already exists; add a neutral "unillustrated page"
  fallback with a pale compass rose).

---

## 4. Component system changes (shared, before any view)

| Component | Change |
| --- | --- |
| `ui/button` | Variants: `ribbon` (primary burgundy, subtle stitched 1px inner border, gold leaf glyph slot, `active:translate-y-px`), `inked` (text + arrow, dotted underline on hover), `outline` restyled to hairline ink. Kill default slate. |
| `ui/card` | Becomes `PageCard`: lighter page surface, hairline border, optional corner flourishes, soft tinted shadow (`shadow-[0_2px_12px_rgb(60_40_20/0.12)]` - never pure black). |
| `ui/input`, `textarea`, `select` | Parchment field: transparent-ish fill, ink hairline border, burgundy focus ring, serif value text. Labels above, helper below (already the shadcn form pattern - keep). |
| `ui/table` | Ledger style: no zebra; single hairline row separators (bottom only), small-caps column heads, generous row height. |
| `ui/dialog` | "Loose page" panel: parchment, hairline frame, drop the default dark overlay for a warm `rgb(40 25 10 / 0.5)` scrim. |
| `ui/toast` | Wax-seal accent bar left, parchment body. |
| **NEW `BookFrame.vue`** | The page/spread chrome: double hairline border, corner flourishes, optional two-column spread with center "gutter" shadow, collapses to single column under `md`. Used by scenario, history, gameplay, profile, quiz. |
| **NEW `OrnamentDivider.vue`** | The fleuron hairline. Replaces `Separator` in reader-facing surfaces. |
| **NEW `StatusStamp.vue`** | Small-caps stamped status with underline (history, scenario recents). |
| **NEW `StoryChoice.vue`** | Replaces `StoryOptions.vue`'s hard-coded gray buttons with the inked-line choice list from `pages/gameplay.png`. Keyboard focus = burgundy ring; hover = burgundy ink + arrow fleuron. |
| `NavBar` | Parchment header strip (like `pages/game-scenario.png`): wordmark in EB Garamond, center links (Stories / How it works / My library), user menu right. Active route marked by a small burgundy ribbon tick under the link. Height ≤ 72px, one line. Mobile sheet becomes a parchment panel. |
| `Footer` | One hairline, three quiet links (© GenQuest / Terms / Privacy), as in `pages/login.png`. |

---

## 5. Route-by-route mapping (current system → new UI)

Legend: 🟢 restyle only · 🟡 restructure markup, keep logic · 🔴 new view/route.

| Route | View (today) | Concept | Level | Work |
| --- | --- | --- | --- | --- |
| `/` | `HomeView.vue` (3 lines of centered text) | `pages/home.png` | 🟡 | Real hero: split layout, left = headline "Every choice writes the next page." + 1-line sub + ribbon CTA "Begin a story" + inked "Explore stories"; right/behind = the generated open-book hero image (from concepts folder or regenerate at web res). `min-h-[100dvh]`, image `fetchpriority=high`. CTA routes to login or `/game` depending on auth. |
| `/auth/login` | `LoginView.vue` (default card) | `pages/login.png` | 🟡 | `AuthLayout` becomes the book spread: left page = form (small-caps eyebrow "WELCOME BACK", H1, fields, ribbon CTA), right page = watercolor illustration (hidden under `md`). Keep vee-validate logic untouched. |
| `/auth/signup` | `SignupView.vue` | `pages/signup.png` | 🟡 | Same spread, different illustration + eyebrow "BEGIN YOUR TALE". |
| `/auth/verify-email`, `forgot-password`, `reset-password`, `password-reset-sent` | 4 views | matching PNGs | 🟢 | Single-page (no spread) parchment card with ornament divider; shared `AuthPage` slot pattern. |
| `/change-password` | `ChangePasswordView.vue` | `pages/change-password.png` | 🟢 | Restyle inside `BookFrame`; concept shows it inside profile sidebar - see profile row below. |
| `/game` | `GameScenarioView.vue` | `pages/game-scenario.png` | 🟡 | Two-page spread: LEFT = "Start Your Adventure" (genre select, details textarea as ruled-paper field, ribbon "Generate scenes"); RIGHT = "Recent stories" list (thumbnail + title + genre + StatusStamp, "View all history →" inked link). Generated scenes section becomes the "Choose your reading level" row: level cards `A2 Wayfarer` / `B1 Storyteller` / `B2 Chronicler` (map from existing per-level scene stream; name by CEFR level, star chars removed) with sample text and "Start at this level →". |
| `/game/:id` | `GamePlayView.vue` | `pages/gameplay.png` | 🟡 | The flagship. Reader column: chapter heading (story title in small-caps eyebrow + H1), story image as tipped-in watercolor plate (hairline frame, no overlay pills), prose in EB Garamond 65ch, paragraph reveal keeps existing logic with ink-fade motion, "Continue reading" as inked centered link. `StoryChoice` list under an "What will you do?" italic line + ornament divider. Lookup popup becomes a small wax-seal "?" button; explanation dialog = loose-page dialog with the selected phrase shown as underlined-in-ink quote. Desktop right rail = "Margin notes" (lookup history) styled as pencil margin notes, not a white card. Remove `bg-white`, `hover:bg-gray-100`, spinner circles → replace with quill/ink-line loading (three fading dots + "The ink is drying…" style copy, matching game-loading concept language). |
| `/game/:id/loading` | — (loading is inline today) | `pages/game-loading.png` | 🔴 | Built in the mockup as `game-loading.html`: card on the closed book, story plates tipped in, rotating tips, compass + progress rail, Start Game ribbon enabled only when generation completes. Needs a route, or can be kept inline using the same markup while the story initialises. |
| `/game/:id/quiz` | — (doesn't exist) | `pages/vocabulary-review.png` | 🔴 | New `GameQuizView.vue` + route + backend endpoints (quiz generation & scoring from lookup history). Spread: left = looked-up expressions with context + explanation textareas; right = submit + results ledger (Correct 1 / Partial 0.5 rows). Phase 2 feature - UI shell can ship with the redesign, gated on backend readiness. |
| `/history` | `HistoryView.vue` (DataTable) | `pages/history.png` | 🟡 | Ledger inside `BookFrame`: eyebrow "MY LIBRARY", H1 "Game History", ribbon "+ New Game" right. TanStack table restyled: thumbnail cell (story image, hairline frame), title serif, StatusStamp, tabular-nums dates, row hover = pale wash + arrow; active/latest row may carry the concept's highlight wash. Pagination as quiet Previous/Next inked buttons. |
| `/profile` | — (only change-password exists) | `pages/profile.png` | 🔴 | New `ProfileView.vue` + route (auth-required): left sidebar (avatar roundel, "N's Library", nav: Profile / Reading preferences / Change password / Sign out), right = settings page (explanation-language select exists in backend? verify; otherwise ship with available user fields). Fold `ChangePasswordView` in as a sidebar section OR keep route and reuse sidebar shell. |
| `/terms`, `/privacy` | 2 views | `terms.png`, `privacy.png` | 🟢 | `prose` on parchment inside a single page frame; typography plugin restyled to serif. |
| `*` 404 | `NotFoundView.vue` | `pages/not-found.png` | 🟢 | Eyebrow "LOST BETWEEN CHAPTERS", giant burgundy 404 in EB Garamond, "This path seems to have slipped out of the story.", ribbon "Return Home" + inked "Go back". Map illustration optional (reuse a generated map image). |

Nav label note (concept vs today): concept nav says "Stories / How it works /
My library". Today's nav is "Game / Admin". Mapping: "Stories" → `/game`,
"My library" → `/history`. "How it works" has no page yet - omit until one
exists (do NOT ship a dead link). "Admin" link moves into the user dropdown.
Route slugs stay unchanged (Section 11.F preservation).

---

## 5b. Product decisions taken during mockup review

These came out of reviewing the mockup and override earlier assumptions.
They need backend/route work, not just styling:

1. **No signup.** `/auth/signup` and `SignupView.vue` are removed, along with
   every "Don't have an account?" link. Accounts are provisioned, not
   self-served. `requiresGuest` routes shrink to login + password reset.
2. **Home has one CTA.** "Begin a story" only. The "Explore stories" link is
   gone (it duplicated Stories in the nav and pointed at an auth-gated page).
3. **Genre list is incomplete today, and themes do not exist.**
   - Genre: full list, grouped `Main genres` / `Sub-genres` / `Other (write
     your own)`. The mockup ships 12 + 20; the real list comes from
     `GameService.getScenarios()`, so the backend `GameScenario` table needs
     seeding to that depth.
   - **Themes: a new field.** Multi-select chips (Secrets, Betrayal,
     Redemption, Survival, Discovery, Sacrifice, Identity, Homecoming, ...),
     optional, several allowed. Needs: a `theme` category (or a new model),
     an API field, and inclusion in the story-generation prompt. Flagged as
     backend work.
4. **Reading levels: 6, and auto-expanding.** A1 Novice, A2 Wayfarer,
   B1 Storyteller (recommended), B2 Chronicler, C1 Loremaster, C2 Archivist.
   The grid is `repeat(auto-fit, minmax(230px, 1fr))` and renders from the
   streamed array, so it takes however many levels the backend sends. No code
   change needed to add or drop a level; only the scenario stream changes.
5. **Story pagination: the illustration is per beat, not per page.**
   A *beat* = one illustration + however many text pages that scene runs to.
   `Prev` / `Next` turn text pages **within** the beat and never touch the
   art. The illustration changes only when a choice advances the story, and
   choices only appear on a beat's last page (so `Next` is disabled there:
   moving on is the choices' job). Maps onto the existing
   `StoryProgress` entries: one entry = one beat = one `image_url`, and the
   current `splitIntoParagraphs` + `currentParagraphIndex` logic becomes page
   turns instead of an inline "Proceed" button.
6. **Lookups are stored, and the quiz is built from them.** See 5c.
7. **Quiz is gated behind the ending.** No "Vocabulary review" tab or link
   exists mid-story; it appears in the end-of-story block only
   (`is_end_point` / `status === 'COMPLETED'`). The Library tab is gone from
   the book entirely (the nav already goes there).

## 5b-ii. Fidelity notes taken from a close read of the concepts

The concepts carry detail that a first pass loses. Specifically:

- **Ornate gold frame.** Pages and laid sheets carry a gold double hairline
  with a leafy flourish in each corner. The flourish is lifted from the
  concepts and stored as a transparent gold PNG in four rotations
  (`corner-tl/tr/br/bl.png`), so it composites on parchment and on the dark
  page without blend-mode tricks.
- **Eyebrows are serif, not sans.** `MY LIBRARY`, `WELCOME BACK`,
  `RECOVER YOUR KEY`, `YOUR DATA` are letterspaced serif caps in burgundy.
- **Dividers** are a gold hairline with a burgundy diamond at the centre,
  not a `❦` glyph.
- **The desk keeps its props.** Quill and pen in a brass inkpot, brass stamp,
  leather books, plant, compass on a map, loose papers. Built from the
  concepts' prop columns only (the render's own book and navbar cropped out),
  so no ghost book sits behind the real one. The book is sized to the
  concepts' ~81% of frame so the props stay visible either side.
- **Auth pages are a single deckle sheet laid on a closed book**, not a
  spread: form on the left of the sheet, illustration on the right, hairline
  rule between them.
- **Legal pages have their own shapes.** Terms: contents on the left page
  with the active chapter on a notched burgundy ribbon, document on the
  right, reading progress down the fore-edge. Privacy: one wide page, filofax
  tabs down the edge, a plain-language summary callout, padlock engraving.
- **Loading**: the card sits on the closed book with the story's first plates
  tipped in above it, a rotating tip carousel, a compass and a progress rail,
  and a Start Game ribbon that only enables when generation finishes.

## 5c. The lookup: storage and behaviour (the core interaction)

The query function is the product. Full loop, as built in the mockup:

1. Reader highlights any phrase in the story text.
2. A burgundy wax-seal **"?"** appears just above the selection.
3. Clicking it opens a loose-page dialog: the phrase, the **sentence it sits
   in** (extracted around the selection, mirroring the existing
   `extractSentenceFromRange`), and the explanation streaming in word by word
   with a caret, the way the websocket delivers it today.
4. The phrase is **underlined with a burgundy dotted line in the story text**
   and stays that way. Clicking an underlined phrase reopens its saved
   explanation, no refetch.
5. It is **saved**, and survives reload. The **notebook** is a drawer fixed to
   the right of the reader, **open by default**; its leather tab carries a live
   count, toggles it, and the choice is remembered. It rolls (scrolls) through
   everything queried in this story, each row reopening the explanation, with
   a × to delete (which also removes the underline). Above 1200px the book
   slides over to make room; below that the notebook overlays.
6. At the ending, the **Vocabulary review** is generated from exactly those
   saved phrases, each with its stored context sentence.

Mapping to the app: the mockup's `GQNotes` store (localStorage) stands in for
`ExplanationService.getLookupHistory(storyId)` plus the `TextExplanation`
records the backend already creates. The persistence and dotted-underline
restore are the new parts: on load, saved phrases are re-marked in the text.
The quiz needs backend endpoints to generate and score from lookup history.

## 6. Implementation phases (when execution is approved)

1. **Foundation** - fonts (@fontsource EB Garamond + Inter Tight), tokens in
   `index.css` (both themes), texture/ornament assets, tailwind config
   (fontFamily, gold + status colors).
2. **Primitives** - button variants, PageCard, inputs, table, dialog, toast,
   OrnamentDivider, StatusStamp, BookFrame.
3. **Chrome** - NavBar, Footer, BaseLayout (paper background), AuthLayout
   (book spread).
4. **Quick-win pages** - Home hero, 404, auth pages, terms/privacy. App
   already looks redesigned after this phase.
5. **Library** - GameScenarioView spread + level cards, HistoryView ledger.
6. **Reader** - GamePlayView (StoryChoice, margin notes, lookup dialog,
   loading states, motion). Highest risk: touches websocket-driven DOM;
   keep all script logic untouched, template-only surgery.
7. **New routes** - ProfileView, GameQuizView shell, optional GameLoadingView
   (needs product/backend decisions flagged above).
8. **Polish pass** - dark mode audit in both themes, reduced-motion audit,
   Lighthouse (texture tile + hero image budget), contrast spot-checks,
   mobile spread collapse on every page.

Estimated blast radius: ~10 `ui/` component files, 2 layouts, 2 shared
components (NavBar/Footer), 14 views restyled, 2-3 new views, zero service /
store / router-guard logic changes (router gains 2-3 route entries only).

---

## 7. Pre-flight self-check (concept-level)

- One theme per page, two themes total, tokenized. ✓
- One accent (burgundy) locked page-wide; gold = ornament only. ✓
- Shape lock: 6px interactive, hairline frames. ✓
- Serif justified by brand; not Fraunces/Instrument Serif. ✓
- Warm palette justified by explicit brand brief (concept images). ✓
- Real images (existing story-image pipeline + concept hero); no div-based
  fake screenshots; illustrations generated, not hand-rolled SVG art. ✓
- Motion motivated: paragraph reveal (storytelling), choice underline
  (feedback), page fade (state transition); all reduced-motion gated. ✓
- No em-dashes anywhere in shipped copy. ✓
- Status dots: none; statuses are stamped words. ✓
- Concept's "Prev/Next" duplication removed; scroll cues: none. ✓
