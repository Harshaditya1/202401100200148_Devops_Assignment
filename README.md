# 🐳 FestPass 2026 — Docker & Container Security

A secure, containerized three-tier web application built as part of the **Docker & Container Security Practical Assessment (CA-2)**. FestPass enables users to register for college technical-fest events through a web interface backed by a Python Flask API and PostgreSQL database.

The project demonstrates containerization, service orchestration, network isolation, persistent storage, vulnerability scanning, versioned image publishing, and container image signing.

## 🚀 Project Overview

FestPass 2026 consists of three services:

- **Frontend:** Nginx serving the registration interface.
- **Backend:** Python Flask REST API for registration management.
- **Database:** PostgreSQL for persistent registration storage.

The application is orchestrated using Docker Compose, scanned using Trivy, published to Docker Hub, and secured with Cosign image signatures.

## 🏗️ Architecture

```text
                 User / Browser
                       |
                       | HTTP : PORT
                       v
              +------------------+
              |     Frontend     |
              |  Nginx + HTML    |
              +------------------+
                       |
                 Frontend Network
                       |
                       v
              +------------------+
              |     Backend      |
              |   Python Flask   |
              |     Port 5000    |
              +------------------+
                       |
                  Database Network
                       |
                       v
              +------------------+
              |    PostgreSQL    |
              |   Persistent DB  |
              +------------------+
                       |
                  Named Volume
```

**Security design:** The frontend and database are placed on separate networks. The backend connects to both networks, allowing the frontend to access the API without direct network access to PostgreSQL.

## ✨ Features

- Three-tier application architecture.
- Dockerfile-based backend containerization.
- Multi-service orchestration with Docker Compose.
- PostgreSQL health checks and service dependency management.
- Named volume for persistent database storage.
- Isolated Docker networks.
- REST API for creating and listing registrations.
- Configurable application version and registration number.
- Trivy vulnerability scanning and remediation.
- Versioned Docker images published to Docker Hub.
- Cosign image signing and signature verification.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | REST API |
| PostgreSQL | Relational database |
| HTML, CSS, JavaScript | Frontend |
| Nginx | Web server and reverse proxy |
| Docker | Containerization |
| Docker Compose | Service orchestration |
| Trivy | Vulnerability scanning |
| Docker Hub | Container image registry |
| Cosign | Image signing and verification |
| Git and GitHub | Version control and submission |

## 📂 Project Structure

```text
REGNO-docker-assessment/
├── README.md
├── compose.yaml
├── .env.example
├── .gitignore
├── cosign.pub
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── frontend/
│   ├── index.html
│   └── nginx.conf
├── reports/
│   ├── trivy-before.txt
│   └── trivy-after.txt
└── screenshots/
```

## ⚙️ Prerequisites

Install the following tools before running the project:

- Docker Desktop or Docker Engine with Docker Compose.
- Git.
- Trivy.
- Cosign.
- A Docker Hub account.

## 🔧 Setup and Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <REGNO>-docker-assessment
```

### 2. Configure environment variables

Create a local `.env` file using `.env.example` as a reference.

```bash
cp .env.example .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Configure a strong database password in `.env`. Never commit this file to GitHub.

### 3. Start the application

```bash
docker compose up -d --build
```

Check the running containers:

```bash
docker compose ps
```

View service logs:

```bash
docker compose logs
```

Open the application at:

```text
http://localhost:<PORT>
```

Replace `<PORT>` with the port calculated from your registration number according to the assessment instructions.

### 4. Stop the application

```bash
docker compose down
```

Database data is stored in a named volume and should persist across container recreation. Do not use `docker compose down -v` when you want to retain the database data.

## 🔌 API Endpoints

The backend exposes the following endpoints through the Nginx reverse proxy.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Checks backend and database status |
| GET | `/api/registrations` | Lists registered participants |
| POST | `/api/registrations` | Creates a new registration |

### Example registration request

```bash
curl -X POST http://localhost:<PORT>/api/registrations \
  -H "Content-Type: application/json" \
  -d '{"name":"Asha","event":"Hackathon"}'
```

Example response:

```json
{
  "id": 1,
  "name": "Asha",
  "event": "Hackathon"
}
```

The returned ID depends on the actual database state.

## 🔒 Container Security

### Non-root execution

The hardened backend image is configured to run as a non-root user, reducing unnecessary privileges inside the container.

### Network isolation

The Compose configuration separates frontend-to-backend communication from backend-to-database communication. The database is not directly exposed to the frontend network.

### Persistent storage

A named Docker volume stores PostgreSQL data so that registrations can survive container recreation.

### Environment variables

Database credentials and other configuration values are supplied through environment variables. Sensitive configuration is excluded from version control.

### Vulnerability scanning with Trivy

The initial backend image is scanned before hardening. The updated image is scanned again after upgrading the base image and dependencies.

Reports are stored in:

- `reports/trivy-before.txt`
- `reports/trivy-after.txt`

### Image signing with Cosign

The release image is signed by its immutable registry digest and verified against the committed public key, `cosign.pub`.

The private signing key, `cosign.key`, must remain private and must never be committed to GitHub.

## 📦 Docker Hub

**Docker Hub username:** `harshdocs22`

**Repository:** [harshdocs22/fest-backend](https://hub.docker.com/r/harshdocs22/fest-backend)

### Build the release image

After completing the hardened image stage:

```bash
docker build \
  --build-arg APP_VERSION=1.0.0 \
  -t harshdocs22/fest-backend:1.0.0 \
  -t harshdocs22/fest-backend:1.0 \
  ./backend
```

### Publish the versioned images

```bash
docker login -u harshdocs22

docker push harshdocs22/fest-backend:1.0.0
docker push harshdocs22/fest-backend:1.0
```

Record the actual published image digest after a successful push.

**Published image digest:** `REPLACE_WITH_ACTUAL_1.0.0_DIGEST`

Do not replace this placeholder until the registry returns the real digest.

## 🛡️ Trivy Vulnerability Comparison

Populate this table using the actual Trivy reports generated on your machine.

| Metric | Initial Image (`0.1`) | Hardened Image (`0.2`) |
|---|---:|---:|
| CRITICAL vulnerabilities | Pending scan | Pending scan |
| HIGH vulnerabilities | Pending scan | Pending scan |
| Image size | Pending measurement | Pending measurement |

Run the required CRITICAL vulnerability check:

```bash
trivy image --severity CRITICAL --ignore-unfixed --exit-code 1 fest-backend:0.2
```

An exit code of `0` means no CRITICAL vulnerabilities with available fixes were found under the specified scan policy. It does not mean the image is free of every possible vulnerability.

## ✍️ Image Signing and Verification

After pushing version `1.0.0`, obtain its actual immutable digest and sign the image using Cosign.

```bash
cosign sign --key cosign.key \
  harshdocs22/fest-backend@sha256:<ACTUAL_DIGEST>
```

Verify the signature:

```bash
cosign verify --key cosign.pub \
  harshdocs22/fest-backend@sha256:<ACTUAL_DIGEST>
```

Replace `<ACTUAL_DIGEST>` with the real digest returned by Docker Hub.

The assessment also requires publishing an unsigned `1.0.1` image and demonstrating that signature verification rejects it.

## 🧪 Testing and Evidence

The `screenshots/` directory contains the assessment evidence captured from the actual development environment.

Evidence covers:

- Backend image build and execution.
- Docker Compose networking and database persistence.
- Initial and hardened Trivy scans.
- Docker Hub publishing and registry-based execution.
- Cosign signing, verification, and unsigned-image rejection.

Only genuine screenshots and actual test results should be included.

## 🤖 AI Assistance

**AI tool used:** GitHub Copilot.

**Purpose:** Assistance with Docker configuration, application containerization, troubleshooting, security hardening, documentation, and command explanations.

All commands, test results, vulnerability reports, image publication, and signature verification must be validated against the actual execution environment.

## 📌 Assessment Status

Update this section as each stage is completed.

- [ ] Stage 1 — Backend containerization.
- [ ] Stage 2 — Docker Compose stack and network isolation.
- [ ] Stage 3 — Trivy scanning and remediation.
- [ ] Stage 4 — Versioned Docker Hub publication.
- [ ] Stage 5 — Cosign signing and verification.
- [ ] Final screenshots and GitHub submission.

**Incomplete steps or blockers:** Document any task that could not be completed and explain its actual status.

## 👨‍💻 Author

**Name:** Harsh Aditya 
**Registration Number:** Replace with your actual REGNO  
**Docker Hub:** [harshdocs22](https://hub.docker.com/u/harshdocs22)

---

*FestPass 2026 — Building, securing, and verifying containerized applications.*
