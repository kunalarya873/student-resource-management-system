# Design-to-Code Structure Skill

This skill defines the end-to-end engineering methodology for converting visual designs, design systems, and UX specifications into clean, scalable, production-grade frontend code.

---

## 1. Core Conversion Philosophy

1. **Tokens Over Hardcoded Values**: Never hardcode hex codes, pixel sizes, or arbitrary margins directly into JSX. Always resolve them to semantic tokens.
2. **Presentational vs. Behavioral Separation**: Keep UI components purely presentational; isolate data-fetching, backend contracts, and side-effects into feature hooks or services.
3. **Six Essential UI States**: Every screen and interactive component must account for:
   - **Loading / Pending** (skeletons, spinners, disabled submit)
   - **Empty** (zero-data onboarding/guidance)
   - **Populated / Success** (standard data presentation)
   - **Validation Error** (field-adjacent and form-summary)
   - **System Error** (network/server failure with retry capability)
   - **Access / Permission Denied** (role-aware visibility & fallback states)
4. **Backend Contract Protection**: Never invent or mutate API contracts to fit a design. When API behavior is unknown or missing, label it explicitly as `UNVERIFIED` and use typed mock adapters.

---

## 2. Phase-by-Phase Conversion Workflow

```
┌─────────────────────────┐
│ 1. Token & Theme Layer  │ -> Colors, Typography, Spacing, Radii, Elevation
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 2. App Shell & Layout   │ -> Breakpoints, Sidebar/Drawer, Topbar, Container
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 3. Atomic Primitives    │ -> Buttons, Inputs, Badges, Modals, Typography
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 4. Domain Components    │ -> ResourceCards, Tables, FilterBars, FormPanels
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 5. Page Assembly        │ -> Routes, Layout Integration, Mock/Real Services
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 6. Review & Audit       │ -> Responsive, A11y, State Verification
└─────────────────────────┘
```

---

## 3. Directory & File Structure Architecture

Structure code to reflect clear boundaries between design tokens, shared primitives, domain features, and page routes:

```text
src/
├── assets/                  # Static assets (SVGs, icons, illustrations)
├── design-system/           # Foundational design tokens & shared primitives
│   ├── tokens/              # Token declarations (colors, typography, spacing)
│   │   ├── colors.ts
│   │   ├── typography.ts
│   │   └── spacing.ts
│   └── components/          # Reusable, domain-agnostic UI atoms
│       ├── Button/
│       │   ├── Button.tsx
│       │   ├── Button.types.ts
│       │   └── index.ts
│       ├── Input/
│       ├── Badge/
│       ├── Dialog/
│       └── EmptyState/
├── components/              # Shared layout & structural elements
│   ├── AppShell/
│   │   ├── AppShell.tsx
│   │   ├── AppSidebar.tsx
│   │   ├── AppTopbar.tsx
│   │   └── PageHeader.tsx
│   └── Feedback/
│       ├── LoadingSkeleton.tsx
│       └── ErrorBoundary.tsx
├── features/                # Domain-specific feature modules
│   └── [feature-name]/      # e.g., resources, auth, folders
│       ├── components/      # Domain components (e.g., ResourceCard, ResourceTable)
│       ├── hooks/           # Feature state & data-fetching hooks
│       ├── services/        # API call definitions & contract mappers
│       └── types/           # View models & verified API types
├── pages/                   # Top-level screen components linked to router
│   ├── DashboardPage.tsx
│   └── ResourceLibraryPage.tsx
├── styles/                  # Global CSS, theme overrides, CSS variables
│   └── index.css
└── App.tsx                  # Route configuration & shell orchestration
```

---

## 4. Design Token Extraction Guidelines

When analyzing design specifications or Figma tokens, map them systematically into semantic layers:

### A. Semantic Color Palette
Avoid generic colors (`red`, `blue`, `green`). Categorize by intent:
- **Brand / Primary**: Brand accents, primary CTA, active navigation (e.g., `--color-brand-primary`, `--color-brand-hover`, `--color-brand-soft`)
- **Surfaces & Backgrounds**: Base background, cards, panels, modals (e.g., `--color-bg-page`, `--color-bg-surface`, `--color-bg-subtle`)
- **Typography & Text**: High-contrast body, secondary subtitles, disabled text (e.g., `--color-text-primary`, `--color-text-secondary`, `--color-text-muted`)
- **Borders & Dividers**: Subtle framing and separation (e.g., `--color-border-subtle`, `--color-border-focus`)
- **Status Indicators**: Functional feedback (e.g., `--color-success`, `--color-warning`, `--color-danger`, `--color-info`)

### B. Typography Hierarchy
Define font scales with explicit line-height and weight pairs:
- **Page Titles**: 28px–32px / 36px–40px, Semibold / Bold
- **Section Headings**: 20px–24px / 28px–32px, Semibold
- **Card / Block Titles**: 16px–18px / 24px, Medium / Semibold
- **Body Regular**: 14px–16px / 20px–24px, Regular
- **Labels & Microcopy**: 12px–13px / 16px–18px, Medium / Regular

### C. Spacing Scale (4px/8px Rhythm)
Standardize spacing intervals across padding, margin, and gaps:
- `space-1`: 4px
- `space-2`: 8px
- `space-3`: 12px
- `space-4`: 16px
- `space-6`: 24px
- `space-8`: 32px
- `space-12`: 48px

---

## 5. Responsive Shell & Navigation Guidelines

Follow a standardized multi-device responsive strategy:

| Breakpoint | Width Range | Sidebar / Navigation Behavior | Layout Behavior |
|---|---|---|---|
| **Desktop** | `>= 1024px` | Persistent left sidebar (approx. 240px–280px) | Multi-column, rich tables, side panels |
| **Tablet** | `640px – 1023px` | Collapsible navigation rail or toggleable drawer | 2-column cards, collapsible filter panels |
| **Mobile** | `< 640px` | Dismissible navigation drawer with overlay backdrop | Single-column stack, cards replace wide tables |

### Implementation Rules:
- The top bar hosts branding, mobile hamburger trigger, contextual title, and user profile.
- Page content lives within a bounded container with standardized padding (e.g., 24px desktop, 16px mobile).
- Touch targets must meet the minimum size requirement of **44x44px** on mobile.

---

## 6. Component Conversion Rules & Conventions

When creating or modifying components:

1. **Typed Props Interface**:
   ```typescript
   export interface ResourceCardProps {
     resource: ResourceViewModel;
     onSelect?: (id: string) => void;
     permittedActions: PermittedAction[];
     isLoading?: boolean;
   }
   ```
2. **No Role Assumption Inside Leaf Components**:
   - Do **NOT** write `if (role === 'Student') { ... }` inside a generic card or table cell.
   - **DO** pass capability flags: `canDelete={canManageResource}`, `canShare={canShareResource}`.
3. **Decompose Complex Screens into Presentational Chunks**:
   - `ScreenView` (manages layout & high-level states)
     - `FilterToolbar` (search input, status filters, sort select)
     - `ContentList` (switches between Loading, Empty, Populated, Error states)
       - `CardItem` / `RowItem` (pure presentational representation)
4. **Form Architecture**:
   - Clear field labels linked via `htmlFor` / `id`.
   - In-place field validation errors under invalid inputs.
   - Pending state disables submit buttons and prevents duplicate submissions.
   - Non-destructive cancel triggers confirmation if inputs are dirty.

---

## 7. Review & Verification Checklist

Before accepting code converted from design, run this verification:

- [ ] **Design Token Adherence**: Colors, spacing, radii, and fonts use defined tokens, not arbitrary values.
- [ ] **Responsive Fluidity**: Layout tested at 375px (mobile), 768px (tablet), and 1280px (desktop).
- [ ] **State Completeness**: Loading skeletons, empty states, error fallbacks, and validation messages are rendered and verified.
- [ ] **Accessibility (A11y)**: Semantic HTML (`<nav>`, `<header>`, `<main>`, `<button>`), visible focus rings, and `aria-label` for icon-only actions.
- [ ] **Type Safety**: No usage of `any`. Explicit types for view models, props, and verified API contracts.
- [ ] **Interactive States**: Hover, focus-visible, active, and disabled states implemented across all interactive elements.