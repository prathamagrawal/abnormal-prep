# Day 3 — LLD + Mock Interview + Day-of Checklist
### Thursday, June 25 | Goal: Sharpen, simulate, then stop and rest

---

## Part 1 — Low Level Design (1 hr max, morning only)

### REST API Design — Know These Cold

| Code | Meaning | When to use |
|---|---|---|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST that created a resource |
| 202 | Accepted | Async job enqueued (provisioning, reports) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input, malformed JSON |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | Authenticated but no permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource, optimistic lock failure |
| 422 | Unprocessable Entity | Valid format but semantic error |
| 429 | Too Many Requests | Rate limited |
| 500 | Internal Server Error | Unexpected server failure |
| 503 | Service Unavailable | Overloaded or in maintenance |

### REST API Design Patterns

```
Resource naming:
  GET    /tenants                → list all tenants
  POST   /tenants                → create tenant (returns 201)
  GET    /tenants/{id}           → get one tenant
  PUT    /tenants/{id}           → full update
  PATCH  /tenants/{id}           → partial update
  DELETE /tenants/{id}           → delete (returns 204)

Nested resources:
  GET    /tenants/{id}/reports   → reports for a tenant
  POST   /tenants/{id}/reports   → create report for tenant

Async operations:
  POST   /tenants                → 202 Accepted, body: {"job_id": "abc"}
  GET    /jobs/{job_id}          → poll status: PENDING / RUNNING / DONE / FAILED

Pagination:
  GET    /words?page=2&page_size=50
  Response: {"data": [...], "next_cursor": "xyz", "total": 1000}
```

### Database Design

**Indexing — when to add, what the trade-off is**
```sql
-- Add index when:
-- 1. Column appears in WHERE clause frequently
-- 2. Column used in JOIN conditions
-- 3. Column used in ORDER BY on large tables

CREATE INDEX idx_words_count ON word_counts(count DESC);  -- for top-K queries
CREATE INDEX idx_events_tenant_date ON events(tenant_id, created_at);  -- composite

-- Trade-off: every index slows down writes (index must be updated on INSERT/UPDATE)
-- Don't index low-cardinality columns (e.g., status with 3 values)
-- Don't over-index write-heavy tables
```

**Normalization vs Denormalization**
```
Normalize when:
  - Data is updated frequently (single source of truth)
  - Storage is the constraint
  - Write-heavy workload

Denormalize when:
  - Read performance is critical
  - Data rarely changes
  - Joins are too slow at your scale
  - Dashboard/analytics use case

Example: store tenant_name on every event row (denormalized)
  vs join to tenants table on every query (normalized)
```

**SQL vs NoSQL**
```
Use SQL (Postgres, MySQL) when:
  - Relationships between entities
  - Transactions with ACID guarantees
  - Schema is well-defined and stable
  - Complex queries with JOINs

Use NoSQL (Cassandra, DynamoDB, Redis) when:
  - Write throughput is the bottleneck
  - Schema is flexible / evolving
  - Simple access patterns (key-value, range scans)
  - Horizontal scale is required

Example: word counts → Cassandra (massive write throughput, simple lookup)
         tenant config → Postgres (relational, transactional)
```

### Concurrency Patterns

**Optimistic vs Pessimistic Locking**
```python
# Pessimistic locking — lock the row before reading
# Use when: high contention, updates always happen after read
cursor.execute("SELECT * FROM accounts WHERE id = %s FOR UPDATE", (account_id,))
# Other transactions block until this transaction commits

# Optimistic locking — no lock, check version on write
# Use when: low contention, reads >> writes
cursor.execute(
    "UPDATE accounts SET balance = %s, version = version + 1 "
    "WHERE id = %s AND version = %s",
    (new_balance, account_id, current_version)
)
# If 0 rows updated → someone else modified it → retry
```

**Idempotency Keys**
```python
# Make POST requests safe to retry
# Client generates a unique key, server deduplicates on it

def create_tenant(request):
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        existing = db.get_by_idempotency_key(idempotency_key)
        if existing:
            return existing  # return same result, don't create again

    tenant = Tenant.create(request.body)
    db.store_idempotency_key(idempotency_key, tenant.id, ttl=24*3600)
    return tenant
```

**Retry with Exponential Backoff**
```python
import time, random

def retry_with_backoff(fn, max_retries=5):
    for attempt in range(max_retries):
        try:
            return fn()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)  # jitter
            time.sleep(wait)
```

**Circuit Breaker**
```
State: CLOSED → OPEN → HALF-OPEN

CLOSED: requests pass through normally
  → if failure rate > threshold: switch to OPEN

OPEN: all requests fail immediately (don't even try)
  → after timeout: switch to HALF-OPEN

HALF-OPEN: let one request through
  → if it succeeds: back to CLOSED
  → if it fails: back to OPEN

Why: prevents cascading failures. If downstream is down,
     failing fast is better than queuing thousands of requests.
```

**Dead Letter Queue**
```
Failed jobs after max retries → DLQ
  → Ops team gets alerted
  → Can inspect the payload and error
  → Can replay manually when issue is fixed

Never silently drop failed messages.
```

---

## Part 2 — Mock Interview Script (1 hr)

Simulate the full 60-minute interview. Do this out loud, alone or with someone.

---

### Interviewer opens:
> "Hi Pratham, thanks for joining. I'm Ubaid. I'm a Software Engineer here at Abnormal. Today we'll work through a coding problem together. Feel free to ask questions at any time — this is collaborative. Ready?"

### Your response:
> "Yes, ready. Thanks Ubaid."

---

### Interviewer:
> "Let's start with a classic. Write a function that takes a string and returns the frequency of each word."

### Your move — DO NOT CODE YET. Ask clarifying questions:
> "Sure — before I start, let me ask a few things to make sure I'm solving the right problem.
>
> First — should this be case-sensitive, or treat 'Hello' and 'hello' as the same word?
> How should I handle punctuation — strip it from words, or treat 'hello!' as a different token from 'hello'?
> Is the input always a valid string, or should I handle None and empty inputs?
> And is this just the full frequency map, or will we need top-K at some point?"

*(Wait for answers. They'll probably say: case-insensitive, strip punctuation, handle edge cases, just the map for now.)*

---

### You say:
> "Great. So: lowercase everything, strip common punctuation, handle empty input gracefully. I'll write this cleanly and we can extend it."

*(Code Level 1 solution. Narrate as you type.)*

```python
def word_count(text: str) -> dict[str, int]:
    if not text or not isinstance(text, str):
        return {}

    counts: dict[str, int] = {}
    for word in text.lower().split():
        word = word.strip('.,!?";:\'()-')
        if word:
            counts[word] = counts.get(word, 0) + 1
    return counts
```

> "I'm iterating over words, lowercasing, stripping punctuation, and using `.get()` with a default to avoid KeyError. The `if word` check handles cases where a token is only punctuation — like if the input was just '!!!'. Time complexity is O(n) where n is the number of words."

---

### Interviewer escalates:
> "Good. Now — what if I wanted the top 5 most frequent words?"

### Your response:
> "Two approaches. Sort is O(n log n) — simple. If k is much smaller than n, a min-heap of size k gives O(n log k), which is better. Python's `Counter.most_common(k)` does this idiomatically. Want me to implement the heap manually or use the built-in?"

*(They'll probably say built-in is fine, or ask you to show the heap.)*

```python
from collections import Counter
import heapq

def top_k_words(text: str, k: int) -> list[tuple[str, int]]:
    counts = Counter(text.lower().split())
    return heapq.nlargest(k, counts.items(), key=lambda x: x[1])
```

---

### Interviewer escalates:
> "What if the file is too large to fit in memory?"

### Your response:
> "Python file iterators are already generators — iterating line by line never loads the full file into memory. I'd do this:"

```python
from collections import Counter

def word_count_large_file(filepath: str) -> Counter:
    counts = Counter()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            counts.update(line.lower().split())
    return counts
```

> "If even the Counter itself overflows — say billions of unique tokens — I'd use external sort: process chunks, write partial counts to disk, then k-way merge. That's the MapReduce pattern applied locally."

---

### Interviewer escalates:
> "What if words are arriving as a stream — one word at a time?"

### Your response:
> "Two scenarios: count everything, or count within a sliding window. For a sliding window I'd use a deque paired with a Counter:"

```python
from collections import Counter, deque

class SlidingWindowCounter:
    def __init__(self, window_size: int):
        self.window = deque()
        self.counts = Counter()
        self.size = window_size

    def process(self, word: str) -> None:
        self.window.append(word)
        self.counts[word] += 1
        if len(self.window) > self.size:
            evicted = self.window.popleft()
            self.counts[evicted] -= 1
            if self.counts[evicted] == 0:
                del self.counts[evicted]
```

> "Deque gives O(1) append and popleft. I decrement on eviction and delete at zero to avoid memory leaking."

---

### Interviewer escalates:
> "Now imagine 4 workers processing this in parallel — what could go wrong?"

### Your response:
> "Race condition on the shared counter. Two workers both read `counts['the'] = 5`, both increment locally, one write is lost. Two fixes: lock — correct but serializes access; or partition the input so each worker handles non-overlapping key ranges, then merge local counters at the end. No shared mutable state, no locks needed. This is the MapReduce pattern."

---

### Interviewer may then pivot to system design:
> "How would you design this to work at massive scale — say, across 100 machines processing terabytes of text?"

### Your response (talk through MapReduce, don't code):
> "I'd use a MapReduce-style architecture. Map phase: each machine independently processes its chunk, emits (word, count) pairs — no inter-machine communication. Shuffle phase: route all instances of the same word to the same reducer using consistent hashing — `hash(word) % num_reducers`. Reduce phase: each reducer sums counts for its word range. Output goes to a distributed store. For Top-K, I'd pre-compute and cache in Redis rather than computing at query time."

---

### End of mock — debrief yourself:
```
Did I ask clarifying questions before coding?        Y / N
Did I narrate my thought process while coding?       Y / N
Did I mention time/space complexity?                 Y / N
Did I handle edge cases (empty, None)?               Y / N
Did I stay calm during escalations?                  Y / N
Did I discuss trade-offs (not just give one answer)? Y / N
```

---

## Part 3 — Day-of Checklist

### The night before (Wednesday evening)
- [ ] Read through the cheatsheet (Cheatsheet.md) once
- [ ] Lay out your anchor stories — one sentence each, from memory
- [ ] Close all prep material at 10pm. Sleep.

### Morning of (Thursday, June 25)
- [ ] Wake up normally. Don't cram.
- [ ] Eat a real breakfast
- [ ] Open Zoom, test audio + video 10 minutes before
- [ ] Have a glass of water on your desk
- [ ] Keep your resume open in front of you
- [ ] Close: Cursor, ChatGPT, Copilot, all AI tools (mandatory per interview email)
- [ ] Have a blank doc or paper for scratch work
- [ ] Join the Zoom at 11:55am (5 min early)

### During the interview — mental checklist
```
□ Clarify before coding (5 questions minimum)
□ Say your approach out loud before writing a line
□ Narrate as you code — don't go silent
□ State complexity when you're done with each solution
□ When escalated: pause, say "let me think about that for a second", then answer
□ If you're stuck: say what you know, ask if you're on the right track
□ If they hint: take it — that's the point
```

### What to say if you don't know something
```
"I haven't implemented that specific thing before, but here's how I'd think through it..."
"Let me reason from first principles — [think out loud]"
"I know there are a few approaches here. Let me start with the simple one and we can optimize."
```

### Tone to maintain
- Confident, not arrogant
- Curious, not defensive
- Collaborative — treat Ubaid as a colleague, not an examiner
- When they push back: "That's a good point — let me reconsider that"

---

## Your Anchor Stories (one sentence each — say from memory)

| Topic | One-line story |
|---|---|
| Distributed systems | Eventlogger: async ingestion from 10+ services via NATS into unified analytics store |
| Provisioning / state | Archival Service: multi-step state machine across distributed services, S3 migration, IAM |
| Automation | Analytics Scheduler: 100+ automated reports/week, 15 eng-hrs/week saved |
| NLQ + LLM | Datalens: NLQ-to-SQL with 3-layer validation, 90% reduction in dashboard build time |
| Airflow + LLM | DBOps: natural language → Airflow operations via Claude API, hours → 2 minutes |
| Performance | Analytics Service: materialized views, 40% DB load reduction, 800ms → 480ms |

---

## After the interview
- Write down everything you remember about the questions asked
- Note what went well and what was hard
- Don't spiral — you prepared, you showed up, that's what you could control

*Good luck Pratham. You've got this.*
