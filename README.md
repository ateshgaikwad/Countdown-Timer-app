
# Kubernetes Countdown Timer

A tiny API to start and check a countdown timer. Two modes:
- **In-memory** (fastest to demo)
- **Redis-backed** (resilient; uses TTL to auto-expire)

## Endpoints
- `POST /start` body: `{"seconds": 60}`
- `GET /remaining`
- `GET /healthz`
- `GET /readyz`

## Build & Push Image
Replace the registry/tag with your own. Example with GHCR:

```bash
# From repo root
docker build -t ghcr.io/<your-username>/countdown-timer:latest ./app
docker push ghcr.io/<your-username>/countdown-timer:latest
``
