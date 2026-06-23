# What To Study Tonight — Gap Analysis
### Pratham | June 23, 2026 | Interview Tomorrow at 12:00pm IST

> This is a focused gap analysis based on your existing notes. Do NOT re-read everything — only hit these gaps.

---

## ✅ What You Already Know Cold

| Area | Status |
|---|---|
| WordCount Level 1–3 (basic, top-K, large file) | ✅ Solid |
| WordCount Level 4 (sliding window with deque) | ✅ Solid |
| WordCount Level 5 (parallel, partition + merge) | ✅ Solid |
| WordCount Level 6 (MapReduce mental model) | ✅ Solid |
| Tenant Provisioning (state machine, idempotency, saga) | ✅ Solid |
| Analytics Pipeline (materialized views, scheduler) | ✅ Solid |
| LLD (HTTP codes, locking, circuit breaker, DLQ) | ✅ Solid |
| Python collections (Counter, deque, defaultdict, heapq) | ✅ Solid |

---

## ❌ Gaps — Study These Tonight

---

### Gap 1 — Count-Min Sketch (HIGH PRIORITY)

Your notes mention it but don't explain it. If they push you on high-throughput approximate counting, this is the answer.

**See:** `Day5_CountMinSketch.md` (created)

---

### Gap 2 — Kafka Internals (MEDIUM PRIORITY)

Your notes say "Kafka topic" but don't explain how Kafka works. If they ask about the streaming design, you need to know:
- Partitions, consumer groups, offsets
- How you'd partition a word-count workload

**See:** `SystemDesign_Concepts.md` → Kafka section

---

### Gap 3 — CAP Theorem + Consistency Models (MEDIUM PRIORITY)

When you discuss Cassandra vs Postgres, they may ask WHY. You need:
- CAP theorem (pick 2 of 3)
- Eventual vs strong consistency
- When each matters

**See:** `SystemDesign_Concepts.md` → CAP section

---

### Gap 4 — Consistent Hashing (MEDIUM PRIORITY)

Your MapReduce notes say `hash(word) % num_reducers` — but what happens when you add/remove a reducer? They may ask. Consistent hashing is the answer.

**See:** `SystemDesign_Concepts.md` → Consistent Hashing section

---

### Gap 5 — Rate Limiting (LOW PRIORITY)

May come up in API design discussion. Know two approaches:
- Token bucket
- Sliding window counter (ironic — same data structure!)

**See:** `SystemDesign_Concepts.md` → Rate Limiting section

---

### Gap 6 — Redis Data Structures (LOW PRIORITY)

Your notes mention Redis for top-K cache but don't say HOW. Redis ZSET (sorted set) is the answer for leaderboard patterns.

**See:** `SystemDesign_Concepts.md` → Redis section

---

## Tonight's Priority Order

**Do these, in this order, stop when you need sleep:**

1. ⭐ Read `Day5_CountMinSketch.md` — 15 mins
2. ⭐ Read `SystemDesign_Concepts.md` — CAP + Consistent Hashing sections — 20 mins
3. Read Kafka section — 15 mins
4. Skim Redis + Rate Limiting — 10 mins
5. **Stop. Sleep. You're ready.**

---

## Questions You Should Be Able to Answer Cold Tomorrow

### WordCount
- [ ] Implement sliding window counter from memory (Level 4)
- [ ] Explain race condition and two fixes (Level 5)
- [ ] Walk through MapReduce without notes (Level 6)
- [ ] Explain Count-Min Sketch in 3 sentences

### System Design
- [ ] Draw Tenant Provisioning architecture in 3 minutes
- [ ] Explain Saga pattern (rollback vs forward)
- [ ] Explain idempotency keys with an example
- [ ] CAP theorem: name the three, explain the trade-off
- [ ] Why Cassandra for word counts? Why Postgres for tenant config?
- [ ] What is consistent hashing and why does it matter?

### Python
- [ ] `Counter` — most_common, update, zero-default behavior
- [ ] `deque` — why O(1) popleft vs O(n) for list
- [ ] `heapq.nlargest` — complexity and when to use
- [ ] GIL and when to use ProcessPoolExecutor vs ThreadPoolExecutor
