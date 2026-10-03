# Day 06 responsive QA report (Person C)

**What was tested.** A production build in mock mode (the layout components are the same in live mode), in headless Chromium, at 360, 768 and 1440 px. Eight states each: empty, loading, normal result, flagged result, cached demo, validation error, service error, and the chat with a result card. That is 24 checks.

**What each check measured.** Horizontal page overflow; any visible element that extends past the viewport edge; any interactive element shorter than 44 px; any visible text smaller than 12 px; browser console errors.

| Result | Value |
|---|---|
| Checks run | 24 (8 states × 3 widths) |
| Horizontal overflow | None |
| Elements outside the viewport | None |
| Tap targets under 44 px | None |
| Text under 12 px | None |
| Console errors | None |

**Looked at by eye.** 360 px (result, chat), 768 px (full page with a flagged result), 1440 px (full page).

**Not covered (needs a person).**
- Real phones and other browsers (Safari, Firefox). Only headless Chromium was used.
- Keyboard walk with Tab and screen readers. Programmatic checks only confirm labels and focus handling, not the real experience.
- Live-mode screens with the real backend. Layout is shared, but the real response text was not seen.
- Visual review of the loading, validation-error and service-error screens at 768 px (measured, not viewed).

**Fixes needed.** None found.

## Demo assets
11 screenshots were captured in mock mode and saved in `docs/demo/` (see `docs/demo/README.md` for what each shows and which should be recaptured from the real backend). No screen recording was made. A recording needs a person: follow `docs/demo-script.md` with a screen recorder.
