# Cheatsheet — Day-of Quick Reference
### Pratham | June 25, 2026 | 12:00pm IST | Ubaid Shaikh | WordCount

Read this once the morning of. Then close it.

---

## Open With These Questions (every time, no exceptions)

```
"What's the input — string, file, or stream?"
"Case-sensitive? How to handle punctuation?"
"Full frequency map, or Top-K?"
"What's the scale — KB, GB, or TB?"
"Should I handle None and empty inputs?"
```

---

## WordCount Levels — One-Line Each

| Level | Key idea |
|---|---|
| Basic | `.lower()` + `.split()` + strip punctuation + `counts.get(word, 0) + 1` |
| Top-K | `Counter.most_common(k)` — O(n log k). Sort is O(n log n). |
| Large file | `for line in f:` — already a generator. Counter.update per line. |
| Streaming | `deque` + `Counter`. On eviction: decrement, delete if 0. |
| Concurrent | Race condition on read-modify-write. Fix: partition keys, merge locally. |
| Distributed | MapReduce: Map (emit word,count) → Shuffle (hash(word)%R) → Reduce (sum) |

---

## Code Snippets to Know Cold

```python
# Level 1
def word_count(text: str) -> dict[str, int]:
    if not text: return {}
    counts: dict[str, int] = {}
    for word in text.lower().split():
        word = word.strip('.,!?";:\'()-')
        if word: counts[word] = counts.get(word, 0) + 1
    return counts

# Level 2
from collections import Counter
def top_k(text: str, k: int) -> list[tuple[str, int]]:
    return Counter(text.lower().split()).most_common(k)

# Level 3
def word_count_file(filepath: str) -> Counter:
    counts = Counter()
    with open(filepath, encoding='utf-8') as f:
        for line in f: counts.update(line.lower().split())
    return counts

# Level 4 — sliding window
from collections import Counter, deque
class SlidingWindowCounter:
    def __init__(self, size: int):
        self.window, self.counts, self.size = deque(), Counter(), size
    def process(self, word: str) -> None:
        self.window.append(word); self.counts[word] += 1
        if len(self.window) > self.size:
            e = self.window.popleft(); self.counts[e] -= 1
            if self.counts[e] == 0: del self.counts[e]

# Level 5 — parallel, no locks
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
def parallel_count(text: str, workers: int = 4) -> Counter:
    words = text.lower().split()
    n = max(1, len(words) // workers)
    chunks = [words[i:i+n] for i in range(0, len(words), n)]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(Counter, chunks))
    final = Counter()
    for r in results: final.update(r)
    return final
```

---

## Python Collections Cheatsheet

```python
from collections import Counter, defaultdict, deque
import heapq

Counter(iterable)           # word frequencies
c.most_common(k)            # top-k, O(n log k)
c["missing"]                # returns 0, no KeyError

defaultdict(int)            # d["x"] += 1, no KeyError

deque(maxlen=N)             # fixed-size, auto-evicts oldest
q.append(x) / q.popleft()  # both O(1)

heapq.nlargest(k, items, key=fn)   # O(n log k)
heapq.nsmallest(k, items, key=fn)  # O(n log k)
```

---

## Complexity Reference

| Operation | Complexity |
|---|---|
| Counter(list) | O(n) |
| Counter.most_common(k) | O(n log k) |
| sorted() | O(n log n) |
| heapq.nlargest(k, n items) | O(n log k) |
| deque.append / popleft | O(1) |
| list.pop(0) | O(n) — don't use |

---

## System Design — 5-Step Frame

```
1. Clarify  (5 min) — scale, consistency, read/write ratio, latency SLA
2. Estimate (3 min) — req/sec, storage, bandwidth
3. Diagram  (10 min) — Client → API → Service → Queue → Worker → Store
4. Deep dive (20 min) — schema, APIs, hardest component
5. Trade-offs (10 min) — what you chose and why, what you'd change at scale
```

---

## Tenant Provisioning — Key Points

- Return 202 Accepted immediately. Provision async via queue.
- State machine: PENDING → CREATING → CONFIGURING → DONE / FAILED
- Every step must be idempotent — check before act
- On failure: Saga rollback (compensating txns) or forward recovery (simpler)
- Dead letter queue for jobs that exhaust retries

---

## HTTP Codes to Know

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 202 | Accepted (async) |
| 204 | No Content (DELETE) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 429 | Rate Limited |
| 500 | Server Error |
| 503 | Unavailable |

---

## Concurrency in One Line Each

- **Optimistic lock**: check version on write, retry if mismatch
- **Pessimistic lock**: `SELECT FOR UPDATE`, blocks other transactions
- **Idempotency key**: client sends UUID header, server deduplicates
- **Circuit breaker**: CLOSED → OPEN (fail fast) → HALF-OPEN (probe)
- **Exponential backoff**: wait 2^attempt + jitter, then retry
- **DLQ**: failed messages after max retries → alert ops, allow replay

---

## Your Anchor Stories (one line each)

| Topic | Story |
|---|---|
| Distributed / async | Eventlogger — NATS, 10+ services, unified analytics store |
| Provisioning / state | Archival Service — state machine, S3 migration, IAM, referential integrity |
| Automation | Analytics Scheduler — 100+ reports/week, 15 eng-hrs saved |
| LLM + NLQ | Datalens — NLQ-to-SQL, 3-layer validation, 90% dashboard time reduction |
| Airflow + LLM | DBOps — Claude API, natural language → DAG operations, hours → 2 min |
| Performance | Analytics Service — materialized views, 800ms → 480ms, 40% DB load down |

---

## Common Traps

- Punctuation attached: `"hello!"` — strip or regex
- Case: always `.lower()` first
- `list.pop(0)` is O(n) — use `deque.popleft()`
- `counts["word"]` raises KeyError — use `.get()` or Counter
- Don't load whole file — iterate line by line
- Mutable default arg: `def f(d={})` — bug. Use `d=None`

---

## Mindset Reminders

```
✓ Ask questions BEFORE coding
✓ Narrate your thought process — don't go silent
✓ State complexity when done
✓ When escalated: pause → "let me think" → answer
✓ Take hints — that's the game
✓ Treat Ubaid as a colleague, not an examiner
```

---

*You prepared. You know this. Go show them.*
