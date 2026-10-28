# FestPass 2026 — Docker & Container Security

## Assessment status

This repository is being completed in stages. The assessment PDF was not present in the workspace or the available session files at implementation time. The implementation therefore follows the requirements supplied in the conversation; PDF-specific starter code, exact wording, and any additional PDF-only details remain unverified.

The actual registration number was not available in the workspace. No real registration number or derived personalized port has been invented. Set `REGNO` to the actual value and set `PORT` to `80 +` its last two digits in your local, untracked `.env`. Until then, screenshots and personalized runtime checks cannot be completed.

## Project overview and architecture

FestPass 2026 is a three-tier registration application:

- Nginx serves the frontend and reverse-proxies `/api/` requests.
- A Flask API reports its registration number, version, container hostname, and database health, and supports listing/creating registrations.
- PostgreSQL stores registrations in a named volume.

The intended Compose network topology isolates PostgreSQL: the frontend shares a network only with the API, while the API and database share a separate network. A frontend container therefore has no direct network membership in the database network.

Docker Hub repository: <https://hub.docker.com/r/harshdocs22/fest-backend>

| Personalization | Value |
|---|---|
| Name | Not provided |
| REGNO | `REGNO_PLACEHOLDER` — replace locally; not a real result |
| PORT | Not available until REGNO is known; calculate as `80 +` the last two REGNO digits |
| Docker Hub username | `harshdocs22` |

## Prerequisites

- Docker Desktop with the Linux container engine and Docker Compose v2.
- A Windows PowerShell terminal.
- A valid REGNO and a local `.env` file for personalized runs.
- Trivy for the actual image reports; Cosign and Docker Hub authentication for publishing/signing stages.

## Stage 1 — backend containerisation

The initial image intentionally uses the assessment's `python:3.9` baseline. Dependency installation precedes `app.py` copying to preserve the dependency layer cache.

```powershell
Set-Location 'C:\Desktop\Devops_CA2\202401100200148_Devops_Assignment'
docker build -t fest-backend:0.1 .\backend
docker image ls fest-backend
docker image inspect fest-backend:0.1 --format '{{.Size}}'
```

Once `REGNO` and its calculated port are set, a temporary Stage 1 run and checks are:

```powershell
$env:REGNO = 'YOUR_ACTUAL_REGNO'
$port = 80 + [int]$env:REGNO.Substring($env:REGNO.Length - 2)
docker run -d --name backend -p "${port}:5000" -e REGNO="$env:REGNO" fest-backend:0.1
docker ps --filter 'name=backend'
curl.exe "http://localhost:$port/api/health"
docker logs backend
docker rm -f backend
```

Without a database, `database_status` should be false at this stage. Run the test only with your actual REGNO; capture the real output yourself.

## Stage 2 — Compose stack

Copy the safe template and replace every marked value in `.env` on your computer. Its `8080` is a syntactically valid example only, not the personalized port; replace it with `80 +` the last two actual REGNO digits. Do not commit `.env`.

```powershell
Copy-Item .env.example .env
# Edit .env: REGNO=<actual value>, PORT=<80 + last two REGNO digits>, DB_PASSWORD=<strong local password>
docker compose config
docker compose up -d --build
```

The backend uses `DB_HOST=db`; its start is gated on the PostgreSQL `pg_isready` health check. PostgreSQL data persists in the named volume. The frontend is attached only to the frontend/backend network; the database is attached only to the backend/database network.

API endpoints:

- `GET /api/health` — registration number, application version, container hostname, database status.
- `GET /api/registrations` — list persisted registrations.
- `POST /api/registrations` — JSON body `{"name":"Example attendee","email":"attendee@example.test"}`.

The frontend is intended to be opened at `http://localhost:<PORT>`. Test a registration using the form, then list it in the page. Restart and check persistence:

```powershell
# Submit and list registrations through the API (PowerShell-native JSON avoids
# Windows curl argument-quoting differences).
$port = [int]((Get-Content .env | Where-Object { $_ -match '^PORT=' } | Select-Object -First 1) -replace '^PORT=', '')
$api = "http://localhost:$port/api"
$first = @{ name = 'Attendee One'; email = 'one@example.test' } | ConvertTo-Json -Compress
$second = @{ name = 'Attendee Two'; email = 'two@example.test' } | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "$api/registrations" -Method Post -ContentType 'application/json' -Body $first
Invoke-RestMethod -Uri "$api/registrations" -Method Post -ContentType 'application/json' -Body $second
Invoke-RestMethod -Uri "$api/registrations" | ConvertTo-Json -Compress

# From the frontend container, this should report that db cannot be found.
docker compose exec frontend busybox nslookup db

docker compose down
docker compose up -d
docker volume ls
# Confirm the earlier registration records are still returned.
Invoke-RestMethod -Uri "$api/registrations" | ConvertTo-Json -Compress
```

`docker compose down` intentionally does not remove the named database volume. Do not use `-v` for the persistence test.

Local Stage 2 checks ran with the clearly marked `REGNO_PLACEHOLDER` and example port `8080`: two API registrations were listed again after `docker compose down` / `up -d`; the PostgreSQL named volume remained; the frontend and database had disjoint Docker networks; and `busybox nslookup db` from the frontend returned `Can't find db: No answer`. These are local functional checks, not personalized screenshots or real attendee data.

## Stage 3 — Trivy

The initial image was actually scanned using Trivy 0.76.1. The unedited table output is saved in `reports/trivy-before.txt`; its structured JSON was used to count findings with a fix version separately from those without one. The initial local image size was measured with `docker image inspect`.

| Image | CRITICAL fixed | CRITICAL unfixed | HIGH fixed | HIGH unfixed | Image size |
|---|---:|---:|---:|---:|---:|
| `fest-backend:0.1` (Python 3.9 baseline) | 217 | 17 | 1,802 | 447 | 412,524,427 bytes (413 MB) |
| `fest-backend:0.2` (maintained runtime) | 0 | 0 | 5 | 44 | 50,039,972 bytes (50 MB) |

“Fix version available” means Trivy reports a version that addresses the finding; it does not mean that affected software in the scanned image is already fixed. “No known fix” means the Trivy result has no `FixedVersion`. Counts are findings, not unique CVE identifiers. The baseline totals are CRITICAL 234 and HIGH 2,249; after the upgrade they are CRITICAL 0 and HIGH 49. The `0.2` image uses the patch-pinned `python:3.13.18-slim-trixie`, pinned current Flask/Werkzeug/psycopg2-binary/Gunicorn packages, a non-root UID, read-only root filesystem in Compose, dropped Linux capabilities, and `no-new-privileges`.

Required checks:

```powershell
$reports = (Get-Location).Path + '\reports'
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${reports}:/reports" -v fest_trivy_cache:/cache aquasec/trivy:0.76.1 --cache-dir /cache image --scanners vuln --format table --output /reports/trivy-before.txt fest-backend:0.1
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${reports}:/reports" -v fest_trivy_cache:/cache aquasec/trivy:0.76.1 --cache-dir /cache image --scanners vuln --format table --output /reports/trivy-after.txt fest-backend:0.2
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${reports}:/reports" -v fest_trivy_cache:/cache aquasec/trivy:0.76.1 --cache-dir /cache image --scanners vuln --severity CRITICAL --ignore-unfixed --exit-code 1 fest-backend:0.2
$trivyExitCode = $LASTEXITCODE
"Actual required-check exit code: $trivyExitCode"
```

The required CRITICAL check was run against `fest-backend:0.2`; actual PowerShell exit code: **0**. Both reports contain the genuine Trivy 0.76.1 table output. The scan was performed using the official Trivy container because a host Trivy executable was not installed.

## Stage 4 — Docker Hub

The fixed backend was built locally with `APP_VERSION=1.0.0` and locally tagged as both `harshdocs22/fest-backend:1.0.0` and `harshdocs22/fest-backend:1.0`. Compose references the versioned image and no longer builds the backend. The local Compose run returned version `1.0.0`, database status `true`, and both existing registration rows. This used the local image tag; it is not evidence of a published registry image.

Local build/tag commands:

```powershell
docker build --build-arg APP_VERSION=1.0.0 -t fest-backend:1.0.0 .\backend
docker tag fest-backend:1.0.0 harshdocs22/fest-backend:1.0.0
docker tag fest-backend:1.0.0 harshdocs22/fest-backend:1.0
```

The public tag lookup returned HTTP 404, and the actual `docker push harshdocs22/fest-backend:1.0.0` attempt failed with `insufficient_scope: authorization failed`. No tag was published and no registry digest is available. Create/confirm the `fest-backend` repository under `harshdocs22` and authenticate with a Docker Hub credential that has write access. Do not put a password/token in a command or chat; use the interactive login locally:

```powershell
docker login --username harshdocs22
docker push harshdocs22/fest-backend:1.0.0
docker push harshdocs22/fest-backend:1.0
```

Record the digest from the successful `1.0.0` push output. Do not infer it from the local image ID. After successful push, pull and run the registry image and check it against the existing database volume:

```powershell
docker compose pull backend
docker compose up -d
docker compose ps
$port = [int]((Get-Content .env | Where-Object { $_ -match '^PORT=' } | Select-Object -First 1) -replace '^PORT=', '')
Invoke-RestMethod -Uri "http://localhost:$port/api/health" | ConvertTo-Json -Compress
Invoke-RestMethod -Uri "http://localhost:$port/api/registrations" | ConvertTo-Json -Compress
```

Do not remove local images until the registry image is confirmed available and the running application is verified to use it. The actual registry push/digest and Docker Hub browser screenshots remain pending until repository write access and manual evidence capture are available.

## Stage 5 — Cosign

The `1.0.1` image was built locally with `APP_VERSION=1.0.1` and was **not signed**. It has not been published because Docker Hub denied write access. Cosign is not installed, no signing key was generated, and no `cosign.pub` is present; these are intentionally not fabricated. `.gitignore` already excludes `*.key` before any key-generation step.

After Docker Hub publishing access is available, check the installed Cosign syntax and generate a password-protected key pair locally. Do not send the passphrase to chat or add `cosign.key` to Git:

```powershell
cosign version
cosign generate-key-pair --help
cosign generate-key-pair
git check-ignore cosign.key
git status --short
```

`cosign generate-key-pair` prompts for the private-key password and writes `cosign.key` and `cosign.pub`. Confirm that Git ignores `cosign.key`; stage/commit only the public key:

```powershell
git add cosign.pub
git diff --cached --name-only
git commit -m "Add Cosign public verification key"
```

After `1.0.0` has actually been pushed and its immutable digest recorded, inspect `cosign sign --help` / `cosign verify --help`, then sign and verify that digest. Replace the marked string only with the digest from the successful registry push:

```powershell
$digest = 'sha256:<DIGEST_FROM_SUCCESSFUL_1.0.0_PUSH>'
cosign sign --key .\cosign.key "harshdocs22/fest-backend@$digest"
cosign verify --key .\cosign.pub "harshdocs22/fest-backend@$digest"
```

Build and publish `1.0.1` without running `cosign sign`, then confirm verification rejects it:

```powershell
docker build --build-arg APP_VERSION=1.0.1 -t fest-backend:1.0.1 .\backend
docker tag fest-backend:1.0.1 harshdocs22/fest-backend:1.0.1
docker push harshdocs22/fest-backend:1.0.1
cosign verify --key .\cosign.pub harshdocs22/fest-backend:1.0.1
$verifyExitCode = $LASTEXITCODE
if ($verifyExitCode -eq 0) { throw 'Unexpectedly verified an unsigned image.' }
Write-Output "Verification rejection exit code: $verifyExitCode"
```

No signing, verification, or unsigned-image rejection result is claimed until these commands are run and their actual output confirms it.

## Evidence checklist

Capture genuine, unedited screenshots yourself; no screenshots are generated by this project. Include the full terminal/browser window and the prompt/address bar details required by the assessment.

- `S1-2.png` — image build, listing, and size.
- `S1-3.png` — container status, health response, and logs.
- `S2-2.png` — frontend-to-database isolation diagnostic.
- `S2-3.png` — browser page with your REGNO and two registrations.
- `S2-4.png` — registrations after restart and named volume listing.
- `S3-1.png` — initial Trivy report and severity totals.
- `S3-3.png` — final Trivy report and actual successful CRITICAL exit-code check.
- `S4-1.png` — Docker Hub push output including the digest.
- `S4-2.png` — Docker Hub Tags page showing `1.0.0` and the username.
- `S4-3.png` — application running from the published image.
- `S5-1.png` — safe public-key evidence.
- `S5-2.png` — signing by digest.
- `S5-3.png` — successful verification.
- `S5-4.png` — rejection of unsigned `1.0.1`.

## AI tools

GitHub Copilot assisted with implementation and documentation. All terminal output, scans, image digests, registry actions, and cryptographic verification must come from the actual local tools and remain independently verifiable.

## Incomplete steps

- The PDF could not be located, so PDF-specific starter code and unquoted requirements could not be independently extracted.
- REGNO and the derived PORT are not available; personalized execution and evidence need the actual value.
- Trivy and Cosign were not installed as host commands at initial inspection; the actual Trivy scan/check used the official pinned Trivy container.
- Docker Hub tag lookup returned 404 and the `1.0.0` push attempt returned `insufficient_scope: authorization failed`; no image was published and no registry digest is available. The Docker Hub repository/write authorization must be corrected.
- GitHub push has not been performed; the repository contains unfinished external publishing/signing stages and must not be presented as complete.
- REGNO is still a placeholder, so personalized port/runtime evidence is pending.
- Cosign key generation, public-key commit, signing, verification, and unsigned `1.0.1` rejection remain pending.
- Required screenshots are manual evidence; none have been fabricated or captured.
