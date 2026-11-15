# SKILLS.md

Agent skills recommended for this repo. Install them with the [skills CLI](https://skills.sh/) (`npx skills add <source>`), then invoke them by name in your agent (for example `/impeccable`).

| Skill | Use it for | Works with React Native / Expo |
|---|---|---|
| [`pair`](https://github.com/nschurmann/hola-ai/blob/main/skills/pair/SKILL.md) | Implementing an issue test-first | Yes (stack independent) |
| [`impeccable`](https://github.com/pbakaus/impeccable) | Design critique, audit and polish of screens | Yes (has iOS/Android guidance) |

## pair

```
npx skills add nschurmann/hola-ai@pair
```

- Pair programming on one issue: the agent writes one test, shows it failing, writes the minimum code, shows it passing, and stops for your go-ahead.
- Start from the issue's acceptance criteria. Approve the test list before any code is written.
- It never commits; you commit following `AGENTS.md`.
- Good fit for: API modules (`router → service → repository`), the window scoring function, sync logic.

## impeccable

```
npx skills add pbakaus/impeccable
```

- Commands we use: `critique` (UX review), `audit` (accessibility, performance, touch targets), `polish` (final pass), `adapt` (screen sizes).
- For the Expo app it switches to its native references (`audit.native.md`, `adapt.native.md`, Android/iOS guidance). `PRODUCT.md` already sets `Platform: adaptive`.
- It reads `PRODUCT.md` (product context) and `DESIGN.md` (visual system) from the repo root.
- Use it on every new screen before opening the PR, and attach the findings you fixed.

Motion values (durations, easing, press scale) are already in `DESIGN.md`, so no animation skill is needed.
