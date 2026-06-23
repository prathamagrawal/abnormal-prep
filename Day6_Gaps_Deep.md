# Day 6 — Gaps Deep Dive
### Pratham | June 23, 2026 | Night before interview

> These are the specific gaps found after reviewing ALL your notes and code.
> Your fundamentals are solid. These are the sharp edges.

---

## Gap 1 — Regex: `\b\w+\b` vs `[A-Za-z']+` — You Use Both, Know Why

Your own code uses both patterns. If the interviewer sees this and asks, you need a clear answer.

```python
# Pattern 1 — word boundary + word chars
re.findall(r"\b\w+\b", text.lower())
# Matches: "hello", "world", "don", "t"  ← splits "don't" into two tokens
# Includes digits: "abc123" matches

# Pattern 2 — only letters + apostrophe
re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text.lower())
# Matches: "hello", "world", "don't"  ← keeps contractions as one word
# Does NOT match digits or underscores

# Pattern 3 — from Day1 notes
re.findall(r"[a-z']+", text.lower())
# Same as Pattern 2 but already lowercased — also matches standalone apostrophes
# Edge case: "'" alone matches — add \w check or use Pattern 2
```

### What to say
> "I use `[A-Za-z]+(?:'[A-Za-z]+)?` when I want to preserve contractions like 'don't' as one token. I use `\b\w+\b` when digits should count as word characters. The choice depends on the spec — I'd ask upfront."

---

## Gap 2 — Timestamp-Based vs Count-Based Sliding Window

Your `prep.py` uses **timestamp-based** eviction. Your `Day1_WordCount.md` uses **count-based** (window of N words). These are different problems. Know which one is being asked.

```python
# COUNT-BASED window: last N words
class SlidingWindowCounter:
    def __init__(self, window_size: int):
        self.window = deque()     # stores words (no timestamp)
        self.counts = Counter()
        self.size = window_size

    def process(self, word: str) -> None:
        self.window.append(word)
        self.counts[word] += 1
        if len(self.window) > self.size:          # evict when count exceeds N
            evicted = self.window.popleft()
            self.counts[evicted] -= 1
            if self.counts[evicted] == 0:
                del self.counts[evicted]


# TIMESTAMP-BASED window: last T seconds
class TimestampSlidingWindowCounter:
    def __init__(self, window_seconds: int):
        self.window = deque()     # stores (timestamp, word)
        self.counts = Counter()
        self.window_seconds = window_seconds

    def process(self, timestamp: int, word: str) -> None:
        self.window.append((timestamp, word))
        self.counts[word] += 1
        # evict words older than window
        while self.window and self.window[0][0] <= timestamp - self.window_seconds:
            _, evicted = self.window.popleft()
            self.counts[evicted] -= 1
            if self.counts[evicted] == 0:
                del self.counts[evicted]
```

### Bug in your dayone_ad.py — know this
```python
# YOUR CODE HAS: self.queue.popleft()  ← NameError, attribute is self.deque
# The field is named self.deque but you called self.queue — would crash at runtime
# Always name your deque field consistently: self.window or self.dq
```

### What to say
> "If they say 'last N words' I use count-based. If they say 'last 60 seconds' I use timestamp-based with `(timestamp, word)` tuples in the deque and a while loop to evict expired entries."

---

## Gap 3 — Heap Lazy Deletion (You Implemented It, Never Explained It)

Your `dayone_ad.py` implements a heap with lazy deletion for `top_k`. If the interviewer asks "why not just use `Counter.most_common()`?", you need to explain this.

### The problem with Counter.most_common() for streaming
```python
# Counter.most_common(k) scans ALL entries every call
# O(D) where D = number of distinct words in window
# Fine for small D, terrible when D = 100,000+
```

### Heap with lazy deletion — O(log D) per update
```python
import heapq
from collections import Counter, deque

class StreamingTopK:
    def __init__(self, window_size: int, k: int):
        self.window = deque()
        self.counts = Counter()
        self.heap = []    # min-heap of (-count, word)
        self.size = window_size
        self.k = k

    def add(self, word: str) -> None:
        self.window.append(word)
        self.counts[word] += 1
        heapq.heappush(self.heap, (-self.counts[word], word))   # push new count

        if len(self.window) > self.size:
            evicted = self.window.popleft()
            self.counts[evicted] -= 1
            if self.counts[evicted] == 0:
                del self.counts[evicted]
            # DON'T remove from heap — mark as stale, clean lazily on query

    def top_k(self) -> list[tuple[str, int]]:
        result = []
        temp = []

        while self.heap and len(result) < self.k:
            neg_count, word = heapq.heappop(self.heap)
            actual_count = self.counts.get(word, 0)

            if actual_count == -neg_count:          # still fresh
                result.append((word, actual_count))
                temp.append((neg_count, word))
            # else: stale entry — discard silently

        for item in temp:
            heapq.heappush(self.heap, item)

        return result
```

### What to say
> "For high-throughput streaming with frequent top_k queries, I use lazy deletion. Stale heap entries are discarded at query time rather than cleaned eagerly on every eviction. This keeps updates at O(log D) and avoids O(D) full scans."

---

## Gap 4 — Counter Arithmetic — The Tricky Parts

You know `Counter.most_common()`. The interviewer may probe deeper.

```python
from collections import Counter

a = Counter({"the": 3, "cat": 2, "sat": 1})
b = Counter({"the": 1, "mat": 2})

# Addition — union, sums counts
a + b  # Counter({"the": 4, "mat": 2, "cat": 2, "sat": 1})

# Subtraction — removes negatives and zeros
a - b  # Counter({"the": 2, "cat": 2, "sat": 1})  ← "mat" gone (0 or negative)

# Intersection — min of counts
a & b  # Counter({"the": 1})  ← only shared keys, minimum count

# Union — max of counts
a | b  # Counter({"the": 3, "mat": 2, "cat": 2, "sat": 1})

# Counter["missing"] returns 0, not KeyError
a["xyz"]  # 0

# most_common() with negatives — careful
c = Counter({"a": -1, "b": 2})
c.most_common()  # [("b", 2), ("a", -1)]  ← negatives included in iteration
c.most_common(1) # [("b", 2)]

# Subtracting to zero doesn't auto-delete
c = Counter({"a": 1})
c["a"] -= 1
c  # Counter({"a": 0})  ← zero entry stays unless you del c["a"]
# This is the memory leak in your SlidingWindow if you forget `del`
```

### What to say
> "Counter arithmetic treats subtraction as removing negatives. The key gotcha is that `c[word] -= 1` leaves a zero entry — it doesn't auto-delete. In a sliding window that's a memory leak, so I explicitly `del self.counts[word]` when the count hits zero."

---

## Gap 5 — GIL, Thread Safety, and `Counter`

Your notes mention the GIL but the nuance is missing.

```python
# The GIL protects individual Python bytecode instructions
# BUT compound operations are NOT atomic

counts = {}

# This is NOT thread-safe — 3 separate bytecode ops:
# 1. LOAD counts["the"]
# 2. ADD 1
# 3. STORE back to counts["the"]
counts["the"] = counts.get("the", 0) + 1  # race condition

# Counter is also NOT thread-safe for += operations
# Even though Counter itself is a dict subclass

# Thread-safe options:
# 1. threading.Lock() — serializes, correct but slow
# 2. Partition input — no shared state, merge at end (preferred)
# 3. queue.Queue + single writer thread — one writer, many readers

# For CPU-bound work: use ProcessPoolExecutor (bypasses GIL)
# For I/O-bound work: ThreadPoolExecutor is fine (GIL releases on I/O)
```

### The partition pattern — the clean answer
```python
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

def count_chunk(words: list[str]) -> Counter:
    return Counter(words)

def parallel_count(text: str, workers: int = 4) -> Counter:
    words = text.lower().split()
    chunk_size = max(1, len(words) // workers)
    chunks = [words[i:i+chunk_size] for i in range(0, len(words), chunk_size)]

    with ProcessPoolExecutor(max_workers=workers) as ex:  # ProcessPool for CPU-bound
        partials = list(ex.map(count_chunk, chunks))

    final = Counter()
    for c in partials:
        final.update(c)
    return final
```

---

## Gap 6 — Unicode and Encoding

You use `encoding='utf-8'` but never explain why it matters.

```python
# Without encoding, Python uses the system default (may be ASCII on some systems)
# This will raise UnicodeDecodeError on non-ASCII text

# Wrong:
with open(filepath, 'r') as f:        # system default encoding
    ...

# Right:
with open(filepath, 'r', encoding='utf-8') as f:
    ...

# Handling encoding errors gracefully:
with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
    # 'ignore' skips undecodable bytes
    # 'replace' substitutes with replacement character
    ...

# Normalize Unicode before counting — 'café' vs 'cafe\u0301' are different strings
import unicodedata
def normalize(word: str) -> str:
    return unicodedata.normalize('NFC', word)
```

### What to say
> "I always specify `encoding='utf-8'`. Without it Python falls back to the system locale which may be ASCII, causing `UnicodeDecodeError` on any non-ASCII character. If the data is dirty I'd add `errors='ignore'` or normalize with `unicodedata.normalize`."

---

## Gap 7 — Backpressure in Streaming

If they ask about your streaming design at high throughput:

```
Scenario: producer sends 1M words/sec, consumer processes 200K/sec

Without backpressure:
  → queue grows unboundedly → OOM
  → or you drop messages → inaccurate counts

Solutions:

1. Bounded queue (maxsize)
   queue = Queue(maxsize=10000)
   Producer blocks when queue is full → natural backpressure

2. Kafka: consumer lag as the signal
   → Consumer falls behind → increase partitions or consumers
   → Monitor consumer group lag (kafka-consumer-groups.sh)

3. Load shedding
   → Explicitly drop messages when queue is full
   → Acceptable for approximate counting (CMS) but not exact billing

4. Token bucket rate limiting on producer
   → Producer sends at controlled rate regardless of burst

```

### What to say
> "Backpressure means the consumer signals the producer to slow down when it can't keep up. In Python I'd use a bounded `Queue(maxsize=N)` which blocks the producer. In Kafka, consumer lag is the metric — you scale consumers or add partitions when lag grows beyond your SLA."

---

## Gap 8 — Walrus Operator (Used in Your Notes, Never Explained)

Your `prepinterview.md` uses it:

```python
while chunk := f.read(chunk_size):
    yield chunk
```

Know what this is in case they ask.

```python
# Walrus operator (:=) assigns and tests in one expression
# Introduced in Python 3.8

# Without walrus:
chunk = f.read(1024)
while chunk:
    process(chunk)
    chunk = f.read(1024)   # repeated read call

# With walrus:
while chunk := f.read(1024):   # assigns to chunk AND tests truthiness
    process(chunk)

# Also useful in comprehensions:
filtered = [y for x in data if (y := transform(x)) is not None]
```

---

## Gap 9 — `\b\w+\b` Matches Digits — Quick Gotcha

```python
import re

text = "Version 3.14 of hello2world"

re.findall(r"\b\w+\b", text)
# ['Version', '3', '14', 'hello2world']  ← digits match, decimal splits

re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)
# ['Version', 'of', 'hello', 'world']  ← only letters, splits hello2world

# For a word count interview: letters only is almost always correct
# Ask: "Should '2022' count as a word?"
```

---

## Summary — What to Confirm You Can Do

- [ ] Explain the regex choice (`[A-Za-z']+` vs `\b\w+\b`) in one sentence
- [ ] Implement count-based sliding window from scratch in 3 minutes
- [ ] Implement timestamp-based sliding window from scratch in 4 minutes
- [ ] Explain heap lazy deletion in 2 sentences
- [ ] Explain why `Counter[word] -= 1` is a memory leak without explicit `del`
- [ ] Explain why `+=` on a shared Counter is not thread-safe despite the GIL
- [ ] Say "backpressure" and describe bounded queue + Kafka consumer lag
- [ ] Explain `encoding='utf-8'` and `errors='ignore'`

---

*These are the last 5% that separate "solid" from "sharp". Sleep well.*
