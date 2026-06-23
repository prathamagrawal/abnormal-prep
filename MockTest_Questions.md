# Mock Test — Interview Simulation
### Pratham | June 23, 2026 | Do this tonight, treat it like the real thing

> Rules: Set a timer. Answer out loud or write code in a blank file.
> Do NOT look at your notes until you've attempted the question.
> Mark each one H (hard), M (medium), E (easy) after you answer.

---

## Section 1 — Python & Data Structures (Questions 1–12)

---

**Q1.** What does this return? Explain why.

```python
from collections import Counter
a = Counter({"the": 3, "cat": 2})
b = Counter({"the": 1, "mat": 2})
print(a - b)
```

<details><summary>Answer</summary>

`Counter({'cat': 2, 'the': 2})` — subtraction removes keys with count ≤ 0. "mat" was only in `b`, so after subtraction it would be -2, which gets dropped. "the" goes from 3-1=2.

</details>

---

**Q2.** What is the time complexity of `Counter.most_common(k)`? What about `Counter.most_common()` with no argument?

<details><summary>Answer</summary>

- `most_common(k)` → O(n log k) using `heapq.nlargest` internally
- `most_common()` (all items) → O(n log n) — full sort

</details>

---

**Q3.** What is wrong here?

```python
c = Counter()
for word in stream:
    c[word] += 1
    if c[word] == 0:
        del c[word]
```

<details><summary>Answer</summary>

The `del` condition is wrong — you'd only delete at zero after incrementing, which never happens here. The check should come after a *decrement*, not an increment. Also, `c[word] += 1` on a Counter starts from 0 due to Counter's `__missing__`, so it's safe, but the `== 0` check is dead code here.

</details>

---

**Q4.** What is the difference between these two?

```python
d = deque(maxlen=5)
d = deque()
```

When would you use each for a sliding window?

<details><summary>Answer</summary>

`deque(maxlen=5)` auto-evicts the oldest element when capacity is exceeded — no manual eviction needed, but you lose track of which word was evicted (you can't decrement its count). Use `maxlen` only if you don't need to maintain a Counter alongside it.

For word-count sliding window you need to know what was evicted to decrement the Counter, so you use `deque()` (unbounded) and evict manually.

</details>

---

**Q5.** Why is `list.pop(0)` O(n) but `deque.popleft()` O(1)?

<details><summary>Answer</summary>

`list` is backed by a contiguous array. Removing the first element requires shifting all remaining elements left — O(n). `deque` (double-ended queue) is backed by a doubly-linked list of fixed-size blocks. Removing the head is a pointer update — O(1).

</details>

---

**Q6.** What does `re.findall(r"\b\w+\b", "don't stop 123")` return?

<details><summary>Answer</summary>

`['don', 't', 'stop', '123']` — `\b\w+\b` splits on apostrophes (not a word char), and matches digits.

If you want contractions preserved and no digits: `re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", "don't stop 123")` → `['don't', 'stop']`

</details>

---

**Q7.** Complete this without using `Counter`, `sorted`, or `heapq`:

```python
def top_3_manual(text: str) -> list[tuple[str, int]]:
    # Implement using only a raw min-heap of size 3
    ...
```

<details><summary>Answer</summary>

```python
import heapq

def top_3_manual(text: str) -> list[tuple[str, int]]:
    freq = {}
    for word in text.lower().split():
        word = word.strip('.,!?')
        if word:
            freq[word] = freq.get(word, 0) + 1

    heap = []   # min-heap of (count, word), size 3
    for word, count in freq.items():
        heapq.heappush(heap, (count, word))
        if len(heap) > 3:
            heapq.heappop(heap)  # remove the smallest

    return sorted(heap, reverse=True)
```

</details>

---

**Q8.** What is the output?

```python
def word_count(text, stop=[]):
    words = text.split()
    return [w for w in words if w not in stop]

result1 = word_count("hello world")
stop_list = word_count.__defaults__[0]
stop_list.append("hello")
result2 = word_count("hello world")
print(result1, result2)
```

<details><summary>Answer</summary>

`['hello', 'world'] ['world']`

The default list `[]` is created once at function definition and shared across all calls. Mutating it affects future calls. Fix: `def word_count(text, stop=None): stop = stop or []`

</details>

---

**Q9.** You have 50 partial `Counter` objects from 50 workers. What's the most efficient way to merge them?

<details><summary>Answer</summary>

```python
from collections import Counter
from functools import reduce

counters = [...]  # list of 50 Counters

# Option 1 — iterative update: O(total_unique_words)
final = Counter()
for c in counters:
    final.update(c)

# Option 2 — reduce with +: same complexity but creates intermediate objects
final = reduce(lambda a, b: a + b, counters)

# Option 1 is preferred — no intermediate Counter objects, lower memory
```

</details>

---

**Q10.** Is this thread-safe? Why or why not?

```python
from collections import Counter
import threading

counts = Counter()

def worker(words):
    for word in words:
        counts[word] += 1  # is this safe?
```

<details><summary>Answer</summary>

No. `counts[word] += 1` is three bytecode ops: LOAD, ADD, STORE. The GIL can release between them (e.g., after LOAD), allowing another thread to read the same stale value. The GIL protects individual bytecode ops, not compound operations. Fix: use a Lock, or partition input so no shared state exists.

</details>

---

**Q11.** What does the walrus operator do here? Rewrite it without it.

```python
while chunk := f.read(1024):
    process(chunk)
```

<details><summary>Answer</summary>

The walrus operator (`:=`) assigns the result of `f.read(1024)` to `chunk` AND evaluates its truthiness in one step. Empty string `""` is falsy so the loop stops at EOF.

Without walrus:
```python
chunk = f.read(1024)
while chunk:
    process(chunk)
    chunk = f.read(1024)
```

</details>

---

**Q12.** What happens if you open a file without specifying encoding on a Linux server with locale set to ASCII?

```python
with open("log.txt", "r") as f:
    data = f.read()
```

<details><summary>Answer</summary>

If `log.txt` contains any non-ASCII bytes (accented chars, emoji, non-latin text), this raises `UnicodeDecodeError`. Always specify `encoding='utf-8'`, or add `errors='ignore'` / `errors='replace'` if the data may be dirty.

</details>

---

## Section 2 — Coding Problems (Questions 13–25)

Set a 20-minute timer per problem. Narrate as you code.

---

**Q13. (Level 1 — 5 min)** Implement `word_count(text)` from scratch:
- No imports
- Case-insensitive
- Strip punctuation `.,!?";:'()-`
- Return empty dict for invalid input

---

**Q14. (Level 2 — 8 min)** Implement `top_k_words(text, k)`:
- O(n log k) time
- Stable: tie-break alphabetically
- Explain complexity when done

---

**Q15. (Level 3 — 10 min)** Implement `word_count_file(filepath)`:
- File may be 100 GB — must be memory-efficient
- Line-by-line generator approach
- Handle `FileNotFoundError` gracefully
- Specify encoding explicitly

---

**Q16. (Level 4a — 10 min)** Implement `StreamCounter`:
- Unbounded stream of words
- `add(word)` — O(1)
- `top_k(k)` — returns top k at any point
- `get_count(word)` — O(1)

---

**Q17. (Level 4b — 15 min)** Implement `SlidingWindowCounter`:
- Count-based window: last N words
- `process(word)` — O(1) amortized
- `top_k(k)` — returns top k in current window
- `get_count(word)` — O(1)
- No memory leak on eviction

---

**Q18. (Level 4c — 20 min)** Now do timestamp-based:
- Window: last T seconds
- `process(timestamp, word)` — O(1) amortized
- Same interface as Q17
- What additional edge case exists vs count-based?

*(Answer: out-of-order timestamps — do you need to handle them? Ask the interviewer.)*

---

**Q19. (Level 5 — 15 min)** Implement `parallel_word_count(text, workers=4)`:
- Use `ProcessPoolExecutor` (not Thread — explain why)
- Partition words into equal chunks
- Merge partial Counters
- No shared mutable state, no locks

---

**Q20. (Bonus — 20 min)** Implement `CountMinSketch` with:
- `add(word)` — O(d) where d = depth
- `estimate(word)` — O(d)
- Constructor takes `width` and `depth`
- Use different seeds per row for independence

---

**Q21. (Debugging — 5 min)** Find and fix all bugs:

```python
from collections import deque, Counter

class SlidingWindowCounter:
    def __init__(self, size):
        self.size = size
        self.window = deque()
        self.counts = Counter()

    def process(self, word):
        self.window.append(word)
        self.counts[word] += 1

        if len(self.window) >= self.size:
            evicted = self.window.pop()
            self.counts[evicted] -= 1
```

<details><summary>Answer</summary>

Three bugs:
1. `>= self.size` should be `> self.size` — evict only when over capacity
2. `self.window.pop()` removes from the **right** (newest) — should be `popleft()` to evict oldest
3. No cleanup when count hits zero — add `if self.counts[evicted] == 0: del self.counts[evicted]` to prevent memory leak

</details>

---

**Q22. (Design — 10 min)** Design a function signature and class for a word counter that supports these operations efficiently. State the complexity for each before writing any code:

- `add_document(doc_id, text)` — index a document
- `get_word_count(doc_id, word)` — count in a specific document
- `get_global_count(word)` — count across all documents
- `top_k_global(k)` — top k words globally

---

**Q23. (Edge cases — 5 min)** What does your `word_count` function return for each of these? Does it behave correctly?

```python
word_count("")
word_count("   ")
word_count("!!!")
word_count("Hello HELLO hello")
word_count("don't stop")
word_count(None)
word_count(42)
```

---

**Q24. (Optimization — 10 min)** This function is called 10,000 times per second with short strings. Profile it mentally and suggest 2 specific optimizations:

```python
import re
from collections import Counter

def word_count(text: str) -> Counter:
    return Counter(re.findall(r"[a-z']+", text.lower()))
```

<details><summary>Answer</summary>

1. **Compile the regex once** — `re.findall` recompiles the pattern on every call. Use `pattern = re.compile(r"[a-z']+")` at module level, then `pattern.findall(text.lower())`.
2. **Avoid `.lower()` on the whole string** — lowercase inside the pattern using `re.IGNORECASE` flag, or lowercase only matched words. Minor, but avoids allocating a new string when text is already lowercase.

</details>

---

**Q25. (Code review — 5 min)** Review this code. Find every issue (style, correctness, performance, safety):

```python
def process_file(f):
    data = open(f).read()
    words = data.split(' ')
    counts = {}
    for w in words:
        w = w.lower()
        counts[w] = counts[w] + 1
    return sorted(counts, key=counts.get)
```

<details><summary>Answer</summary>

Issues:
1. `open(f)` — no `with` statement, file never closed → resource leak
2. `open(f).read()` — loads entire file into memory
3. `data.split(' ')` — splits only on space, not tabs/newlines. Use `.split()`
4. No punctuation stripping — "hello," ≠ "hello"
5. No encoding specified
6. `counts[w] + 1` — raises `KeyError` on first occurrence. Use `.get(w, 0) + 1`
7. `sorted(counts, ...)` — sorts keys only, loses values. Should be `sorted(counts.items(), key=lambda x: x[1], reverse=True)`
8. No input validation — what if `f` doesn't exist?

</details>

---

## Section 3 — System Design (Questions 26–35)

Answer these verbally. Aim for 3–5 minutes each.

---

**Q26.** Design a system that accepts a stream of words from a Kafka topic and maintains a live top-10 leaderboard. Users can query the leaderboard at any time with < 100ms latency.

*Cover: consumer group, aggregation, storage, Redis ZSET, refresh strategy.*

---

**Q27.** Your word-count API endpoint is being hit 50,000 times/second. The database query for `get_count(word)` is taking 200ms. How do you fix it?

*Cover: caching (Redis), cache-aside pattern, TTL trade-offs, cache invalidation.*

---

**Q28.** A tenant's provisioning workflow fails at step 5 of 8. Steps 1–4 created database records and an S3 bucket. What are your options? What do you recommend?

*Cover: forward recovery vs rollback saga, idempotency, DLQ, partial state risk.*

---

**Q29.** You're designing the schema for a multi-tenant word-count analytics system. Each tenant has millions of documents. How do you structure the database?

*Cover: row-level isolation vs schema-per-tenant, tenant_id on every table, query performance, migration complexity.*

---

**Q30.** Explain consistent hashing. Your MapReduce job uses `hash(word) % num_reducers`. You add 2 new reducers. What breaks, and how does consistent hashing fix it?

*Cover: modular hashing causes massive re-routing, consistent hashing minimizes remapping, virtual nodes.*

---

**Q31.** Explain the CAP theorem. Where does Cassandra sit? Where does Postgres sit? Why would you use Cassandra for word counts but Postgres for tenant configuration?

*Cover: Cassandra = AP (eventual consistency, high availability), Postgres = CP (strong consistency, transactions), choice based on workload.*

---

**Q32.** Your Kafka consumer for word counting is falling behind — lag is growing by 1M messages/minute. What do you do?

*Cover: scale consumers (up to partition count), increase partitions, check for hot partitions, optimize consumer code, backpressure vs load shedding.*

---

**Q33.** Design the API for a word-count service. Include:
- Ingest endpoint (submit text or file)
- Query endpoint (get count for a word)
- Top-K endpoint
- Async job status endpoint

*Cover: REST verbs, status codes (202 for async), pagination, idempotency key header.*

---

**Q34.** A dashboard query runs this SQL and takes 3 seconds:

```sql
SELECT word, SUM(count) as total
FROM word_counts
WHERE tenant_id = $1
GROUP BY word
ORDER BY total DESC
LIMIT 10;
```

How do you make it fast?

*Cover: composite index on (tenant_id, count), materialized view refreshed on schedule, Redis ZSET as pre-computed leaderboard.*

---

**Q35.** You need to count words across 1TB of logs split across 100 machines. Walk through the complete MapReduce execution, naming every phase and what data flows between them.

*Cover: Map (emit word,1 per line), Combiner (optional local reduce to cut shuffle data), Shuffle (hash(word)%reducers), Reduce (sum), Output to distributed store.*

---

## Section 4 — Mixed Rapid Fire (Questions 36–45)

30 seconds each. Say the answer out loud immediately.

---

**Q36.** What HTTP status code do you return when a POST creates a resource successfully?

**Q37.** What HTTP status code do you return when a POST kicks off an async job?

**Q38.** What HTTP status code for "authenticated but no permission"?

**Q39.** What is optimistic locking? Give the SQL pattern.

**Q40.** What is a dead letter queue and why do you need one?

**Q41.** What is the difference between HyperLogLog and Count-Min Sketch?

**Q42.** Why use `ProcessPoolExecutor` instead of `ThreadPoolExecutor` for CPU-bound work?

**Q43.** What is exponential backoff with jitter? Why the jitter?

**Q44.** What is a circuit breaker's three states?

**Q45.** What does `Counter({"a": 1}) & Counter({"a": 3, "b": 2})` return?

<details><summary>Answers 36–45</summary>

36. 201 Created
37. 202 Accepted
38. 403 Forbidden
39. Read version, update with `WHERE id=? AND version=?`, retry if 0 rows updated
40. Queue for messages that fail after max retries — ops can inspect and replay
41. CMS estimates frequency of a specific item. HLL estimates cardinality (distinct count)
42. GIL prevents true parallelism for CPU-bound threads. ProcessPool uses separate processes that each have their own GIL
43. `wait = 2^attempt + random(0, 1)`. Jitter prevents all retrying clients from hammering at the same moment (thundering herd)
44. CLOSED (normal) → OPEN (fail fast) → HALF-OPEN (probe one request)
45. `Counter({'a': 1})` — intersection keeps minimum count, 'b' not in left operand so excluded

</details>

---

## Section 5 — Behavioral & Judgment (Questions 46–50)

These come at the end of an interview. Answer in 60–90 seconds each.

---

**Q46.** The interviewer hints at an optimization after you give your first solution. Do you take the hint or defend your original answer?

*Right answer: Take the hint immediately. Say "Good point — I hadn't considered that. Let me reconsider." Defending mediocre solutions signals closed-mindedness.*

---

**Q47.** You're stuck on the large-file problem. You know you need streaming but can't remember the exact Python syntax. What do you say?

*Right answer: "I know I need to iterate line by line to keep memory O(1). I'd use a with-open block and iterate with `for line in f`. I believe Python's file iterator is already lazy so I don't need to read chunks manually — let me write that out." Never go silent.*

---

**Q48.** Ubaid asks: "Is there a more efficient approach?" after you give an O(n log n) sort-based top-K. What do you say?

*Right answer: "Yes — if k is much smaller than n, a min-heap of size k gives O(n log k) instead of O(n log n). Python's heapq.nlargest does this. Want me to implement that?"*

---

**Q49.** After your sliding window answer, he asks: "What if the window needs to handle out-of-order arrivals?" What do you say?

*Right answer: "Good edge case — my current design assumes timestamps arrive in order. For out-of-order, I'd need to buffer events and wait for a watermark before finalizing counts. That's similar to how Flink handles late events. Want me to sketch that?"*

---

**Q50.** He asks: "How would you test the word count function?" Walk through your testing strategy.

*Right answer: Unit tests — empty string, None, single word, all-same word, punctuation-only, mixed case, contractions. Property test: `word_count(a + " " + b) == merge(word_count(a), word_count(b))`. Integration test: known file with expected output. Performance test: 1M word string, assert runs in < 1 second.*

---

## Self-Scoring

After running through this test:

| Section | Questions | Your Score |
|---|---|---|
| Python & Data Structures | Q1–Q12 | /12 |
| Coding Problems | Q13–Q25 | /13 |
| System Design | Q26–Q35 | /10 |
| Rapid Fire | Q36–Q45 | /10 |
| Behavioral | Q46–Q50 | /5 |
| **Total** | **50 questions** | **/50** |

Score yourself:
- **45–50**: You're ready. Sleep.
- **38–44**: Review the ones you missed. Sleep by 11pm.
- **<38**: Focus on coding problems Q13–Q19 — those are the core. Everything else is secondary.

---

*Good luck tomorrow, Pratham.*
