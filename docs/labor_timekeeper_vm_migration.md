# Labor Timekeeper: VM Migration Plan

*Generated: 2026-02-23 | Status: Draft*

## 1. Current Architecture

| Component | Current State |
|-----------|--------------|
| **Runtime** | GCP App Engine (Node.js 22, F1 instance) |
| **Database** | SQLite via `better-sqlite3` at `/tmp/app.db` (ephemeral) |
| **Backup** | GCS bucket `jcw-labor-timekeeper` — 5-min interval + daily snapshots |
| **Cold Start** | 3-retry restore from GCS, fallback to daily snapshots |
| **Secrets** | GCP Secret Manager (`SMTP_USER`, `SMTP_PASS`, `OPENAI_API_KEY`) |
| **URL** | `https://labor-timekeeper-dot-jcw-2-android-estimator.uc.r.appspot.com` |
| **Project** | `jcw-2-android-estimator` |

### Current Problems
1. Every App Engine version switch = fresh DB restore from GCS
2. If backup is overwritten with empty DB, data loss occurs (happened 2/21)
3. No persistent disk — SQLite lives in `/tmp` (wiped on deploy)
4. Version management is fragile (jcw8 → jcw12 through trial and error)

## 2. Target Architecture

| Component | Target State |
|-----------|-------------|
| **Runtime** | Docker on GCE VM (clawbot-ops or dedicated `jcw-app-vm`) |
| **Database** | SQLite on persistent disk, mounted as Docker volume |
| **Backup** | Cron: DB → GCS every 5 min + daily snapshot, 30-day retention |
| **Reverse Proxy** | Nginx or Caddy for HTTPS termination |
| **Secrets** | Environment file on VM (from Secret Manager) |
| **URL** | Same App Engine URL → redirect to VM, or new subdomain |

### Why Move?
- **Data durability**: Persistent disk survives container restarts
- **Simpler deploys**: `docker-compose up -d` replaces version juggling
- **Cost**: VM is flat ~$25/month vs App Engine pay-per-use
- **Control**: Direct SSH access, no cold start delays

## 3. Docker Configuration

### Updated docker-compose.yml
```yaml
version: '3.8'
services:
  labor-timekeeper:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - app-data:/app/data        # Persistent SQLite
      - app-exports:/app/exports  # Export files
    environment:
      - NODE_ENV=production
      - PORT=8080
      - GOOGLE_CLOUD_PROJECT=jcw-2-android-estimator
      - GCS_BUCKET=jcw-labor-timekeeper
    env_file:
      - .env.production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - labor-timekeeper
    restart: unless-stopped

volumes:
  app-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/labor-timekeeper/data
  app-exports:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/labor-timekeeper/exports
```

### Key Changes from Current Dockerfile
- Mount `/app/data` as persistent volume (SQLite lives here)
- Add health check endpoint
- Environment variables via `.env.production` file
- Nginx for HTTPS termination

## 4. Migration Steps

### Phase 1: Prepare (1-2 days)
1. Create persistent disk directory: `/opt/labor-timekeeper/{data,exports}`
2. Download current GCS backup: `gsutil cp gs://jcw-labor-timekeeper/app.db /opt/labor-timekeeper/data/`
3. Update `server.js` to use `/app/data/app.db` instead of `/tmp/app.db`
4. Build and test Docker image locally
5. Create `.env.production` with secrets from Secret Manager

### Phase 2: Deploy to VM (1 day)
1. `docker-compose build` on clawbot-ops (or dedicated VM)
2. `docker-compose up -d`
3. Verify app loads at `http://VM_IP:8080`
4. Run backup cron: test GCS upload from container
5. Configure Nginx for HTTPS (Let's Encrypt or Cloudflare)

### Phase 3: Cutover (1 day)
1. Take final backup from App Engine version
2. Stop GCS auto-backup on App Engine
3. Upload final backup to VM persistent disk
4. Update DNS/routing to point to VM
5. Verify all endpoints work
6. Keep App Engine version as standby (no traffic)

### Phase 4: Cleanup (1 week after cutover)
1. Monitor for 1 week
2. Confirm all payroll exports work
3. Disable App Engine version (don't delete)
4. Update documentation

## 5. Backup Strategy

```bash
# /etc/cron.d/labor-timekeeper-backup
# Every 5 minutes: copy DB to GCS
*/5 * * * * root docker exec labor-timekeeper-labor-timekeeper-1 \
  sqlite3 /app/data/app.db ".backup /tmp/backup.db" && \
  gsutil cp /tmp/backup.db gs://jcw-labor-timekeeper/app.db

# Daily at 2 AM: snapshot with date
0 2 * * * root docker exec labor-timekeeper-labor-timekeeper-1 \
  sqlite3 /app/data/app.db ".backup /tmp/daily.db" && \
  gsutil cp /tmp/daily.db gs://jcw-labor-timekeeper/backups/daily/app.db.$(date +\%Y-\%m-\%d)

# Weekly cleanup: keep 30 days
0 3 * * 0 root gsutil ls gs://jcw-labor-timekeeper/backups/daily/ | \
  head -n -30 | xargs -r gsutil rm
```

## 6. Rollback Plan

If the VM deployment fails:
1. Stop Docker containers on VM
2. Re-enable App Engine version: `gcloud app services set-traffic labor-timekeeper --splits jcw12=1`
3. App Engine will cold-start and restore from GCS backup
4. Investigate and fix VM issues before retrying

## 7. DNS/Routing Options

| Option | How | Complexity |
|--------|-----|-----------|
| **A: Keep App Engine URL** | Use App Engine dispatch rules to proxy to VM | Medium |
| **B: Direct VM access** | Point a new subdomain (e.g., `timekeeper.jcw.ai`) to VM IP | Low |
| **C: Cloudflare Tunnel** | Use Cloudflare to route `timekeeper.jcw.ai` → VM | Medium |

**Recommendation: Option B** — Create a DNS record for `timekeeper.jcw.ai` → VM static IP. Simple, no proxy complexity. Use Let's Encrypt for HTTPS.

## 8. Cost Comparison

| | App Engine | VM (e2-medium) |
|--|-----------|----------------|
| Compute | ~$30-50/mo (usage-based) | ~$25/mo (flat) |
| Storage | GCS: ~$1/mo | GCS + persistent disk: ~$2/mo |
| Complexity | Medium (version management) | Low (docker-compose) |
| Data durability | Poor (ephemeral) | Good (persistent disk) |

## 9. Prerequisites Checklist

- [ ] Persistent disk directory created on VM
- [ ] Docker and docker-compose installed on VM
- [ ] Latest GCS backup downloaded and verified
- [ ] `.env.production` file created with secrets
- [ ] Nginx configured with SSL certificate
- [ ] Backup cron tested
- [ ] Health check endpoint added to server.js
- [ ] DNS record created (if using custom domain)