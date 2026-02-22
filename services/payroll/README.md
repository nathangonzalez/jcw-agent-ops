# Payroll Service

The JCW Labor Timekeeper application — existing App Engine service.

## Migration Status
- [ ] Copy from `jcw_payroll/labor-timekeeper/` into this directory
- [ ] Update `app.yaml` service name
- [ ] Verify CI/CD path filters work
- [ ] Test deployment from monorepo

## Stack
- Node.js / Express
- SQLite (ephemeral, GCS-backed)
- ExcelJS for report generation
- ElevenLabs TTS for voice input