import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


def _ts(base: datetime, delta_seconds: float) -> str:
    return (base + timedelta(seconds=delta_seconds)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def generate_chaos_logs(scenario: str) -> List[Dict[str, Any]]:
    dispatch = {
        "db_connection_leak": _db_connection_leak,
        "memory_leak": _memory_leak,
        "api_cascade": _api_cascade,
    }
    return dispatch[scenario]()


# ── db_connection_leak ────────────────────────────────────────────────────────

def _db_connection_leak() -> List[Dict[str, Any]]:
    logs: List[Dict[str, Any]] = []
    base = datetime.now(timezone.utc) - timedelta(minutes=10)
    total = 5000
    window = 600.0  # seconds

    phases = [
        (0,   60,  5,   "INFO"),
        (60,  120, 10,  "INFO"),
        (120, 180, 20,  "WARN"),
        (180, 240, 35,  "WARN"),
        (240, 300, 52,  "WARN"),
        (300, 360, 71,  "ERROR"),
        (360, 420, 88,  "ERROR"),
        (420, 480, 96,  "ERROR"),
        (480, 540, 100, "ERROR"),
        (540, 600, 100, "ERROR"),
    ]

    services = ["auth-service", "user-api", "postgres", "pgbouncer"]

    for i in range(total):
        t = (i / total) * window
        conn = 5
        level = "INFO"
        for start, end, c, lvl in phases:
            if start <= t < end:
                conn = c
                level = lvl
                break

        ts = _ts(base, t)
        service = random.choice(services)

        if conn < 20:
            msg = random.choice([
                f"Connection acquired from pool [{conn}/100 active]",
                f"Query executed in {random.randint(1, 45)}ms",
                f"Transaction committed successfully for request #{random.randint(10000, 99999)}",
                f"Connection returned to pool [{conn}/100 active]",
                f"Health check OK — pool utilization {conn}% on {service}",
            ])
        elif conn < 52:
            msg = random.choice([
                f"Pool utilization at {conn}% — scale-up recommended immediately",
                f"Idle connection timeout warning: {conn} connections idle > 60s",
                f"Slow query detected: {random.randint(200, 800)}ms on SELECT FROM orders",
                f"Connection pool growing: {conn}/100 slots used",
                f"pgbouncer: client conn waiting {random.randint(80, 300)}ms for server conn",
                f"WARNING: connection churn detected — {random.randint(5, 20)} connects/sec",
            ])
        elif conn < 96:
            msg = random.choice([
                f"sqlalchemy.exc.TimeoutError: Connection pool timeout after 30000ms [{conn}/100]",
                f"FATAL: could not connect to postgres: too many connections ({conn}/100)",
                f"Connection acquire timeout: waiting {random.randint(5000, 29000)}ms exceeded",
                f"pg connection refused: max_connections=100 reached, current={conn}",
                f"ERROR: pool exhaustion imminent — {conn}/100 connections active",
                f"Circuit breaker HALF_OPEN: connection success rate {100 - conn}%",
                f"RETRY {random.randint(1,3)}/3: acquiring DB connection after timeout on {service}",
            ])
        else:
            stacks = [
                (
                    "sqlalchemy.exc.TimeoutError: QueuePool limit of size 100 overflow 0 reached, "
                    "connection timed out, timeout 30\n"
                    "  File \"/app/db/pool.py\", line 142, in acquire\n"
                    "    raise TimeoutError(f\"Connection pool exhausted\")\n"
                    "  sqlalchemy.exc.TimeoutError: QueuePool exhausted"
                ),
                "FATAL: max_connections=100 exceeded — rejecting new connections from all clients",
                "pg_stat_activity: 100/100 connections occupied, 0 available",
                "CRITICAL: Connection pool exhausted — returning HTTP 503 to all upstream callers",
                (
                    "pg connection refused: FATAL: remaining connection slots are reserved "
                    "for non-replication superuser connections"
                ),
                (
                    "sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) "
                    "FATAL: remaining connection slots reserved for superuser"
                ),
                f"ERROR: Transaction rollback — connection refused by postgres-primary after {random.randint(3, 10)} retries",
                "health_check: payments-api → DEGRADED (HTTP 503) — DB unavailable",
            ]
            msg = random.choice(stacks)

        logs.append({
            "timestamp": ts,
            "severity": level,
            "service": service,
            "message": msg,
            "meta": {"connection_count": conn},
        })

    return sorted(logs, key=lambda x: x["timestamp"])


# ── memory_leak ───────────────────────────────────────────────────────────────

def _memory_leak() -> List[Dict[str, Any]]:
    logs: List[Dict[str, Any]] = []
    base = datetime.now(timezone.utc) - timedelta(minutes=8)
    total = 2000
    window = 480.0

    phases = [
        (0,   90,  60,  "INFO"),
        (90,  150, 72,  "WARN"),
        (150, 210, 81,  "WARN"),
        (210, 270, 89,  "ERROR"),
        (270, 330, 94,  "ERROR"),
        (330, 360, 99,  "ERROR"),
        (360, 480, -1,  "WARN"),
    ]

    services = ["recommendation-engine", "redis-cache", "kubelet", "kube-scheduler"]
    restart_count = 0

    for i in range(total):
        t = (i / total) * window
        ts = _ts(base, t)
        service = random.choice(services)

        mem = 60
        level = "INFO"
        for start, end, m, lvl in phases:
            if start <= t < end:
                mem = m
                level = lvl
                break

        if mem == -1:
            restart_count += 1
            msg = random.choice([
                f"OOMKilled: recommendation-engine-{random.randint(1000, 9999)} — exit code 137",
                f"kubelet: pod recommendation-engine restarted (total restarts: {restart_count})",
                f"CrashLoopBackOff: recommendation-engine — {restart_count} restarts in 5m",
                f"Pod restarted — heap cleared, starting at {random.randint(15, 30)}% memory",
                f"Alert: recommendation-engine restart loop — {restart_count}/5 replicas cycling",
                f"PodDisruptionBudget: {min(restart_count, 3)}/3 replicas simultaneously restarting",
            ])
            level = "ERROR" if restart_count >= 3 else "WARN"
        elif mem < 72:
            msg = random.choice([
                f"Heap memory: {mem}% ({random.randint(1200, 1470)}MB / 2048MB)",
                f"GC cycle completed in {random.randint(40, 130)}ms — {mem}% heap utilized",
                f"Cache miss rate: {random.randint(5, 14)}% — within normal bounds",
                f"recommendation-engine processed {random.randint(200, 600)} recs/s",
            ])
        elif mem < 90:
            msg = random.choice([
                f"WARNING: heap at {mem}% ({random.randint(1500, 1840)}MB / 2048MB) — growing",
                f"GC pressure: full GC every {random.randint(5, 15)}s, pausing {random.randint(200, 900)}ms",
                f"Object alloc rate {random.randint(50, 160)}MB/s — possible leak in recommendation cache",
                f"redis-cache: eviction rate up — maxmemory {mem}% utilized",
                f"Large object heap: {random.randint(200, 500)}MB unreachable objects pending GC",
            ])
        else:
            msg = random.choice([
                f"CRITICAL: heap at {mem}% — OOM kill imminent on recommendation-engine",
                f"GC pause >2s at {mem}% heap — application frozen, requests queuing",
                f"java.lang.OutOfMemoryError: Java heap space — {mem}% utilization",
                f"recommendation-engine pod {random.randint(1, 3)}/5: memory_pressure=true",
                f"Kubernetes: evicting recommendation-engine-{random.randint(1000, 9999)} — {mem}% > 90% limit",
                f"OOM score: {random.randint(850, 999)} — pod scheduled for termination",
            ])

        logs.append({
            "timestamp": ts,
            "severity": level,
            "service": service,
            "message": msg,
            "meta": {"memory_pct": max(mem, 0)},
        })

    return sorted(logs, key=lambda x: x["timestamp"])


# ── api_cascade ───────────────────────────────────────────────────────────────

def _api_cascade() -> List[Dict[str, Any]]:
    logs: List[Dict[str, Any]] = []
    base = datetime.now(timezone.utc) - timedelta(minutes=6)
    total = 3000
    window = 360.0

    for i in range(total):
        t = (i / total) * window
        ts = _ts(base, t)

        if t < 30:
            service = random.choice(["payment-service", "order-service", "api-gateway"])
            msg = random.choice([
                f"POST /api/payments/charge 200 {random.randint(45, 110)}ms",
                f"POST /api/orders/create 200 {random.randint(30, 80)}ms",
                f"GET /api/health 200 2ms",
                f"Payment processed successfully for order #{random.randint(10000, 99999)}",
            ])
            level = "INFO"

        elif t < 60:
            service = "payment-service"
            lat = random.randint(600, 3500)
            msg = random.choice([
                f"POST /api/payments/charge 200 {lat}ms — latency degraded",
                f"Stripe API timeout after {lat}ms — retrying ({random.randint(1,2)}/3)",
                f"payment-service: DB query slow — {lat}ms on payments.transactions",
                f"WARNING: P99 latency {lat}ms exceeds 500ms SLO threshold",
                f"Connection pool warming: {random.randint(50, 90)}% utilization",
            ])
            level = "WARN"

        elif t < 120:
            service = random.choice(["payment-service", "order-service"])
            retry = random.randint(1, 5)
            backoff = int(2 ** retry * 100)
            if service == "payment-service":
                msg = random.choice([
                    f"POST /api/payments/charge 503 {random.randint(5000, 30000)}ms — circuit breaker OPEN",
                    "payment-service: connection timeout to payment-processor-api after 30s",
                    f"ERROR: payment gateway returned 503 after {random.randint(3, 10)}s — circuit OPEN",
                    "Circuit breaker OPEN on payment-service/charge — rejecting all requests",
                ])
                level = "ERROR"
            else:
                msg = random.choice([
                    f"Retry {retry}/5 for payment on order #{random.randint(10000, 99999)} — backoff {backoff}ms",
                    f"order-service: payment attempt {retry} failed — exponential backoff {backoff}ms",
                    f"order-service: {random.randint(50, 250)} orders queued waiting for payment retry",
                    f"Retry storm: {random.randint(200, 800)} concurrent retry requests → payment-service",
                ])
                level = "ERROR" if retry >= 3 else "WARN"

        elif t < 240:
            service = random.choice(["api-gateway", "order-service", "payment-service", "notification-service"])
            req_rate = random.randint(1000, 6000)
            if service == "api-gateway":
                msg = random.choice([
                    f"GET /api/orders 503 — upstream payment-service unavailable [{req_rate} req/s]",
                    f"api-gateway: rate limit triggered — {req_rate} req/s from order-service retries",
                    "Load balancer: health check FAILED for payment-service — removed from pool",
                    f"api-gateway: upstream timeout 30s — returning 503 to {random.randint(200, 2000)} clients",
                    f"ERROR: 503 cascade — {random.randint(500, 5000)} queued requests timing out",
                ])
                level = "ERROR"
            else:
                msg = random.choice([
                    f"CRITICAL: order-service retry queue depth {random.randint(5000, 50000)} — overloaded",
                    "payment-service: 0/5 pods healthy — rolling restart triggered",
                    f"DeadLetterQueue: {random.randint(1000, 12000)} failed payment events accumulating",
                    "notification-service: webhook delivery failing (collateral damage from cascade)",
                    f"order-service memory: {random.randint(85, 98)}% — retry storm causing heap pressure",
                ])
                level = "ERROR"

        else:
            service = random.choice(["payment-service", "order-service", "api-gateway"])
            msg = random.choice([
                "Circuit breaker HALF_OPEN: testing payment-service recovery probe",
                f"payment-service pod {random.randint(1, 5)}/5 healthy — reintroducing to pool",
                f"api-gateway: retry rate dropping {random.randint(1000, 3000)} → {random.randint(50, 400)} req/s",
                f"order-service: queue draining — {random.randint(100, 2000)} orders processing",
                "payment-service: health check PASSING — adding back to load balancer",
                f"Error rate recovering: {random.uniform(8, 15):.1f}% → {random.uniform(1, 4):.1f}%",
            ])
            level = "WARN" if t < 300 else "INFO"

        logs.append({"timestamp": ts, "severity": level, "service": service, "message": msg})

    return sorted(logs, key=lambda x: x["timestamp"])
