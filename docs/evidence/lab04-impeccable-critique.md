# Impeccable Critique — Lab 04 CE Amplifier Simulator

- **Target:** `templates/index.html` rendered at <http://127.0.0.1:5000/>
- **Surface mode:** Operate (engineering tool for EE students)
- **Method:** dual-agent (A: `ses_df2c9fe42ffebEzYlD2OZfH7mn` · B: `ses_df2c9fe41ffeSF2pAfNoz34zHv`)
- **Tooling:** Impeccable skill v4.10.0 (project install) + bundled detector + Playwright MCP
- **Date:** 2026-11-24

## Design Health Score (Assessment A)

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of System Status | 3 | Status and run id are clear; no progress indicator for a multi-second run |
| 2 | Match System / Real World | 3 | EE units match; no schematic or node map |
| 3 | User Control and Freedom | 2 | No reset/undo; mode switch is a one-way submit |
| 4 | Consistency and Standards | 2 | Two dropdowns commit differently; some token drift |
| 5 | Error Prevention | 2 | Free-text numeric inputs; invalid RE caught only after submit |
| 6 | Recognition Rather Than Recall | 2 | Two forms require retyping the same circuit |
| 7 | Flexibility and Efficiency | 1 | Enter does nothing in the simulator; no URL state |
| 8 | Aesthetic and Minimalist Design | 3 | Calm layout; duplicate provenance line and raw chart ticks |
| 9 | Error Recovery | 3 | Exact Thai error, stale charts hidden; error was far from the field |
| 10 | Help and Documentation | 2 | Good chart notes; no in-app glossary |
| **Total** | | **23/40** | Moderate-good engineering utility |

## Design Specificity Verdict

**Content-specific, structurally generic.** The substance is genuinely this
project: real ngspice runs, engine/model/run-id provenance, `.op/.ac/.tran`,
Thai-first copy, and region badges. The structure is still a single-column form
card that could host any calculator; the engineering identity lives mostly in
text rather than in a schematic or node map.

## Deterministic Scan (Assessment B)

| Scan | Result |
|---|---|
| `detect --json templates/index.html` | 1 `flat-type-hierarchy` warning — **false positive**: the detector cannot resolve Jinja `url_for()` for the stylesheet, so it measures unstyled 16/16/16 defaults instead of the rendered 24/18.4/16 px hierarchy |
| `detect --json http://127.0.0.1:5000/` (1280 px) | `[]` — no findings |
| `detect --json --viewport 390x844 http://127.0.0.1:5000/` | `[]` — no findings |
| Browser console | 0 errors, 0 warnings before/after all interactions |
| Horizontal overflow | none at 1280×900 or 390×844 |

Evidence files: `lab04-impeccable-before.txt`, `lab04-impeccable-after.txt`,
`lab04-impeccable-source.json`, `lab04-impeccable-url-desktop.json`,
`lab04-impeccable-url-mobile.json`.

## Priority Issues and Resolution

| Severity | Issue | Resolution | Evidence |
|---|---|---|---|
| P1 | Transient x-axis showed raw JS floats (`0.3464000000000004`, …) | Added a label-aware `formatTimeTick` (`timeMs[index].toFixed(2)`) and `maxTicksLimit`; ticks now `0.00, 0.69, …` ms | `lab04-impeccable-before-tran.png` → `lab04-b5-tran-playwright.png` |
| P1 | AC log-axis labels collided at the right edge | Added `formatLogTick` (10/100/1k/10k/100k/1M) and responsive `maxTicksLimit` | `lab04-impeccable-before-ac.png` → `lab04-b4-ac-playwright.png` |
| P2 | Mobile `เปลี่ยนโหมด` button wrapped to 3 lines | Stacked the mode bar below 560 px; button is now 309×47.6 px, one line | `lab04-impeccable-before-mobile.png` → `lab04-b8-mobile-playwright.png` |
| P2 | Errors were detached from the field and not announced | Added `aria-live="polite"` to status, `aria-invalid` + focus on the failing input, and a red invalid style | `lab04-impeccable-before-error.png` → `lab04-b7-invalid-playwright.png` |
| P2 | Canvas charts had no text alternative | Added `role="img"` and a data-derived `aria-label` (point count, min/max) to both canvases | `lab04-b4-ac-playwright.png`, `lab04-b5-tran-playwright.png` |
| P2 | Simulator `.op` table used `th` without `thead`/`scope` | Added `thead`, `tbody`, and `scope="col"` | `templates/index.html` |
| P3 | Mobile h1 wrapped with a short last line | Added `text-wrap: balance` | `lab04-b8-mobile-playwright.png` |
| P3 | Simulator select used a different border/radius token | Unified with the mode select (`--line`, 6 px) | `static/style.css` |
| P3 | Mixed Thai/English failure phrase and “analytical” | Changed to `การจำลองล้มเหลว` and `ผลคำนวณเชิงวิเคราะห์` | `static/app.js`, `templates/index.html` |

## Issues Still Unresolved (honest scope)

1. **No schematic or node map.** A circuit drawing would be a valuable next
   step, but it is outside the v1 scope in the handout. The UI names the
   reference circuit and every node value explicitly.
2. **The analytical form and the SPICE form are separate.** This is intentional:
   Lab 03 remains a regression surface, and Lab 04 simulates one fixed CE
   Voltage Divider reference circuit. The simulator labels itself as a separate
   reference circuit; a future version could copy values across forms.
3. **Changing the Lab 03 bias mode still resets typed inputs.** This is the
   existing Lab 03 behavior and was deliberately preserved to avoid changing
   the graded regression flow.
4. **Charts are canvas-only.** They now expose a text alternative via
   `aria-label`, but there is no full data table. The underlying values are
   still available from the ngspice run and the API.
5. **`Engine`, `Model`, and `Run` labels remain English.** The handout explicitly
   asks for “Model และ Run Status”; these are technical provenance labels, while
   the surrounding explanations are Thai.
6. **Desktop content stays in a 720 px card.** This keeps line length and chart
   readability stable; it is a deliberate reading-first choice, not a missing
   responsive layout.

## Verification After Fixes

- `python -m unittest discover -s tests -v` → **Ran 57 tests, OK**
- Playwright post-fix checks:
  - AC ticks: `10, 100, 1k, 10k, 100k, 1M`
  - Transient ticks: `0.00, 0.69, 1.41, …` ms (no float noise; uses the real time labels, not point indices)
  - Invalid RE=0: status `การจำลองล้มเหลว`, error `RE ต้องมีค่ามากกว่า 0`,
    `aria-invalid="true"`, focus on `#sim-re`, all SPICE result panels hidden
  - Mobile 390 px: `scrollWidth 375`, no horizontal overflow; mode button 309×47.6 px
  - Desktop 1280 px: `scrollWidth 1265`, no horizontal overflow
