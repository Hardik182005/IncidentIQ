// =============================================
// DATA.JSX — Shared constants, data, utilities
// =============================================

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#EF4444', glow: 'rgba(239,68,68,0.5)', bg: 'rgba(239,68,68,0.11)' },
  HIGH:     { color: '#F97316', glow: 'rgba(249,115,22,0.4)', bg: 'rgba(249,115,22,0.09)' },
  MEDIUM:   { color: '#F59E0B', glow: 'rgba(245,158,11,0.35)', bg: 'rgba(245,158,11,0.08)' },
  LOW:      { color: '#10B981', glow: 'rgba(16,185,129,0.3)', bg: 'rgba(16,185,129,0.07)' },
};

const INITIAL_INCIDENTS = [];

const FAKE_LOGS = [];

const FIX_COMMANDS = [
  {
    title: 'Scale connection pool limit',
    risk: 'LOW',
    cmd: `kubectl set env deployment/payments-api \\
  -n production \\
  DB_POOL_MAX=200 \\
  DB_POOL_IDLE_TIMEOUT=30000 \\
  DB_POOL_ACQUIRE_TIMEOUT=5000`,
  },
  {
    title: 'Drain stale idle connections',
    risk: 'MEDIUM',
    cmd: `psql $DATABASE_URL << 'EOF'
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < NOW() - INTERVAL '5 min'
  AND datname = 'payments_db';
EOF`,
  },
  {
    title: 'Rolling restart with health check',
    risk: 'HIGH',
    cmd: `kubectl rollout restart \\
  deployment/payments-api \\
  -n production

kubectl rollout status \\
  deployment/payments-api \\
  -n production --timeout=120s`,
  },
];

const CHAOS_SCENARIOS = [
  { id: 'db-leak',       label: 'Database Connection Leak', service: 'postgres-primary', severity: 'CRITICAL' },
  { id: 'mem-leak',      label: 'Memory Leak',               service: 'user-service',     severity: 'HIGH' },
  { id: 'cascade',       label: 'API Cascade Failure',       service: 'gateway-api',      severity: 'CRITICAL' },
  { id: 'latency-spike', label: 'Network Latency Spike',     service: 'gateway-api',      severity: 'CRITICAL' },
  { id: 'db-deadlock',   label: 'Database Deadlock Aborts',  service: 'postgres-primary', severity: 'CRITICAL' },
];

const AI_STAGES = [
  { name: 'Groq',   role: 'Initial triage & log parsing',    color: '#F59E0B', processingTime: '1.2s' },
  { name: 'Gemini', role: 'Pattern matching & correlation',  color: '#3B82F6', processingTime: '2.1s' },
  { name: 'OpenAI', role: 'Root cause synthesis',            color: '#8B5CF6', processingTime: '1.8s' },
];

const AI_CONCLUSION = 'Root cause confirmed: PostgreSQL connection pool exhaustion on payments-api triggered by a misconfigured idle_timeout (300s) introduced in deploy v2.14.1. 847 idle connections are occupying all pool slots. Recommend immediate pool drain and resetting DB_POOL_IDLE_TIMEOUT to 30s.';

const TOPOLOGY_NODES = [
  { id: 'gateway',  label: 'gateway',   x: 0.50, y: 0.10, status: 'healthy'  },
  { id: 'auth',     label: 'auth-svc',  x: 0.15, y: 0.47, status: 'healthy' },
  { id: 'payments', label: 'payments',  x: 0.50, y: 0.47, status: 'healthy' },
  { id: 'user',     label: 'user-svc',  x: 0.85, y: 0.47, status: 'healthy'  },
  { id: 'postgres', label: 'postgres',  x: 0.33, y: 0.82, status: 'healthy' },
  { id: 'cache',    label: 'redis',     x: 0.68, y: 0.82, status: 'healthy'  },
  { id: 'notif',    label: 'notif',     x: 0.88, y: 0.82, status: 'healthy' },
];

const TOPOLOGY_EDGES = [
  ['gateway','auth'], ['gateway','payments'], ['gateway','user'],
  ['auth','postgres'], ['payments','postgres'],
  ['user','cache'], ['user','notif'],
];

const TIMELINE_EVENTS = [];


const CHAOS_ROOTS = {
  'db-leak':       'PostgreSQL connections leaking — 1,200+ stale handles detected in pg_stat_activity',
  'mem-leak':      'Heap memory growing unbounded — 94% utilization on 3/5 pods, GC pausing >2s',
  'cascade':       'Gateway timeout cascade — payments + auth returning 503, downstream circuit breakers tripping',
  'latency-spike': 'Network latency spike — region transit degraded, P99 latency exceeded 15,000ms',
  'db-deadlock':   'PostgreSQL exclusive transaction deadlock — locks on tables orders and payments causing deadlock aborts',
};

function formatElapsed(secs) {
  if (secs < 60) return `00:${String(secs).padStart(2,'0')}`;
  const m = Math.floor(secs / 60), s = secs % 60;
  if (m < 60) return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
  const h = Math.floor(m / 60);
  return `${String(h).padStart(2,'0')}:${String(m%60).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}

function generateSeries(n, base, variance, spikeIdx) {
  const g = (x, mu, sig) => Math.exp(-0.5*((x-mu)/sig)**2);
  return Array.from({length: n}, (_, i) => {
    const noise = (Math.random()-0.5) * variance;
    const spike = spikeIdx != null ? variance * 4 * g(i, spikeIdx, 2.5) : 0;
    return Math.max(0, base + noise + spike);
  });
}

function createChaosIncident(scenario) {
  return {
    id: `INC-${2848 + Math.floor(Math.random()*100)}`,
    severity: scenario.severity, service: scenario.service, region: 'us-east-1',
    timestamp: 'Just now',
    rootCause: CHAOS_ROOTS[scenario.id] || 'Automated chaos scenario triggered — diagnosis running',
    confidence: 0, status: 'ACTIVE', elapsed: 0,
    tags: [scenario.id, 'chaos', 'auto'], isNew: true,
  };
}

Object.assign(window, {
  SEVERITY_CONFIG, INITIAL_INCIDENTS, FAKE_LOGS, FIX_COMMANDS,
  CHAOS_SCENARIOS, AI_STAGES, AI_CONCLUSION,
  TOPOLOGY_NODES, TOPOLOGY_EDGES, TIMELINE_EVENTS,
  formatElapsed, generateSeries, createChaosIncident,
});
