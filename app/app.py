

import os
import time
from flask import Flask, request, jsonify

USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
APP_VERSION = os.getenv("APP_VERSION", "v1")
PORT = int(os.getenv("PORT", "8080"))

app = Flask(__name__)

# In-memory fallback
end_time_in_memory = None

# Optional Redis client
r = None
if USE_REDIS:
    import redis
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

TIMER_KEY = os.getenv("TIMER_KEY", "timer:end")

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/readyz")
def readyz():
    if USE_REDIS:
        try:
            r.ping()
        except Exception:
            return "redis not ready", 503
    return "ready", 200

@app.post("/start")
def start():
    data = request.get_json(silent=True) or {}
    seconds = int(data.get("seconds", 60))
    seconds = max(1, min(seconds, 86400))  # clamp between 1s and 24h

    end_ts = int(time.time()) + seconds
    if USE_REDIS:
        # store end timestamp and set TTL so key auto-expires
        r.set(TIMER_KEY, str(end_ts), ex=seconds)
        backend = "redis"
    else:
        global end_time_in_memory
        end_time_in_memory = end_ts
        backend = "memory"

    return jsonify({
        "message": "timer started",
        "duration_seconds": seconds,
        "backend": backend,
        "app_version": APP_VERSION
    }), 200

@app.get("/remaining")
def remaining():
    now = int(time.time())
    if USE_REDIS:
        end_ts = r.get(TIMER_KEY)
        if not end_ts:
            return jsonify({"remaining": 0, "status": "no active timer", "app_version": APP_VERSION}), 200
        end_ts = int(end_ts)
    else:
        global end_time_in_memory
        if not end_time_in_memory:
            return jsonify({"remaining": 0, "status": "no active timer", "app_version": APP_VERSION}), 200
        end_ts = end_time_in_memory

    rem = max(0, end_ts - now)
    status = "running" if rem > 0 else "finished"
    return jsonify({"remaining": rem, "status": status, "app_version": APP_VERSION}), 200

@app.get("/")
def root():
    return jsonify({
        "message": "Countdown Timer API",
        "usage": {
            "POST /start": {"body": {"seconds": 60}},
            "GET /remaining": {},
            "GET /healthz": {},
            "GET /readyz": {}
        },
        "backend": "redis" if USE_REDIS else "memory",
        "app_version": APP_VERSION
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
