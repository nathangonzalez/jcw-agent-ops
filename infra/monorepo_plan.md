# Monorepo Plan (JCW Suite)

## Goal
Create a single monorepo with independently deployable App Engine services and a suite-shell UI that links all apps.

## Target Layout
```
services/
  payroll/
  estimating/
  financials/
  suite-shell/
packages/
  shared/
  ui/
infra/
  ci-cd-monorepo.yml
  appengine/
    dispatch.yaml (optional)
```

## Service Boundaries
- **payroll**: labor timekeeper app (existing App Engine service).
- **estimating**: estimator app (future service).
- **financials**: financials app (future service).
- **suite-shell**: single UI shell with app buttons, auth, and navigation.

## Routing Strategy
- **Default**: subdomains per service (e.g., `payroll.<domain>`, `estimating.<domain>`).
- **Optional**: `dispatch.yaml` to map `/payroll/*`, `/estimating/*` to App Engine services.

## Migration Steps (Incremental)
1. **Create monorepo skeleton** under `services/` and `packages/`.
2. **Move payroll** into `services/payroll` (keep App Engine `app.yaml`).
3. **Add suite-shell** with basic UI + app buttons.
4. **Copy CI/CD workflow** to monorepo and run in dry-run mode.
5. **Add estimating/financials** services as they stabilize.
6. **Enable dispatch routing** only after subdomains are confirmed.

## Risks / Mitigations
- **CI/CD complexity**: use path filters + matrix to isolate service builds.
- **Shared dependency drift**: use `packages/shared` with semantic versioning.
- **Auth integration**: centralize in suite-shell and validate per service.

## Acceptance
- Repo layout exists.
- Suite-shell runs locally.
- CI/CD workflow template added.
- Payroll can deploy from the new layout (patch + promote).
