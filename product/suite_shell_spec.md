# Suite-Shell UX Spec (v0)

## Goal
Single UI shell with app buttons that routes to each module (payroll, estimating, financials, 3D studio).

## Layout
- **Top bar**: suite logo, app name, user menu, notifications.
- **Side dock**: vertical app buttons with icons + tooltips; active app highlighted.
- **Main panel**: active app content (iframe or route mount).

## Routing
- `/app/<app-id>` for deep links.
- Optional `/` landing shows app tiles.

## Modules
- App dock
- App router
- User menu
- Notifications/toasts
- Optional quick switcher (Cmd/Ctrl+K)

## Non-Goals (v0)
- Cross-app data sync
- Single sign-on beyond existing auth (phase 2)

## Acceptance
- UI shell loads.
- App buttons navigate between placeholder routes.
- Layout works on mobile and desktop.
