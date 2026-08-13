# TalentLens AI — Design Notes

## Direction
A recruiter-facing SaaS tool, not a marketing page or an "AI toy" — closer
in spirit to Linear/Ashby/Greenhouse than to a chatbot UI. Data-dense,
confident, low-ornamentation, with exactly one deliberate signature motif
rather than decoration scattered everywhere.

## The signature element: the aperture ring
The product's whole premise is "focus in on the right candidate," so the
match-score visualization (`components/common/ScoreRing.tsx`) is built as
a set of aperture blades that close in around the score, rather than a
generic donut/pie chart. The same blade motif appears at 1/8th scale as
the wordmark icon in the sidebar and login screen. This is the one motif
repeated across the product — it isn't diluted by using a different chart
style elsewhere.

## Color
Deliberately avoids the two generic-AI-app defaults (warm cream+terracotta,
or near-black+neon). Cool neutral base instead:

| Token | Hex | Use |
|---|---|---|
| `paper` | `#F5F6F8` | App background |
| `paperRaised` | `#FFFFFF` | Cards, inputs |
| `ink` | `#14151F` | Primary text (near-black w/ faint blue-violet undertone, not pure black) |
| `ink-soft` / `ink-faint` | `#3A3C4C` / `#6C6E82` | Secondary/tertiary text |
| `line` | `#E3E5EB` | Borders, dividers |
| `lens` | `#3B2FA3` | Brand/primary accent — deeper and more saturated than a default Tailwind indigo |
| `sage` | `#3F7159` | Positive/strong-match signal |
| `amber` | `#C98A2C` | Moderate/attention signal |
| `clay` | `#B65C43` | Gap/missing signal — muted, never used as a large fill |

Semantic accents (`sage`/`amber`/`clay`) appear only in small doses —
badges, score-ring color, thin progress bars — never as backgrounds or
large blocks, so the product doesn't read as "traffic-light UI."

## Typography
Three-family system: a display serif for page titles and empty-state
headlines (restrained use — this is a data tool, not an editorial site), a
grotesque sans for all UI chrome and body text, and a monospace for every
number that represents a score, percentage, or year count, so numeric data
has a consistent rhythm distinct from prose.

**Current limitation:** this sandbox has no network access to Google
Fonts, so `tailwind.config.js` currently falls back to system font stacks
(`ui-serif`/`Georgia`, system sans, `ui-monospace`) that approximate the
intended feel. In a real deployment, swap these for `next/font/google`
with **Fraunces** (display), **Inter** (sans), and **IBM Plex Mono**
(mono) — a one-line change per font, see the `fontFamily` block in
`tailwind.config.js`.

## What to extend next
- Recharts is installed but not yet used — the Analytics page (section 49)
  is intentionally left minimal rather than shipping fake charts; wire up
  score-distribution and skill-gap charts once there's real match data to
  chart against a live embedding model.
- Blind-screening mode (section 73) has a settings-page placeholder but no
  backend toggle yet — see PROGRESS.md.
