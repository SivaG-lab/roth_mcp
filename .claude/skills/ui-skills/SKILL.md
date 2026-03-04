---
name: ui-skills
description: "Opinionated constraints for building modern web interfaces. Covers layout, spacing, typography, color, responsiveness, accessibility, and component design. Use when building UI components, designing layouts, styling web apps, or reviewing frontend code for design quality."
---

# UI Skills — Interface Design Constraints

## Purpose

Opinionated, practical rules for building clean, consistent web interfaces. Apply these constraints when writing HTML/CSS/JSX to avoid common design mistakes.

## When to Use

- Building or styling UI components
- Reviewing frontend code for visual quality
- Creating layouts, forms, or navigation
- Implementing responsive designs

## Core Constraints

### Layout
- Use CSS Grid for 2D layouts, Flexbox for 1D alignment
- Maximum content width: 1200-1440px for readability
- Use consistent spacing scale (4px base: 4, 8, 12, 16, 24, 32, 48, 64)
- Avoid arbitrary magic numbers for spacing

### Typography
- Maximum 2 font families per project (heading + body)
- Use rem for font sizes, maintain a type scale (1.25 or 1.333 ratio)
- Body text: 16px minimum, line-height 1.5-1.75
- Headings: line-height 1.1-1.3

### Color
- Define a palette with semantic tokens (primary, secondary, success, warning, error)
- Ensure 4.5:1 contrast ratio for text (WCAG AA)
- Use opacity for hover/active states, not new colors
- Support dark mode from the start (CSS custom properties)

### Components
- Every interactive element needs visible focus styles
- Buttons: minimum 44x44px touch target
- Forms: labels above inputs, visible error states, helpful placeholders
- Cards: consistent border-radius, shadow hierarchy (sm, md, lg)

### Responsiveness
- Mobile-first: design for 320px, enhance upward
- Breakpoints: 640px (sm), 768px (md), 1024px (lg), 1280px (xl)
- Never hide critical content on mobile — reorganize instead
- Test with real content, not lorem ipsum

### Accessibility
- All images need alt text (decorative = empty alt)
- Keyboard navigable: tab order, focus management
- Announce dynamic content changes to screen readers
- Don't rely on color alone to convey information
