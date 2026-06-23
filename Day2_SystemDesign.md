# Day 2 — System Design
### Tuesday, June 23 | Goal: Design 3 systems confidently end to end

---

## The HLD Framework — Internalize This

Use this structure for every system design question. It keeps you in control.

| Step | What to do | Time |
|---|---|---|
| 1. Clarify | Requirements, scale, consistency, read/write ratio, latency SLA | 5 min |
| 2. Estimate | Data volume, requests/sec, storage needs | 3 min |
| 3. High-level boxes | Draw components, label data flow | 10 min |
| 4. Deep dive | Pick 1-2 hardest components — schema, APIs, bottlenecks | 20 min |
| 5. Trade-offs | Failure handling, what you'd do differently at larger scale | 10 min |

### Standard Clarifying Questions (memorize these)
```
Scale:        "How many users? Requests/sec? Data volume?"
Consistency:  "Do we need strong consistency or is eventual okay?"
Read/write:   "Is this read-heavy, write-heavy, or balanced?"
Latency:      "Any SLA? Sub-100ms reads? Batch is fine for writes?"
Availability: "What's the uptime requirement? 99.9%? 99.99%?"
Scope:        "Should I focus on a specific component or the full system?"
```

### Drawing the boxes (always say these out loud)
```
Client → API Gateway → Service → Database
                     ↓
                  Queue (Kafka/SQS)
                     ↓
                  Worker → Result Store
```

---

## System 1 — Distributed Word Count / Log Analytics

This is the most likely technical deep-dive since it directly extends the coding problem.

### Clarifying Questions
```
"Are we building a batch system, streaming, or both?"
"What's the input — log files on S3, a Kafka topic, raw text files?"
"Do we need real-time results or is T+5min acceptable?"
"What queries do we serve — top-K globally, per-document, time-windowed?"
"How long do we retain data?"
```

### Architecture

```
INPUT LAYER
  S3 / HDFS                 → batch files
  Kafka topic               → streaming events

PROCESSING LAYER
  Batch:    Spark / Hadoop MapReduce
  Stream:   Kafka + Flink or Spark Streaming

STORAGE LAYER
  Raw counts:    Cassandra or DynamoDB  (word → count, partitioned by word)
  Top-K cache:   Redis (pre-computed, refreshed periodically)
  Analytics:     ClickHouse / BigQuery  (for time-windowed queries)

QUERY LAYER
  REST API → hits Redis for top-K, DB for arbitrary lookups
```

### MapReduce Deep Dive
```
Map phase:
  Input:  ("file_chunk", "the cat sat on the mat")
  Output: [("the",1), ("cat",1), ("sat",1), ("on",1), ("the",1), ("mat",1)]
  Key:    Each mapper runs independently — no coordination

Shuffle phase:
  Groups all values by key
  hash(word) % num_reducers → routes to correct reducer
  This is the network bottleneck — minimize data sent

Reduce phase:
  Input:  ("the", [1,1,1,1,...])
  Output: ("the", 4)
  Key:    Each reducer handles a non-overlapping key range
```

### Schema
```sql
-- Word counts table
CREATE TABLE word_counts (
    word        VARCHAR(255) PRIMARY KEY,
    count       BIGINT NOT NULL DEFAULT 0,
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- For time-windowed queries
CREATE TABLE word_counts_by_hour (
    word        VARCHAR(255),
    hour        TIMESTAMP,
    count       BIGINT,
    PRIMARY KEY (word, hour)
);
```

### Key Trade-offs to Discuss
```
Batch vs Streaming:
  Batch    → simpler, higher throughput, higher latency (minutes to hours)
  Stream   → complex, lower throughput, low latency (seconds)
  Lambda   → run both, merge results — complex but covers both SLAs

Exact vs Approximate:
  Exact    → full MapReduce, expensive at scale
  Approx   → Count-Min Sketch, HyperLogLog — O(1) memory, bounded error
  Use case drives choice: billing = exact, trending topics = approximate

Storage choice:
  Cassandra → great for (word → count) lookups, write-heavy, eventual consistency
  Redis     → great for top-K cache, leaderboard pattern (ZSET)
  ClickHouse → great for time-series analytics queries
```

### Your Anchor Story
> "This maps directly to what I built — the Eventlogger ingested high-throughput events from 10+ services via NATS into a unified analytics store. The challenge was exactly this: high write volume, low-latency reads for dashboards. I used async ingestion to decouple producers from storage, which let us scale writes independently."

---

## System 2 — Tenant Provisioning System

Most likely asked because Abnormal is a multi-tenant SaaS. They deal with this internally.

### What Is It
```
When a new customer signs up, you need to:
  1. Create their account in the DB
  2. Provision their isolated data store
  3. Set up IAM roles and permissions
  4. Configure their email/domain settings
  5. Send welcome email
  6. Notify internal systems (CRM, billing)

This is a multi-step workflow. Any step can fail.
```

### Clarifying Questions
```
"How many tenants do we provision per day? 10? 10,000?"
"Should provisioning be synchronous (user waits) or async (user gets notified)?"
"What's the rollback strategy if step 4 fails — undo steps 1-3 or mark as failed?"
"Do we need idempotency — what if the client retries the request?"
"Any SLA on provisioning time?"
```

### Architecture

```
CLIENT
  POST /tenants → returns 202 Accepted + job_id immediately (async)

API GATEWAY
  Validates request, creates DB record (status=PENDING), enqueues job

QUEUE (SQS / Kafka)
  Holds provisioning jobs
  Allows retries, dead letter queue for failures

PROVISIONING WORKER
  Picks up job, executes steps in order
  Updates status at each step: PENDING → CREATING_DB → CONFIGURING_IAM → DONE
  On failure: updates status to FAILED, triggers compensation

STATE STORE (DB)
  tenant_id, status, current_step, error, created_at, completed_at

NOTIFICATION SERVICE
  Sends welcome email on DONE
  Sends failure alert to ops on FAILED

POLLING / WEBHOOK
  GET /tenants/{id}/status → client polls for result
  OR: webhook callback when done
```

### State Machine
```
PENDING → CREATING_ACCOUNT → PROVISIONING_STORAGE → CONFIGURING_IAM
       → SETTING_UP_EMAIL → NOTIFYING_SYSTEMS → COMPLETE
                                                ↓ (any step)
                                             FAILED
```

### Idempotency — Key Concept
```python
# Every step must be idempotent — safe to retry
# Use idempotency keys

def provision_storage(tenant_id: str) -> None:
    # Check if already done before doing it
    if storage_exists(tenant_id):
        return  # already provisioned, skip

    create_storage(tenant_id)
    mark_step_done(tenant_id, step="storage")
```

### Saga Pattern — For Rollback
```
Two approaches when step N fails:

1. Rollback Saga (compensating transactions)
   → For each step done, run the undo operation in reverse order
   → Step 4 fails → undo step 3, undo step 2, undo step 1
   → Problem: undo might also fail

2. Forward Recovery
   → Mark the tenant as FAILED
   → Allow manual or automated retry from the failed step
   → Don't undo — just resume
   → Simpler, but tenant state may be partially provisioned

Which to use: depends on whether partial state is dangerous.
  IAM roles partially created = dangerous → rollback
  Welcome email not sent = fine → just retry forward
```

### Schema
```sql
CREATE TABLE tenants (
    tenant_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    status      VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    current_step VARCHAR(100),
    error       TEXT,
    created_at  TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE TABLE provisioning_steps (
    id          SERIAL PRIMARY KEY,
    tenant_id   UUID REFERENCES tenants(tenant_id),
    step_name   VARCHAR(100),
    status      VARCHAR(50),  -- PENDING, DONE, FAILED
    completed_at TIMESTAMP
);
```

### Key Trade-offs to Discuss
```
Sync vs Async:
  Sync  → simpler client code, but user waits 30+ seconds, timeout risk
  Async → better UX, requires polling or webhook, more complex

Rollback vs Forward:
  Rollback   → clean state, but compensation logic is complex and can fail
  Forward    → simpler, but tenant may be in partial state if abandoned

Idempotency:
  Every step must be idempotent — check before act
  Use idempotency keys on API requests to prevent duplicate jobs

Dead Letter Queue:
  Failed jobs after max retries go to DLQ
  Ops team gets alerted, can inspect and replay
```

### Your Anchor Story
> "This is exactly what I built in the Archival Service — a multi-step workflow managing state across 10+ distributed services with referential integrity. The hardest part was making each step idempotent and deciding where rollback was necessary vs where forward recovery was safer. I used a state machine pattern with a status column to make the workflow inspectable and resumable."

---

## System 3 — Analytics / Reporting Pipeline

### What Is It
```
Serve dashboards and scheduled reports to tenants.
Queries can be slow — you need to serve them with low latency at scale.
Reports need to run on a schedule (daily/weekly) per tenant.
```

### Clarifying Questions
```
"How many tenants? How many reports per tenant?"
"What's the acceptable latency for dashboard loads? Sub-second?"
"Are reports real-time or can they be pre-computed?"
"Do tenants query each other's data? (Probably not — isolation required)"
"What's the data volume per tenant?"
```

### Architecture

```
DATA LAYER
  Raw events → append-only event store (Kafka or S3)
  Aggregated → OLAP store (ClickHouse, BigQuery, Redshift)
  Materialized views → pre-computed aggregations in DB or Redis

QUERY LAYER
  API → checks Redis cache first
      → falls back to materialized view
      → falls back to live OLAP query (slow, last resort)

SCHEDULER
  Cron or Celery Beat → triggers report jobs per tenant on schedule
  Job queue → workers pick up jobs, run queries, store results
  Results stored as static artifacts (S3 + presigned URL)

DELIVERY
  Email with attachment / link
  In-app notification
  Webhook to tenant system
```

### Materialized Views — Key Concept
```sql
-- Instead of running this expensive query on every dashboard load:
SELECT date, COUNT(*) as events, COUNT(DISTINCT user_id) as users
FROM events
WHERE tenant_id = $1 AND date >= NOW() - INTERVAL '30 days'
GROUP BY date;

-- Pre-compute it as a materialized view, refresh periodically:
CREATE MATERIALIZED VIEW tenant_daily_stats AS
SELECT tenant_id, date, COUNT(*) as events, COUNT(DISTINCT user_id) as users
FROM events
GROUP BY tenant_id, date;

-- Refresh on schedule:
REFRESH MATERIALIZED VIEW tenant_daily_stats;
```

### Multi-tenant Data Isolation
```
Option 1: Row-level (single DB, tenant_id column on every table)
  + Simple, cheap
  - Bug risk: forget WHERE tenant_id = ? and leak data
  - Harder to scale one noisy tenant

Option 2: Schema-per-tenant (same DB, different schema)
  + Better isolation
  - Schema migration complexity scales with tenant count

Option 3: DB-per-tenant (separate database per tenant)
  + Full isolation
  - Expensive, complex ops

Abnormal likely uses row-level with strict ORM-level enforcement.
```

### Scheduler Design
```python
# Celery Beat example
from celery import Celery
from celery.schedules import crontab

app = Celery()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run daily report for each tenant at 6am
    sender.add_periodic_task(
        crontab(hour=6, minute=0),
        generate_daily_reports.s(),
    )

@app.task
def generate_daily_reports():
    tenants = get_all_active_tenants()
    for tenant_id in tenants:
        generate_report.delay(tenant_id)  # fan out

@app.task
def generate_report(tenant_id: str):
    data = query_analytics(tenant_id)
    artifact = render_report(data)
    store_and_notify(tenant_id, artifact)
```

### Key Trade-offs to Discuss
```
Pre-compute vs real-time:
  Pre-compute → fast reads, staleness risk, storage cost
  Real-time   → always fresh, slow queries at scale, expensive

Caching strategy:
  Cache key: (tenant_id, report_type, date_range)
  TTL: depends on data freshness SLA
  Invalidation: time-based (simple) or event-based (complex but fresh)

Fan-out at scale:
  Generating 10,000 reports simultaneously → queue with rate limiting
  Stagger report generation to avoid DB spike
  Prioritize paying/enterprise tenants
```

### Your Anchor Story
> "I've built this in production — the Analytics Scheduler automated 100+ reports per week and saved 15 engineer-hours per week. The Datalens system added NLQ-to-SQL on top. At larger scale I'd add a proper job queue with priority lanes and pre-compute materialized views aggressively rather than running live queries per request."

---

## How to Structure Your Answer in the Interview

### Opening (first 2 minutes)
```
"Before I start designing, let me clarify a few things:
  - What's the expected scale? [wait for answer]
  - Is this batch or real-time? [wait]
  - What are the consistency requirements? [wait]

Okay, based on that, here's my high-level approach..."
```

### Drawing the diagram (next 5 minutes)
```
"Let me draw the major components first without going deep.
 We have [clients] talking to [API layer], which writes to [storage].
 For the heavy lifting we have [workers] reading from [queue].
 Results go to [result store] which [query layer] reads from."
```

### Going deep (next 15 minutes)
```
"The hardest part of this system is [X]. Let me focus there.
 For the schema, I'd design it like this...
 The bottleneck is [Y] because...
 I'd handle that by..."
```

### Trade-offs (last 5 minutes)
```
"A few trade-offs worth calling out:
 I chose [A] over [B] because [reason], but the cost is [downside].
 If we needed [different requirement], I'd switch to [alternative]."
```

---

## Today's Practice Plan

**Morning (2 hrs):**
1. Read through all 3 systems above
2. For each, close this file and draw the architecture from memory on paper
3. Narrate it out loud as if you're in the interview

**Afternoon (2 hrs):**
1. Pick System 2 (Tenant Provisioning) — most likely to come up
2. Do a full timed walkthrough: 5 min clarify → 5 min estimate → 10 min draw → 15 min deep dive → 5 min trade-offs
3. Record yourself or have someone listen — you need to verbalize, not just think

**Evening (1 hr):**
1. Light review of LLD concepts (HTTP codes, DB indexing, locking) — these are in Day 3
2. Sleep well

*Tomorrow morning: Light LLD review + mock interview + rest.*
