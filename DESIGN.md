---
name: Choclito
description: Farmer-first decision support for Cochabamba's valley, readable in direct sun.
colors:
  field: "#1B6E3A"
  field-deep: "#145730"
  field-soft: "#E8F3EA"
  field-line: "#B9D9C1"
  paper: "#FFFFFF"
  paper-2: "#F4F7F3"
  line: "#E1E8E0"
  ink: "#13261A"
  ink-2: "#33463A"
  corn-gold: "#C9A227"
  water: "#1C63B7"
  water-soft: "#E8F0FB"
  frost: "#0B6E8A"
  frost-soft: "#E2F3F7"
  dry: "#8F5200"
  dry-soft: "#FFF3DC"
  nowater: "#B42318"
  nowater-soft: "#FDECEA"
typography:
  headline:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 600
    lineHeight: 1.3
  meta:
    fontFamily: "Atkinson Hyperlegible Next, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.3
rounded:
  btn: "14px"
  card: "16px"
  sheet: "24px"
  pill: "999px"
spacing:
  gutter: "16px"
  section: "16px"
  card-pad: "16px"
components:
  button-primary:
    backgroundColor: "{colors.field}"
    textColor: "{colors.paper}"
    rounded: "{rounded.btn}"
    height: "60px"
  button-primary-active:
    backgroundColor: "{colors.field-deep}"
  button-secondary:
    backgroundColor: "{colors.field-soft}"
    textColor: "{colors.field-deep}"
    rounded: "{rounded.btn}"
    height: "60px"
  card:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.card}"
    padding: "16px"
  chip-selected:
    backgroundColor: "{colors.field}"
    textColor: "{colors.paper}"
    rounded: "{rounded.pill}"
    height: "56px"
  nav-tab-active:
    backgroundColor: "{colors.field-soft}"
    textColor: "{colors.field}"
  alert-frost:
    backgroundColor: "{colors.frost-soft}"
    textColor: "{colors.frost}"
    rounded: "{rounded.btn}"
  toast:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.btn}"
---

# Design System: Choclito

Extracted from the approved HTML mockups (`mockups/app.css`). The Expo app reproduces these tokens in a theme file.

## Overview

**Creative North Star: "The Field Almanac"**

A white page you can read standing in a field at noon. Mostly white for sunlight legibility, with green only where something can be tapped or is selected. Each screen answers one question with one main action, in large type and short words for farmers who read little.

Weather and risk are never shown by color alone: every state is icon + word + color, always the same pairing (water blue, frost teal, drought amber, no-water red). Data is shown as words ("lluvia débil", "Helada") in lists; numbers live inside the detail sheets.

**Key Characteristics:**
- White surfaces, thin borders, no shadows on cards.
- One green accent; status colors only for weather and risk.
- Large text (body 19 px, never below 15 px) and large targets (≥ 56 px).
- Bottom sheets for detail; four-tab bottom navigation.
- Offline-first copy: "actualizado + date", never "sin señal".

## Colors

A white-and-field-green palette with a fixed set of status colors.

### Primary
- **Field Green** (`field`): primary buttons, selected chips and days, active tab label, links. The only action color.
- **Deep Field** (`field-deep`): pressed primary, text on light green, brand wordmark.
- **Sprout Tint** (`field-soft`): secondary buttons, active tab pill, cosecha/siembra tiles, good-day fills.
- **Furrow Line** (`field-line`): borders on green-tinted elements.

### Secondary
- **Corn Gold** (`corn-gold`): the corn logo and harvest markers in the sowing calendar only.

### Status (fixed meaning)
- **River Blue** (`water`, `water-soft`): rain, irrigation, flooding.
- **Frost Teal** (`frost`, `frost-soft`): frost alerts and frost days.
- **Dry Amber** (`dry`, `dry-soft`): drought, "con cuidado", warnings to review with a technician.
- **No-Water Red** (`nowater`, `nowater-soft`): water that did not arrive, bad days, notification badge.

### Neutral
- **Paper** (`paper`): page and card background.
- **Mist** (`paper-2`): neutral tiles, round icon buttons, disabled buttons.
- **Hairline** (`line`): card borders and row dividers.
- **Soil Ink** (`ink`): main text, toast background.
- **Soil Ink Soft** (`ink-2`): secondary text and metadata.

**The Green Means Tap Rule.** Field green marks what is interactive or selected. Never use it as decoration.

**The Same Meaning Rule.** A status color always comes with its icon and word, and always means the same thing on every screen.

## Typography

**Body Font:** Atkinson Hyperlegible Next (with system-ui, sans-serif). Weights 400–700.

**Character:** A typeface designed for low vision, with open shapes and unambiguous letters and digits; it reads well in glare. Digits use tabular figures.

### Hierarchy
- **Headline** (700, 26 px, 1.15): one screen title.
- **Title** (700, 20 px, 1.2): section titles and sheet titles (sheet titles may go to 26 px).
- **Body** (400, 19 px, 1.45): main text.
- **Label** (600, 17 px): buttons use 18 px; chips, rows and secondary lines 17 px.
- **Meta** (600, 15 px): "actualizado" line, dates in lists, data source lines. Nothing smaller except the badge count.

**The 15 Pixel Floor Rule.** No readable text below 15 px. Day numbers, temperatures and dates use larger sizes, not smaller.

## Layout

- Single column, max width 430 px, 16 px side gutter, 16 px between sections.
- Header: brand or back link, zone + "actualizado" line, bell, language switch.
- Fixed bottom navigation with four tabs: Hoy, Calendario, Sembrar, Mi zona.
- Primary actions sit at the bottom of the content or fixed above the navigation.
- Lists are cards with full-width rows: a 92 px tile on the left (icon + word), text on the right, chevron when tappable.
- The most important content fits in a 390 × 844 screen without scrolling.

## Elevation & Depth

Flat. Cards are white with a 1 px hairline border and no shadow. Depth comes from overlays only: bottom sheets over a dark scrim (ink at 45 %) and the toast above the navigation.

**The Flat Card Rule.** Cards never get shadows; separate them with borders and spacing.

## Shapes

- Buttons and inline alerts: gently rounded (14 px).
- Cards and lists: 16 px.
- Bottom sheets: 24 px top corners with a grab handle.
- Chips, tab pills, language switch, badges: fully rounded.
- Selected days in the sowing calendar are rounded squares (11 px); other days are circles.

## Components

### Buttons
- **Primary:** field green, white text, 60 px tall, full width. Pressed: deep field and scale to 0.97.
- **Secondary:** sprout tint with deep field text, same size. Never an outlined button.
- **Disabled:** mist background, soft ink text.
- **Motion:** press feedback 140 ms, strong ease-out (`cubic-bezier(0.23, 1, 0.32, 1)`). In React Native use `react-native-reanimated` with the same curve.

### Chips and choice tiles
- **Style:** white, hairline border, fully rounded, ≥ 48 px tall (56 px for main choices).
- **Selected:** field green fill and white text. A tap saves; there is no Save button.

### Cards / Containers
- **Corner Style:** 16 px.
- **Background:** paper with hairline border; the current week or item may use sprout tint.
- **Internal Padding:** 14–16 px.

### Navigation
- **Tabs:** icon above a 16 px label in soft ink. Active: field green label and a sprout-tint pill behind the icon.
- **Header bell:** round mist button with a red count badge.

### Bottom Sheet
- **Use:** every detail view (week forecast, crop calendar, rotation plan, report, history, harvest question).
- **Shape:** 24 px top corners, grab handle, title row with a 56 px round close button.
- **Motion:** enters from the bottom in 320 ms with the drawer curve (`cubic-bezier(0.32, 0.72, 0, 1)`); scrim fades in. With reduced motion, no slide.
- **Footer:** a one-line data source in meta style ("Datos: NASA POWER e IMERG").

### Alerts and toasts
- **Alert strip:** status tint background, status icon, one bold line, chevron. Frost uses frost teal.
- **Toast:** soil ink background, white 18 px text, close button, above the navigation, visible 7 s.

## Do's and Don'ts

### Do:
- **Do** pair every status with icon + word + color.
- **Do** keep one main action per screen and make it 60 px tall.
- **Do** write short, plain Spanish: "lluvia débil", not "precipitación baja".
- **Do** show the data source in sheets and "actualizado + date" in the header.

### Don't:
- **Don't** put temperatures or numbers in list tiles; keep them for the detail sheet.
- **Don't** use green for decoration or status colors without their icon.
- **Don't** add shadows to cards or use outlined secondary buttons.
- **Don't** use emojis or diminutives in UI text.
- **Don't** say "sin señal"; say when the data was last updated.
