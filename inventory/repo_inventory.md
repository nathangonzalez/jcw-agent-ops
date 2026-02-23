# JCW Repo Inventory

> Last updated: 2026-02-23 by Scout Agent

## Summary

- **Total repos:** 19
- **Active / Core:** 5
- **Dev / Legacy:** 8
- **Archived:** 1
- **Empty / Stub:** 3
- **Personal / Fork:** 2
- **GCP Project:** `jcw-2-android-estimator`

---

## Repo Table

| # | Repo | Visibility | Primary Language / Stack | Deploy Target | Datastore | Owner | Status | Risks / Notes |
|---|------|-----------|--------------------------|---------------|-----------|-------|--------|---------------|
| 1 | **jcw-agent-ops** | Public | Python, JS, PowerShell | GCP App Engine (agentops-webui svc) | Firestore (jcw-2-android-estimator) | nathan | **Active Core** | Ops brain; Playwright UAT; Slack bot; webui service |
| 2 | **jcw_payroll** | Public | Node.js (Express), HTML/JS | GCP App Engine (labor-timekeeper svc, nodejs22, F1) | SQLite (better-sqlite3) + GCS backup | nathan | **Active Core** | Single-instance SQLite on ephemeral disk; GCS restore on cold start |
| 3 | **jcw-suite** | Public | Monorepo shell (no code yet) | GCP App Engine (planned) | -- | nathan | **Active Scaffold** | Consolidation target for all core apps |
| 4 | **jcw_financials** | Public | Python (Streamlit) | GCP App Engine (planned) | None (pandas in-memory) | nathan | **Active Core** | No persistent datastore; reconcile and analyze scripts |
| 5 | **ConstructionEstimator** | Private | Python (Flask), Jupyter | Docker / local | SQLite (construction_estimator.db) | nathan | **Active Dev** | OpenAI deep-research test; OCR pipeline |
| 6 | **jcw-enterprise-suite** | Public | Python (mega-repo, C/C++/Cython) | -- | -- | nathan | **Archived** | 105 MB Python vendored; mined only |
| 7 | **jcw-estimator-pro** | Public | Python (FastAPI + uvicorn), JS, HTML | GCP Cloud Run (Dockerfile + GCP deploy YAMLs) | None persisted (in-memory) | nathan | **Active Legacy** | FastAPI cost estimator; ML model (scikit-learn); OCR libs; master branch |
| 8 | **jcw-2-admin** | Private | Python (Flask), HTML | Docker Compose (Flask + nginx) | SQLAlchemy (Flask-SQLAlchemy) | nathan | **Active Legacy** | Estimating admin app; PyJWT + bcrypt auth; docker-compose with nginx |
| 9 | **mainstreet_migrator** | Public | Python (Flask), Shell, C, Tcl | GCP Cloud Run (cloudrun.yaml) | Database dir present (likely SQLite) | nathan | **Active Migration** | Data migration tool; 181 MB Python vendored; SA msm-runtime@ |
| 10 | **jcw_ai_estimator** | Public | Python (FastAPI), TypeScript | GCP (infra dir, Dockerfiles, gcloud deploy) | FastAPI backend (pydantic models) | nathan | **Active Dev** | Separate frontend/backend; GCloud deploy scripts |
| 11 | **estimator-backend** | Public | -- | -- | -- | nathan | **Empty Stub** | Only README.md; placeholder repo |
| 12 | **jcw_estimate_ai-** | Public | Python (Flask) | Render (render.yaml, free plan) | Firebase Admin + Vertex AI | nathan | **Legacy** | Flask + firebase-admin + google-cloud-aiplatform; Render free tier |
| 13 | **jcw_estimate_android** | Public | Kotlin, Swift, TypeScript | Firebase / Android | Firestore (rules present) | nathan | **Legacy** | Firestore rules expired 2025-09-14; RISK: open rules |
| 14 | **jcw_estimate** | Public | Python (Flask) | Render (render.yaml, free plan) | None | nathan | **Legacy** | Minimal Flask + gunicorn; Render free tier |
| 15 | **ConstructionEstimator3.0** | Public | -- | -- | -- | nathan | **Empty Stub** | Only README.md |
| 16 | **ConstructionEstimator2.0** | Public | -- | -- | -- | nathan | **Empty Stub** | Only README.md |
| 17 | **Nate12** | Public | -- | -- | -- | nathan | **Empty** | Empty repo; created 2021 |
| 18 | **sample_app** | Public | Ruby, JavaScript | Heroku (inferred) | -- | nathan | **Personal Inactive** | Rails tutorial app; last updated 2018 |
| 19 | **heroku-buildpack-ruby** | Public | Ruby, Shell | Heroku | -- | nathan | **Fork Inactive** | Forked Heroku buildpack; last updated 2018 |

---

## Deployment Targets Summary

| Target | Service(s) |
|--------|-----------|
| GCP App Engine | labor-timekeeper (jcw_payroll), agentops-webui (jcw-agent-ops), planned: financials, suite-shell, estimator |
| GCP Cloud Run | jcw-estimator-pro, mainstreet_migrator |
| Render (free) | jcw_estimate, jcw_estimate_ai- |
| Firebase / Android | jcw_estimate_android |
| Docker (local/self-host) | ConstructionEstimator, jcw-2-admin |
| Heroku (inactive) | sample_app |

## Datastore Summary

| Datastore | Repo(s) |
|-----------|---------|
| SQLite (better-sqlite3) + GCS | jcw_payroll |
| SQLite (local) | ConstructionEstimator |
| SQLAlchemy (Flask-SQLAlchemy) | jcw-2-admin |
| Firestore | jcw-agent-ops (webui), jcw_estimate_android |
| Firebase Admin + Vertex AI | jcw_estimate_ai- |
| None / In-memory | jcw_financials, jcw-estimator-pro, jcw_estimate |

## Key Risks

1. **jcw_estimate_android** - Firestore security rules expired 2025-09-14 with open read/write. All client requests denied or wide open depending on Firebase behavior.
2. **jcw_payroll** - SQLite on App Engine ephemeral disk; single instance (min=1, max=1). GCS backup/restore is the durability mechanism but risks data loss on crash between backups.
3. **jcw-enterprise-suite** - 105 MB+ Python vendored in repo; archived but not cleaned.
4. **Render free tier** - jcw_estimate and jcw_estimate_ai- on Render free plan; likely sleeping/unreliable.
5. **Scattered deploy targets** - App Engine, Cloud Run, Render, Firebase, Docker across repos. Consolidation into jcw-suite monorepo is planned but not started.
6. **No CI/CD** on most repos (only GitHub Actions dirs present on some).
7. **Secrets** - OpenAI API keys referenced in multiple repos; GCP Secret Manager used only by jcw_payroll.

## Consolidation Plan (from jcw-suite/REPOS.md)

- jcw_payroll -> apps/payroll
- jcw_financials -> apps/financials
- jcw-estimator-pro -> apps/estimator-legacy (mine only)
- jcw-enterprise-suite -> archive (mined only)
- estimator-backend -> services/estimator-backend
- Dev/Legacy repos (jcw_ai_estimator, jcw_estimate, jcw_estimate_android, jcw_estimate_ai-, ConstructionEstimator 2.0/3.0) -> mine then archive
