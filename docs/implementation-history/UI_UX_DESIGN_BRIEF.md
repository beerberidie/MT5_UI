# Trade Agent MT5 – Comprehensive, Self‑Contained UI/UX Design Brief

## Executive Summary and Goals
- Objective: Redesign the existing single‑page trading workstation into a professional‑grade MT5 companion UI that matches industry standards for financial platforms, while preserving all current functionality and tightening accessibility, performance, and reliability.
- Scope: Navigation/layout, trading workflow, data presentation, interaction patterns, responsive behavior, accessibility (WCAG 2.2 AA), performance, and implementation/testing guidance.
- Non‑goals: Backend feature expansion; major API changes. UI modernization must be strictly backward‑compatible with current APIs and front‑end scripts unless a specific migration path is defined herein.

---

## 1) Complete Project Context

### Purpose and Target Users
- Purpose: A local, fast, reliable trading workstation UI for retail/professional MT5 (MetaTrader 5) traders operating a connected MT5 terminal. Optimized for quick execution, monitoring, and audit/history review.
- Users: Forex/CFD day traders and swing traders with moderate–high information density tolerance. Keyboard power users. Dark‑theme preference. High refresh cadence.

### Technology Stack and Architecture Constraints
- Frontend:
  - Single HTML file: `frontend/index.html` (contains HTML+CSS+JS).
  - Served locally by Python `http.server` on `http://127.0.0.1:3000` via `start_app.py`.
  - No bundler currently; keep zero‑install, local‑only simplicity.
- Backend:
  - FastAPI app at `http://127.0.0.1:5001` (uvicorn), with CORS enabled for `127.0.0.1:3000`.
  - Rate limiting via slowapi; CSV logging; optional X‑API‑Key security.
  - MT5 integration through `backend.mt5_client` (direct terminal integration).
  - Key configs from `backend/config.py`: API_HOST/PORT, FRONTEND_ORIGINS, data/log directories, AUGMENT_API_KEY.
- Local Orchestration:
  - `start_app.py` launches both backend and static frontend server, watches output, and opens the browser.

### Existing Functionality to Preserve
- Market watch symbols (from live MT5 Market Watch; fallback to configured symbols).
- Order entry: market orders (buy/sell); pending orders (create/cancel).
- Positions list; account summary header; activity (deals/orders) history; historical bars/ticks range fetch.
- Collapsible left sidebar with “Mini Market Watch” (priority/top movers); tabbed panels; notifications.
- Auto-refresh loops for market data, account, and positions.
- Keyboard and ARIA support in tab systems; prefers-reduced-motion; reduced visual jitter; dark UI theme.

### MT5 Integration Requirements
- Live symbols and prices via MT5 terminal connection.
- Market orders: mapped via canonical to broker symbol.
- Pending orders create/cancel; history (deals/orders) and historical price data (bars/ticks).
- Daily loss limit enforcement, session windows, and symbol volume validations enforced server‑side.

---

## 2) Detailed Current State Documentation

### High‑Level UI Layout (Current)
- 3‑column grid: Left (sidebar), Center (primary content), Right (positions/activity).
- Sidebar collapsible to a thin icon rail; shows a “Mini Market Watch” list in collapsed state.
- Dense tab usage: order type tabs (Market vs Pending), analysis tabs (Chart, Bars, Ticks, Stats), activity tabs (Deals, Orders, Summary).

### Frontend Structure
- Single file: `frontend/index.html`
  - CSS: root‑level design tokens (colors, spacing, typography), responsive media queries at 1600/1400/1200/1000/768px.
  - JS: CONFIG object, state, API helpers, loaders, event handlers, tab logic, sidebar toggle, refresh loops.

Example CONFIG block (do not change name/shape):

```html
<script>
  const CONFIG = {
    API_BASE: 'http://127.0.0.1:5001',
    REFRESH_INTERVAL: 5000,
    CONNECTION_TIMEOUT: 10000,
    MAX_RETRIES: 3
  };
</script>
```

Auth headers (uses global `window.AUGMENT_API_KEY` if present):

```javascript
function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (window.AUGMENT_API_KEY) headers['X-API-Key'] = String(window.AUGMENT_API_KEY);
  return headers;
}
```

### Critical Components and IDs (JS‑Referenced; must remain stable)
- Order entry: `sym`, `buy-btn`, `sell-btn`, `volume`, `deviation`, `sl`, `tp`, `order-output`.
- Account summary header: `header-balance`, `header-equity`, `header-margin`, `header-free-margin`.
- Positions: `positions-tbody`.
- Historical data: `histSymbol`, `histTimeframe`, `histDateFrom`, `histDateTo`, `histCount`, `historical-bars-table`.
- Activity/history: `historyDateFrom`, `historyDateTo`, `historySymbolFilter`, `deals-table`, `orders-history-table`, `history-summary` metrics (`total-deals`, `total-profit`, `total-commission`, `net-profit`).
- Pending orders (standalone): `pendingOrderType`, `pendingSymbol`, `pendingPrice`, `pendingVolume`, `pendingSL`, `pendingTP`, `pendingComment`, `pending-orders-tbody`.
- Pending orders (integrated): `pendingOrderTypeIntegrated`, `pendingSymbolIntegrated`, `pendingPriceIntegrated`, `pendingVolumeIntegrated`, `pendingSLIntegrated`, `pendingTPIntegrated`, `pending-order-output-integrated`.
- Sidebar/priority: `priority-symbols-list`, `sidebar-mini-watch-list`; sidebar toggle button has `aria-expanded` attribute.
- Analysis controls: `analysis-controls-panel`, `controls-toggle-icon`.
- Connection indicator: `connection-status`, `connection-text`.

Rule: Do not rename or remove these IDs without updating event handlers and API calls accordingly.

### Current API Integrations (must remain functional)
- `GET /api/symbols?live=true|false`
- `GET /api/symbols/priority?limit=5`
- `GET /api/account`
- `GET /api/positions`
- `POST /api/order` (requires X‑API‑Key if configured)
- `GET /api/orders` (pending)
- `POST /api/orders/pending` (requires X‑API‑Key)
- `DELETE /api/orders/{ticket}` (requires X‑API‑Key)
- `GET /api/history/bars?symbol=...&timeframe=...&date_from=...&date_to=...&count=...`
- `GET /api/history/deals?date_from=...&date_to=...&symbol=...`
- `GET /api/history/orders?date_from=...&date_to=...&symbol=...`
- `GET /events` (SSE heartbeat)

Note: One legacy `fetch('/api/place_order')` remains in the integrated pending order path; replace with `CONFIG.API_BASE + '/api/orders/pending'` in implementation, preserving current UX.

### Responsive Behavior and Breakpoints
- Media queries at 1600/1400/1200/1000/768px adjust grid columns, form grids, tabs, and controls density.
- Collapsed sidebar reduces left column to an icon rail; Mini Market Watch becomes visible.

### Accessibility Status
- ARIA for tablists/tabpanel with `aria-selected`, `aria-controls`, `aria-hidden` updates.
- Keyboard navigation for tabs (ArrowLeft/Right, Home/End).
- `prefers-reduced-motion` respected for transitions.
- Needs improvements: color contrast audit, focus outlines consistency, form labeling and error hinting, reduced motion alternatives for all animated affordances.

---

## 3) Explicit Technical Requirements and Constraints

### File/Build Constraints
- Maintain a single‑file HTML deliverable (`index.html`) with embedded CSS/JS for now.
- No external build tools by default; any proposal to split files/bundle must include a zero‑config fallback plan.

### JavaScript Functions That Must Continue to Work
- Data: `loadSymbols`, `loadPrioritySymbols`, `loadAccount`, `loadPositions`, `refreshMarketData`, `startAutoRefresh`, `stopAutoRefresh`.
- Orders: `sendOrder`, `placePendingOrder`, `placePendingOrderIntegrated`, `cancelPendingOrder`.
- History: `loadHistoricalData`, `loadTradingHistory`.
- UI: `setupEventHandlers`, `initializeApp`, `toggleSidebar`, `showOrderTab`, `showHistoricalTab`, `showActivityTab`, `toggleAnalysisControls`, `showNotification`.

### DOM Stability Requirements
- Preserve IDs listed above; maintain presence and semantics of tab containers and ARIA attributes.
- Preserve `order-tabs`, `analysis-tabs`, `feed-tabs` structures with `role="tablist"/role="tab"/role="tabpanel"` logic.

### API and Security
- All fetches must use `CONFIG.API_BASE` prefix and include `getAuthHeaders()`.
- POST/DELETE operations require `X‑API‑Key` when backend AUGMENT_API_KEY is set.
- Rate limits: orders ~10/min; reads ~60–100/min (respect backoff; surface friendly errors).

### Performance and Compatibility
- Target 60 FPS on modern desktop browsers; avoid layout thrash; minimize reflows/repaints.
- Keep initial HTML+CSS+JS size reasonable; defer noncritical work until idle; batch DOM updates.
- Ensure smooth behavior at zoom levels 90–125% and DPI scaling on Windows.

---

## 4) Design Specifications

### Information Architecture and Layout (Proposed)
- Left: Collapsible Sidebar (navigation, compact metrics; collapsed icon rail shows mini watch and quick actions).
- Center: Primary Workpane
  - Top: Order Entry (tabbed: Market | Pending). High‑visibility symbol selector, volume, risk/deviation, SL/TP.
  - Middle: Market Analysis (tabbed: Chart | Bars | Ticks | Stats) with collapsible controls panel.
- Right: Positions and Activity
  - Positions table with sticky header, summary row, row actions (close/modify pending).
  - Activity (tabbed: Deals | Orders | Summary) with date/symbol filters.
- Global: Header account KPIs (Balance, Equity, Margin, Free Margin) with strong contrast and clear units.

### Component Standards
- Buttons: Primary (accent), Success (green), Danger (red), Subtle (secondary). 44px min target height (desktop), with compact density option.
- Forms: Labeled inputs with inline validation, helpful placeholders, explicit units. Keyboard focus outline visible on dark backgrounds.
- Tables: Sticky header, zebra stripes, hover row highlight, numeric alignment on right, monospace for prices if needed; loading/empty states.
- Cards: Low‑elevation panels with clear headers, consistent padding, and slots for actions.
- Tabs: Large click targets, clear selected state, keyboard accessible per WAI‑ARIA APG 1.2.
- Tooltips: On hover/focus; accessible description for icons.

### Visual System (Dark Theme)
- Color palette tokens (example mapping): backgrounds (primary/secondary/tertiary), cards, text (primary/secondary/muted), accents (primary/success/danger/warning), borders, state backgrounds.
- Typography: Inter system stack; base 16px; scale: xs/sm/base/lg/xl/2xl; weights: 400–700; consider tabular-nums for numeric columns.
- Spacing and Radii: spacing scale `space-1..space-8`; radii `radius-sm/md/lg`; minimal shadows to reduce bloom on dark backgrounds.

### Interaction Patterns and Workflow
- Order entry: symbol selection auto-fills across panels; real‑time volume validation with min/step hints; submit shows confirmation with ticket/retcode; broker errors surfaced clearly.
- Pending orders: integrated form reuses validation; success re-fetches pending list; cancellation prompts confirmation.
- Analysis: controls collapsible with state persistence; bars/ticks tables offer quick count presets; stats summarize ranges.
- Activity filters: date range presets (today, week, custom), symbol filter; summary cards reflect current filter.
- Sidebar: toggle via click and Alt+S (optional), state persisted; collapsed mode shows top movers.

### Responsive Breakpoints (min required)
- ≥1600px: 3 columns (L variable | C 1fr | R fixed ~380px).
- 1400–1599px: reduce side paddings and card gaps; keep 3 columns.
- 1200–1399px: narrow right column if needed; compact table density.
- 1000–1199px: stack right column under center; keep left sidebar.
- <1000px: single column stack; sidebar overlays as drawer; key trading actions remain reachable.

### Accessibility (WCAG 2.2 AA)
- Contrast: All text/UI ≥ 4.5:1; large text ≥ 3:1; verify table header contrast.
- Keyboard: Full tab order coverage; tablists per APG (Arrow keys, Home/End); focus visible, not obscured by sticky elements.
- Motion: Honor `prefers-reduced-motion`; provide no-motion alternative for transitions.
- Forms: Programmatic labels, `aria‑describedby` for hints/errors; input errors described; no color‑only cues.
- Live regions: Notifications via `aria-live="polite"` for order confirmations/errors.
- Tooltips: Accessible descriptions on focusable controls; dismissable and not hover‑only.

---

## 5) Implementation Guidelines

### Step‑by‑Step Approach
1. Baseline snapshot: branch off and copy current `index.html`; enable a feature flag data‑attrib (e.g., `data-ui="v2"`) on `<body>` to stage new styles/components without breaking.
2. Token audit: normalize color/typography/spacing tokens; centralize usage; verify contrast.
3. Layout refactor: implement grid with named areas (sidebar/content/aside) preserving IDs and tab structures.
4. Componentization (within single file):
   - Create CSS sections per component (Buttons, Forms, Tabs, Tables, Cards, Sidebar, Header).
   - Convert ad‑hoc styles to BEM‑like classes; keep legacy IDs for script hooks.
5. Interaction polish:
   - Standardize focus/hover/active states; keyboard flows for all tabs.
   - Consistent loading/empty/error states with skeletons where applicable.
6. API call consistency:
   - Ensure all fetches use `CONFIG.API_BASE + endpoint` with `getAuthHeaders()`.
   - Replace legacy `fetch('/api/place_order')` with `POST /api/orders/pending` using `CONFIG.API_BASE`.
7. Responsive tuning: implement the breakpoint behaviors above; verify stacking logic and density modes.
8. Accessibility pass: ARIA attributes, focus management, reduced motion, screen reader labels.
9. Performance: batch DOM updates, reduce reflows, debounce high‑frequency events; minimize costly shadows/filters.
10. Persistence: keep sidebar collapsed state and analysis controls state in `localStorage`; add optional per‑tab persistence.

### Testing and Validation
- Unit/API tests: run `pytest -q` in `tests/` (e.g., `tests/test_api_endpoints_phase1.py`); confirm endpoints and CSV logging behaviors.
- Smoke tests: `scripts/smoke_test.py`; manual flow for order submit/cancel, history loads, and refresh loops.
- UI checks (manual unless Playwright is approved):
  - Viewports: 1920, 1600, 1366, 1024, 768 px; zoom 90/100/110/125%.
  - Keyboard navigation through all tabs and forms; focus visibility.
  - Reduced motion enabled OS‑wide: verify no excessive animation.
  - Tooltip visibility and ARIA labeling; loading/empty/error states.
- Performance: DevTools Performance overview; inspect layout thrashing; FPS stable on table scroll and tab switches.

### Rollback Procedures
- Keep original `index.html` as `index.legacy.html`.
- Feature flag gating: toggle `data-ui="v1|v2"` on `<body>` to switch styles if needed.
- If critical regression detected:
  - Revert to legacy file; restore CONFIG/API call consistency changes only (safe).
  - Preserve logs for diff and follow‑up.

### Code Organization and Commenting Standards
- Organize CSS by component blocks with clear headers and token usage comments.
- JS: group by domains (API, State, UI, Events). JSDoc-style comments for public functions (e.g., `loadPositions()`).
- Include “Do not rename/remove” comments above critical IDs and tab containers referenced by JS.
- Log user‑visible errors via `showNotification`; log technical details to console.

---

## 6) Deliverables for the Designer/Engineer
- Wireframes for Desktop (≥1600), Laptop (1366), Tablet (1024/768) showing:
  - Sidebar collapsed/expanded states; Mini Market Watch content model.
  - Order Entry (Market/Pending) layouts with validation hints.
  - Market Analysis tab states; controls expanded/collapsed.
  - Positions table with empty/loading/filled; Activity tabs (Deals/Orders/Summary).
- Component spec sheet:
  - Buttons, Inputs, Selects, Tables, Cards, Tabs, Tooltips, Notifications.
  - States: default/hover/focus/active/disabled; tokens mapping.
- Token sheet:
  - Colors with roles; spacing; typography; radii; elevation; transitions; motion guidance.
- Accessibility checklist with examples (labels, live regions, keyboard bindings).
- Change log mapping: which styles/classes are new vs reused; explicit note that IDs listed earlier remain intact.

---

## 7) Acceptance Criteria (Go/No‑Go)
- Functional parity: All prior flows work (symbols, account, positions, market order, pending order create/cancel, historical data, activity).
- No broken selectors: All listed IDs remain, with scripts functioning without edits (except the intentional legacy endpoint fix).
- UI quality:
  - Clear hierarchy, professional density, consistent spacing/typography, legible tables.
  - Sidebar collapsed UX is useful (mini metrics/movers).
- Accessibility:
  - WCAG 2.2 AA contrast; keyboardable tabs; visible focus; reduced motion respected.
- Performance:
  - Smooth tab switches and table scroll; no long tasks > 50ms on routine interactions.
- Responsive:
  - Layouts hold at 1920/1600/1366/1024/768 widths; critical actions always reachable.

---

## 8) Known Gaps and Technical Debt to Address
- Replace legacy `fetch('/api/place_order')` with `CONFIG.API_BASE + '/api/orders/pending'` and `getAuthHeaders()`.
- Consolidate any duplicate tab logic; ensure one canonical keyboard handler per tablist instance.
- Audit symbols priority/mini watch heuristics to ensure it degrades gracefully with empty logs.

---

## 9) How to Run and Verify (for the Implementer)
- Start services: `python start_app.py` (requires `.venv311` with dependencies installed).
- Visit: `http://127.0.0.1:3000`; Swagger at `http://127.0.0.1:5001/docs`.
- If `AUGMENT_API_KEY` is set server‑side, set `window.AUGMENT_API_KEY` (or add an input UI that stores it, then sets a global).
- Run tests: `pytest -q` (focus: `tests/test_api*.py`, `tests/test_integration.py`, `tests/test_risk*.py`).
- Optional UI automation: propose Playwright script for viewport/zoom matrix (requires approval to add dev deps).

