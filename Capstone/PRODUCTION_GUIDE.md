# Production Deployment & Operational Runbook
## Secure Role-Based Access Control for Hospital RAG (Capstone CSA4706)

---

## 1. Production Architecture Overview

The system runs a **fail-closed, defense-in-depth security model**:
- **Authentication**: Stateless HMAC-SHA256 JWT tokens issued by the hospital Identity Provider.
- **Pre-Retrieval Filtering**: Deterministic SQL and embedded vector metadata filtering (SQLite in Write-Ahead Logging mode).
- **Post-Generation Output Guard**: Algorithm 1 verification (`ids_ok`, `cats_ok`, `grounded`).
- **Cryptographic Audit Accountability**: Algorithm 2 monotonic SHA-256 hash chaining with thread-safe atomic serialization.
- **Separation of Duties**: System Administrator has zero access to patient clinical or identifier data.

---

## 2. Docker Container Deployment (Recommended)

### Prerequisites:
- Docker Engine 24.0+ and Docker Compose v2.0+

### Step-by-Step Deployment:
1. Clone the repository and navigate to the project directory:
   ```bash
   cd Capstone
   ```
2. Copy the environment configuration file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and set a strong production JWT secret:
   ```bash
   JWT_SECRET="e98a1f4b238dc830c29f798e09fba248c82138e698bc01d51a6938dc819fbc42"
   ENVIRONMENT="production"
   ```
4. Build and start the container in detached mode:
   ```bash
   docker compose up -d --build
   ```
5. Verify container health status:
   ```bash
   docker ps
   # Output should show: hospital-rag-rbac-service (healthy)
   ```
6. Check live system logs:
   ```bash
   docker compose logs -f hospital-rag
   ```

---

## 3. Bare-Metal / Host Deployment

### Prerequisites:
- Python 3.11+
- Virtual environment (`venv`)

### Linux / systemd Service:
Create `/etc/systemd/system/hospital-rag.service`:
```ini
[Unit]
Description=Hospital Clinical RAG RBAC Production Service
After=network.target

[Service]
Type=simple
User=appuser
Group=appgroup
WorkingDirectory=/opt/hospital-rag
EnvironmentFile=/opt/hospital-rag/.env
ExecStart=/opt/hospital-rag/.venv/bin/uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hospital-rag
sudo systemctl start hospital-rag
```

### Windows Deployment:
Double-click `run_server.bat` or run in PowerShell:
```powershell
& "..\.venv\Scripts\python.exe" -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000
```

---

## 4. Operational Health & Telemetry Probes

The service exposes standardized observability endpoints:

| Endpoint | Method | Purpose | Normal Response |
| :--- | :---: | :--- | :--- |
| **`/api/health/live`** | `GET` | Container liveness check | `{"status": "ALIVE"}` (HTTP 200) |
| **`/api/health/ready`** | `GET` | Deep readiness probe (DB, Policy, Audit Chain) | `{"ready": true, "subsystems": {...}}` (HTTP 200) |
| **`/api/metrics`** | `GET` | Operational metrics (throughput, block ratio) | JSON metrics with request counters and uptime |

---

## 5. Security Runbooks & Incident Response

### Playbook A: Cryptographic Tamper Alert (Algorithm 2)
If `/api/audit/verify` returns `TAMPER ALERT`:
1. **Immediate Quarantine**: Check the alerted entry index and timestamp reported in the response.
2. **Inspect Chain Log**:
   ```bash
   tail -n 20 logs/audit_chain.jsonl
   ```
3. **Identify Discrepancy**: Compare the computed SHA-256 against the stored `current_hash`. The system pinpoints the exact modified row.
4. **Forensic Report**: Export the tampered record to `logs/security_incident_[DATE].json` for compliance review.
5. **Restore Verified Snapshot**: Restore `audit_chain.jsonl` from the most recent immutable off-site backup.

### Playbook B: JWT Secret Key Rotation
1. Update `JWT_SECRET` in `.env` with the new 256-bit key.
2. Existing active staff sessions will be asked to re-authenticate.
3. Note: The SHA-256 audit log does *not* depend on the JWT secret; existing hash chains remain 100% valid across key rotations.

### Playbook C: Disaster Recovery & Backup
- **Relational DB Backup**:
  ```bash
  sqlite3 data/hospital.db ".backup 'backups/hospital_backup_$(date +%Y%m%d).db'"
  ```
- **Audit Log Backup**:
  ```bash
  cp logs/audit_chain.jsonl backups/audit_chain_$(date +%Y%m%d).jsonl
  ```
