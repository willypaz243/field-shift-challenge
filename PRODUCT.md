# Product — Choclito

<!-- impeccable:product-schema 1 -->

## Platform

adaptive

## Stack

App: Expo (React Native + TypeScript) in `app/`, one codebase for Android and web. API: FastAPI + SQLModel + SQLite modular monolith in `api/`. Full stack in `README.md`. Reference mockups: static HTML/CSS in `mockups/` (also in Figma).

## Users

Small farmers in the peri-urban zones of Cercado, Cochabamba (main pilot: District 9 Itocta and District 15 Tamborada). They grow maize (corn and fodder), alfalfa, oats, broad beans, potatoes and vegetables, on plots irrigated by La Angostura, Misicuni, wells or wastewater, or rainfed only.
- Phone: low-end Android, small screen, limited data, often no signal in the field.
- Reading: little. They read short phrases and prefer icons and audio.
- Language: Spanish and Quechua from the first version.
- Job: decide when to irrigate and what to plant next, protect crops from frost, hail, drought and flooding, and report what happens on their plot.

Secondary audience (unconfirmed): GAMC technicians and farmer union leaders who look at the zone's reports.

## Product Purpose

A farmer-first decision-support tool (DSS) built for the NASA Space Apps Challenge 2026 "Field Shift: Adapting Farms with NASA Data", local GAMC Cochabamba focus (Agrotechnology and Water Management). It turns NASA data (SMAP soil moisture, GPM/IMERG rain, POWER climate, MODIS/Sentinel NDVI) together with soil data, crop data (FAO-56 Kc, frost and drought tolerance) and the farmer's priorities into direct, per-plot actions:
- when to irrigate;
- frost, drought or heavy-rain alerts 1 to 2 weeks ahead;
- 7- and 14-day weather forecast;
- a comparison of at least 3 rotations, including the current one.

Success: the farmer acts (irrigates, covers the crop, picks a plan, reports) in as few taps as possible, and trusts the recommendation without needing technical knowledge.

## Positioning

It joins satellite data with farmer reports from the same zone (water that didn't arrive, hail, frost, flooding). Neighbors' reports show where the irrigation system failed, and the past local history (Rocha River floods, La Angostura dam levels) puts the forecast in context. It works without signal and queues reports until signal returns.

## Operating Context

- Used outdoors in direct sun, often with dirty or wet hands, standing in the field.
- Two growing seasons:
  - Main season: sown Sep–Nov, harvested Feb–May.
  - Short "mishka" season: sown Mar–Apr, irrigation required.
- Frost: May–Aug. Hail and floods: Dec–Mar. 2026–27 is an El Niño year, with drought expected in the valleys.
- Irrigation runs in turns from the La Angostura dam and the Misicuni project. Dam levels and canal overflows set when water is available.
- Background: `docs/CONTEXTO-LOCAL.md`, `docs/CHALLENGE.md`, `docs/DATA-SOURCES.md`.
- GAMC data: WMS layers for peri-urban zones, drainage and districts (`docs/DATA-SOURCES.md`).

## Capabilities and Constraints

- Screens (see `docs/FLUJO-APP.md`):
  1. Locate plot (GPS) and water source + main goal
  2. Hoy (today's weather, alerts, my crops)
  3. Calendario (4 weeks, past weeks, next months, harvest and sowing events)
  4. Sembrar (crops, best sowing date)
  5. ¿Qué sembrar después? (current rotation vs. at least 3 alternatives)
  6. Mi zona (map, report a problem, history)
  7. Avisos (alerts and harvest reminders)
- Fewest taps possible: key actions take 1 tap and choosing a plan takes 2. No "Save" step: tapping an option saves it.
- Offline-first: cached data with a "data from HH:MM" note; reports go into a queue.
- Location by GPS on the phone. IP location is a fallback.
- Notifications 1 to 2 weeks before an event.
- Recommendations are support only. They always remind the farmer to consult a technician or their union.
- The 4-tab nav (Hoy, Calendario, Sembrar, Mi zona) is confirmed.
- Undecided: short-range forecast source, Quechua audio recordings.

## Brand Commitments

- Context: NASA Space Apps Cochabamba 2026 and GAMC (Gobierno Autónomo Municipal de Cochabamba).
- The user asked for a light, professional green-and-white theme for farmers.
- Figma reference: `31yuIJWCMMsIUDCPhw9Jov`, page "Mockups Choclito v2". Visual system in `DESIGN.md`.

## Evidence on Hand

- Real local events with dates and sources in `docs/CONTEXTO-LOCAL.md`:
  - 10 Mar 2024 flood, Valverde canal;
  - La Angostura at 18% capacity, Jul 2024;
  - 26 Nov 2018 hailstorm;
  - drought alert, Oct 2026.
- NASA POWER climatology for District 9.
- FAO-56 Kc values.

Do not invent: farmer names presented as real, testimonials, yield figures, or seed prices. There is no official price table yet.

## Product Principles

1. One screen, one decision: the most important action is visible without scrolling and takes 1 tap.
2. Icon + word + color with a fixed meaning (water, frost, drought, no water), never color alone.
3. Works without signal; always says how old the data is.
4. Supports, does not replace: show the reason for each recommendation and remind the farmer to consult a technician or their union.
5. Language a farmer uses ("riega el martes"), not technical terms; Spanish and Quechua from the start.

## Accessibility & Inclusion

- Low literacy: short text, clear icons, audio playback of the main message.
- Legible in sunlight: high contrast (WCAG AA minimum, aim for AAA on main text), body text 17px or larger.
- Touch targets of 56px or larger; usable with one hand.
- Quechua runs longer than Spanish, so layouts must handle long text without breaking.
- Low-end phones: light on resources, no heavy effects.
