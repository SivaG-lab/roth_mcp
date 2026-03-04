---
name: stitch-ui-design
description: >
  Expert guide for crafting prompts for Google Stitch AI UI design tool.
  Covers prompt structure, iteration strategies, platform targeting, and
  design-to-code workflows. Use when creating Stitch prompts, generating
  UI mockups with Stitch, or integrating Stitch output into development.
  Triggers: stitch, google stitch, stitch prompt, stitch design, stitch UI,
  ai ui generator, stitch mockup, gemini stitch.
user-invokable: true
argument-hint: "<design brief or keywords>"
---

# Stitch UI Design — Prompt Crafting Guide

Google Stitch is an experimental AI UI generator powered by Gemini. It takes natural-language prompts and outputs multi-screen UI designs with HTML/CSS export.

## When to Use

- Crafting prompts for Google Stitch (stitch.withgoogle.com)
- Generating UI mockups, wireframes, or prototypes with AI
- Converting design briefs into Stitch-ready prompts
- Integrating Stitch output into development workflows

## Do Not Use When

- Building production UIs directly (Stitch output needs cleanup)
- Needing pixel-perfect Figma designs (use Figma instead)
- The project has an existing design system (extend it manually)

---

## Core Prompting Principles

| Principle | Do | Don't |
|-----------|-----|-------|
| **Be specific** | "Sign-up form with email, password, Google SSO button" | "Make a login page" |
| **Define visual style** | "Minimalist, Inter font, blue-700 primary, rounded-lg" | "Make it look good" |
| **Specify platform** | "Mobile-first responsive, 375px default" | Leave platform ambiguous |
| **Structure flows** | "3 screens: landing > pricing > checkout" | One giant paragraph |
| **Include functional reqs** | "Dark mode toggle in header, persists to localStorage" | Only describe layout |
| **Specify interactions** | "Button: hover lift+shadow, active pressed, disabled 50%" | Skip hover/focus states |

---

## Prompt Template

```
Design a [type] for [product/purpose].

**Style:** [visual style, colors, fonts, mood]
**Platform:** [mobile/desktop/responsive] [breakpoints]
**Screens:** [list each screen and key elements]

Screen 1 — [Name]:
- [Element]: [specific description]
- [Element]: [specific description]

Screen 2 — [Name]:
- [Element]: [specific description]

**Interactions:** [hover states, transitions, animations]
**Constraints:** [accessibility, brand guidelines, tech stack]
```

---

## Examples by Use Case

### Landing Page

```
Design a SaaS landing page for an AI writing tool.

Style: Modern minimal, Inter + DM Sans, indigo-600 primary, white bg.
Platform: Desktop-first, responsive to mobile.

Sections:
1. Hero: Headline "Write faster with AI", subtext, CTA button, product screenshot
2. Features: 3-column icon grid (Speed, Quality, Integration)
3. Social proof: Logo bar + 2 testimonial cards
4. Pricing: 3-tier cards (Free/Pro/Team) with feature comparison
5. Footer: Links, newsletter signup

Interactions: Subtle fade-in on scroll, hover lift on cards.
```

### Mobile App

```
Design a fitness tracking app, 4 screens.

Style: Dark theme, rounded corners, SF Pro, lime-400 accent on dark-900.
Platform: iOS, 390px width, safe areas.

Screen 1 — Dashboard: Daily stats ring, activity feed, bottom tab bar.
Screen 2 — Workout: Exercise list with sets/reps, timer, rest countdown.
Screen 3 — Progress: Weekly chart, personal records, streak counter.
Screen 4 — Profile: Avatar, goals, settings list, sign out.
```

### Dashboard

```
Design an analytics dashboard for e-commerce.

Style: Clean corporate, Zinc neutrals, Geist font, data-dense layout.
Platform: Desktop 1440px, sidebar navigation.

Layout:
- Sidebar: Logo, nav (Overview, Orders, Products, Customers, Settings)
- Header: Date range picker, search, notification bell, avatar
- Main grid: Revenue card, Orders card, Conversion rate, AOV
- Charts: Line chart (revenue trend), Bar chart (top products)
- Table: Recent orders with status badges, pagination
```

### Multi-Step Form

```
Multi-step signup form for B2B platform.

Steps:
1. Account details (company name, email, password)
2. Company information (industry, size, role)
3. Team setup (invite members)
4. Confirmation with success message

Features: Progress indicator at top, field validation with inline errors,
Back/Next navigation, Skip option for step 3.

Style: Minimal, focused, low-friction. White bg, green success states.
```

---

## Iteration Strategies

1. **Refine with annotations** — "Move the CTA above the fold", "Make the sidebar collapsible"
2. **Generate variants** — "Show 3 color scheme variations of this design"
3. **Progressive refinement** — Layout first, then typography, color, interactions
4. **Component focus** — "Redesign just the pricing card with monthly/annual toggle"

---

## Design-to-Code Workflow

| Path | Best For | Steps |
|------|----------|-------|
| **Stitch > HTML** | Quick prototypes | Export HTML, clean up, integrate |
| **Stitch > Figma** | Design handoff | Screenshot, Figma trace, dev specs |
| **Stitch > Framework** | Production | Export, extract tokens, build in React/Vue |

### Export Best Practices

1. Export as HTML/CSS, extract design tokens (colors, spacing, fonts)
2. Replace hardcoded values with CSS custom properties
3. Convert to your component framework (React, Vue, Svelte)
4. Add responsive breakpoints if output is single-width
5. Add accessibility: alt text, ARIA labels, keyboard nav, focus styles
6. Replace any emoji icons with proper SVG icons (Lucide, Heroicons)

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Vague prompts | Generic output | Be specific about every element |
| Too many screens | Quality drops | 3-5 screens per prompt max |
| No style direction | Inconsistent aesthetics | Always specify colors, fonts, mood |
| Ignoring platform | Wrong sizing/touch targets | Specify mobile/desktop/responsive |
| Copy-paste without review | Inaccessible HTML | Always audit and refine output |
| Skipping interactions | Static feel | Describe hover, focus, active states |

---

## Tips for Better Results

1. **Reference real products** — "Similar to Linear's dashboard layout"
2. **Specify exact colors** — Use hex or Tailwind color names, not "blue"
3. **Name your fonts** — "Inter for body, Space Grotesk for headings"
4. **Describe states** — "Button: default, hover (lift+shadow), active, disabled (opacity 50%)"
5. **Set constraints** — "Max 5 nav items", "No more than 3 CTAs per page"
6. **Specify icon style** — "Outlined 24px icons from Lucide" not just "add icons"
7. **Use design terminology** — "hero section", "glassmorphic", "bento grid"
8. **Iterate incrementally** — Small focused changes, not complete redesigns
