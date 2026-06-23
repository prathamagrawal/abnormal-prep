# Abnormal AI — Interview Prep Plan
### Pratham Agrawal | SE1 Backend | June 25, 2026 | 12:00pm IST

---

## Interview Details

| Field | Info |
|---|---|
| Role | Software Engineer 1 - Backend |
| Round | Technical Screening — WordCount |
| Interviewer | Ubaid Shaikh (Software Engineer II) |
| Date & Time | Thursday, June 25, 2026 — 12:00pm IST |
| Duration | 1 hour |
| Platform | Zoom |
| Recorded | Yes — BrightHire (no personal AI tools allowed) |

---

## What This Round Tests

1. **Coding** — WordCount problem with escalating complexity
2. **System Design** — practical, production-grade, not textbook
3. **Engineering Judgment** — trade-offs, clarifying questions, thinking out loud

---

## 3-Day Prep Plan

---

### Day 1 (Monday) — Coding Fundamentals

**Goal: Be completely comfortable with WordCount and all its escalations**

#### Session 1 — Core Data Structures (2 hrs)

Practice these from scratch in Python without looking anything up:

- `dict` / `collections.Counter` — word frequency
- `collections.defaultdict` — cleaner counter patterns
- `heapq` — min/max heap for Top-K problems
- `collections.deque` — sliding window problems

#### Session 2 — WordCount Escalations (2 hrs)

Work through each level yourself before looking at solutions:

**Level 1 — Basic**
```python
# Input: string
# Output: {word: count}
# Handle: punctuation, case, empty strings

def word_count(text: str) -> dict[str, int]:
    counts = {}
    for word in text.lower().split():
        word = word.strip('.,!?";:()[]')
        if word:
            counts[word] = counts.get(word, 0) + 1
    return counts
```

**Level 2 — Top-K Most Frequent Words**
```python
import heapq
from collections import Counter

def top_k_words(text: str, k: int) -> list[tuple[str, int]]:
    counts = Counter(text.lower().split())
    return heapq.nlargest(k, counts.items(), key=lambda x: x[1])

# Know both approaches and their trade-offs:
# Sort approach  → O(n log n) — simple, fine for small data
# Heap approach  → O(n log k) — better when k << n
```

**Level 3 — Large File (doesn't fit in memory)**
```python
# Don't need to fully implement — be able to discuss:
# - Process file in chunks using a generator
# - Write partial counts to disk
# - Merge at the end (external merge sort)
# - MapReduce mental model:
#     Map phase   → tokenize + emit (word, 1) pairs
#     Shuffle     → group by word
#     Reduce      → sum counts per word

def word_count_large_file(filepath: str) -> dict[str, int]:
    counts = Counter()
    with open(filepath, 'r') as f:
        for line in f:  # generator — one line at a time
            counts.update(line.lower().split())
    return dict(counts)
```

**Level 4 — Streaming Input**
```
Words arrive one at a time continuously
Think about:
  - Sliding window counts
  - When to evict old counts
  - Redis-like in-memory store with periodic flushing
  - Approximate counting with Count-Min Sketch
```

**Level 5 — Concurrent Workers**
```
Multiple threads counting simultaneously
Think about:
  - Race conditions on shared dict
  - Partitioning input by key range (A-M / N-Z)
  - Thread-safe approaches: locks, atomic ops
  - Merge results at the end — no shared mutable state
```

#### Session 3 — Python Production Patterns (1 hr)

Things that make your code look production-grade:

```python
# Type hints
def word_count(text: str) -> dict[str, int]:

# Error handling
if not text or not isinstance(text, str):
    return {}

# Generator for large files
def read_chunks(filepath: str, chunk_size: int = 1024):
    with open(filepath, 'r') as f:
        while chunk := f.read(chunk_size):
            yield chunk

# Context managers
with open(filepath, 'r', encoding='utf-8') as f:
    ...
```

---

### Day 2 (Wednesday) — System Design

**Goal: Be able to design 2-3 systems confidently end to end**

#### Morning — HLD Framework (2 hrs)

Internalize this structure for every system design question:

| Step | What To Do | Time |
|---|---|---|
| 1 | Clarify requirements — scale, consistency, read/write ratio, latency SLA | 5 mins |
| 2 | Capacity estimation — data volume, requests/sec, storage | 3 mins |
| 3 | High level architecture — draw the boxes, data flow | 10 mins |
| 4 | Deep dive on hardest components — schema, APIs, bottlenecks | 20 mins |
| 5 | Trade-offs and failure handling | 10 mins |

**Always ask these clarifying questions:**
- What's the scale? (users, requests/sec, data volume)
- What are the consistency requirements? (strong vs eventual)
- What's the read/write ratio?
- Any latency SLAs?
- Availability requirements?

#### Afternoon — Practice These 3 Systems (3 hrs)

**System 1 — Tenant Provisioning System** *(most likely ask)*

Core challenges:
- Multi-step workflow with state tracking
- What happens when step 4 of 7 fails — rollback or resume?
- How do you make it idempotent?
- How do you handle concurrent provisioning for multiple tenants?

Your anchor story:
> *"This is similar to what I built in the Archival Service — managing state across 10+ distributed services with referential integrity and failover reliability."*

**System 2 — Distributed Word Count / Log Analytics**

Core challenges:
- Count words across terabytes of text
- MapReduce architecture
- Kafka for streaming input
- Store and query results efficiently

Your anchor story:
> *"This is essentially what I built with the Eventlogger — high-throughput ingestion from 10+ services into a unified analytics store with sub-second latency."*

**System 3 — Analytics / Reporting Pipeline**

Core challenges:
- Serve dashboards with low latency at scale
- Materialized views vs real-time queries — when to use each
- Scheduling recurring reports at scale
- Multi-tenant data isolation

Your anchor story:
> *"I've built this in production — Datalens and the Analytics Scheduler. Let me walk through what I'd do differently at larger scale."*

---

### Day 3 (Thursday Morning) — LLD + Mock + Rest

**Goal: Sharpen LLD, do one full mock, then stop and rest**

#### Morning — Low Level Design (2 hrs)

**REST API Design — Know these cold:**

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

**Database Design:**
- Normalization vs denormalization — when to choose each
- Indexing — when to add, what the trade-off is
- Foreign keys and referential integrity
- SQL vs NoSQL decision framework

**Concurrency Patterns:**
- Optimistic vs pessimistic locking
- Idempotency keys — make APIs safe to retry
- Race conditions — detect and prevent
- Retry with exponential backoff
- Dead letter queues
- Circuit breakers

#### Mock Interview (1.5 hrs)

Simulate the full hour:
- 5 mins — clarify requirements
- 10 mins — discuss approach out loud
- 30 mins — code the solution
- 15 mins — escalate to scaling discussion

**After the mock — stop prepping.** Review notes lightly in the evening. You need to be sharp and rested, not exhausted.

---

## What NOT To Study

- LeetCode hard problems — not their style
- Graph algorithms, dynamic programming — unlikely
- Kubernetes/Docker internals — too deep
- Specific AWS service internals — too deep

---

## Interview Day Tips

**Before the call:**
- Join 2-3 minutes early
- Test camera and mic — video is mandatory
- Keep your resume open in front of you
- Have water nearby
- No personal AI tools open (Cursor, ChatGPT etc)

**During the call:**
- Clarify requirements before writing a single line of code
- State your approach and trade-offs before implementing
- Verbalize your thought process — don't code in silence
- When they escalate the problem, don't panic — it's expected
- Silence is okay — 3 seconds to think is fine

**Clarifying questions to open with:**
- "Is the input a single string, a file, or a stream?"
- "Should this be case-sensitive? How do we handle punctuation?"
- "What's the expected scale — megabytes or terabytes?"
- "Do we need top-K, or just full frequency counts?"

---

## Your Strongest Anchor Stories by Topic

| Topic | Your Story |
|---|---|
| Distributed systems / decoupling | Eventlogger — async ingestion from 10+ services via NATS |
| Provisioning / state across services | Archival Service — referential integrity, S3 migration, IAM |
| Automation of manual processes | Analytics Scheduler — 100+ automated reports, 15 eng-hrs/week saved |
| LLM + NLQ + self-serve | Datalens — NLQ-to-SQL, 3-layer validation, 90% dashboard time reduction |
| Airflow / DAG operations | DBOps — LLM-driven Airflow operations layer (Claude API + prompt chaining) |
| Performance optimisation | Analytics Service — materialized views, 40% DB load reduction, 800ms → 480ms |

---

## DBOps — Locked In Answer

> *"I built DBOps — an LLM-driven operations layer on top of Airflow. It lets data ops teams interact with their DAGs in natural language — triggering runs, listing DAGs, inspecting logs, debugging failures. We used the Claude API with prompt chaining to map user intent to specific Airflow operations. Reduced manual ops time from hours to under 2 minutes. Currently extending it with an MCP server integration."*

**If they ask about ETL generation (resume wording):**
> *"You're right, and I want to be precise — the system orchestrates and operates Airflow DAGs through natural language rather than generating ETL logic from scratch. The ETL logic lives in the DAGs themselves. I should have been more precise in how I worded that."*

---

## Daily Schedule Summary

| Day | Focus | Hours |
|---|---|---|
| Monday | WordCount coding + Python fundamentals | 5 hrs |
| Wednesday | System design — HLD + 3 systems + LLD | 5 hrs |
| Thursday morning | Light review + mock + rest | 1 hr max |

---

*Good luck Pratham. You've got this.* 🚀
