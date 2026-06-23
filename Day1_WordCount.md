# Day 1 — WordCount Deep Dive
### Monday, June 22 | Goal: Be completely fluent in WordCount at every level

---

## How This Round Will Actually Go

Ubaid will start simple and escalate. The escalations are the real test — not the base problem.

| Level | What It Tests |
|---|---|
| Basic word count | Data structures, clean code |
| Top-K | Heap vs sort trade-off reasoning |
| Large file | Memory-aware thinking |
| Streaming | Stateful, time-aware thinking |
| Concurrent | Thread safety, partitioning |
| Distributed | System design instincts |

**He is evaluating:** Do you ask the right questions? Do you think before coding? Can you adapt when requirements change?

---

## Clarifying Questions to Open With

Before writing a single line, ask these. They signal engineering maturity.

```
1. "What's the input format — a string, a file path, or a stream?"
2. "Should counting be case-sensitive? Default: probably no."
3. "How should we handle punctuation? Strip it? Treat 'don't' as one word or two?"
4. "What's the expected scale — a paragraph, megabytes, or terabytes?"
5. "Do you want the full frequency map, or just Top-K most frequent?"
6. "Any special tokens to ignore — stopwords like 'the', 'a', 'is'?"
```

Say these out loud. Silence at the start looks bad. Questions look great.

---

## Level 1 — Basic Word Count

### Problem
```
Input:  "Hello world hello WORLD!"
Output: {"hello": 2, "world": 2}
```

### Solution
```python
def word_count(text: str) -> dict[str, int]:
    if not text or not isinstance(text, str):
        return {}

    counts: dict[str, int] = {}
    for word in text.lower().split():
        word = word.strip('.,!?";:\'()-[]{}')
        if word:
            counts[word] = counts.get(word, 0) + 1
    return counts
```

### Cleaner with Counter + regex
```python
import re
from collections import Counter

def word_count_clean(text: str) -> dict[str, int]:
    if not text:
        return {}
    words = re.findall(r"[a-z']+", text.lower())  # handles contractions
    return dict(Counter(words))
```

### Common Traps at Level 1
- `"hello!".split()` gives `["hello!"]` — strip punctuation or use regex
- Case: `"Hello" != "hello"` — always `.lower()` first
- Empty string: `"".split()` returns `[]`, fine, but check explicitly
- `"don't"` — one word or two? **Ask.**

### What to Say
> "I'll lowercase, split on whitespace, and strip punctuation. For production I'd use regex to be precise, but let me start simple."

---

## Level 2 — Top-K Most Frequent Words

### Problem
```
Input: "the cat sat on the mat the cat", k=2
Output: [("the", 3), ("cat", 2)]
```

### Two Approaches — Know Both

**Sort — simple, O(n log n)**
```python
from collections import Counter

def top_k_sort(text: str, k: int) -> list[tuple[str, int]]:
    counts = Counter(text.lower().split())
    return counts.most_common(k)  # built-in, uses heapq internally
```

**Heap — optimal when k << n, O(n log k)**
```python
import heapq
from collections import Counter

def top_k_heap(text: str, k: int) -> list[tuple[str, int]]:
    counts = Counter(text.lower().split())
    return heapq.nlargest(k, counts.items(), key=lambda x: x[1])
```

### Complexity Table

| Approach | Time | Space | Use When |
|---|---|---|---|
| Sort all | O(n log n) | O(n) | k close to n |
| Min-heap of size k | O(n log k) | O(k) | k << n |
| `Counter.most_common(k)` | O(n log k) | O(n) | Default in Python |

### Tie-breaking
```python
# Sort by (-count, word) for stable alphabetical tie-breaking
def top_k_stable(text: str, k: int) -> list[tuple[str, int]]:
    counts = Counter(text.lower().split())
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:k]
```

### What to Say
> "Sort is O(n log n). Heap is O(n log k) — better when k is small. I'll use `Counter.most_common(k)` which is idiomatic Python. Should I implement the heap manually?"

---

## Level 3 — Large File (Doesn't Fit in Memory)

### Problem
```
File is 50GB. You can't load it into RAM.
Count word frequencies across the entire file.
```

### Key Insight
> Python file iterators are already generators. Iterating line by line never loads the full file.

### Solution
```python
from collections import Counter

def word_count_large_file(filepath: str) -> Counter:
    counts = Counter()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:          # one line at a time — O(1) memory per line
            counts.update(line.lower().split())
    return counts
```

### Generator pattern — show this if asked
```python
def read_words(filepath: str):
    """Yields one cleaned word at a time."""
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            for word in line.lower().split():
                yield word.strip('.,!?";:')

# Usage: Counter(read_words(filepath))
```

### If even the Counter is too big (billions of unique words)
```
Strategy: External Sort

1. Read file in chunks
2. Compute partial counts per chunk → write to temp file on disk
3. K-way merge of temp files (external merge sort)
   → This is MapReduce applied locally

MapReduce mental model:
  Map phase    → each worker processes a chunk, emits (word, 1)
  Shuffle      → group all (word, *) pairs by key
  Reduce phase → sum counts per word
```

### What to Say
> "Python file iteration is a generator — O(1) memory per line. If even the Counter overflows, I'd use external sort: write partial counts to disk, then k-way merge. This is essentially MapReduce."

---

## Level 4 — Streaming Input

### Problem
```
Words arrive one at a time continuously.
a) Count all words seen so far
b) Count words in a sliding window of last N words
```

### 4a — Unbounded stream
```python
from collections import Counter

class StreamCounter:
    def __init__(self):
        self.counts: Counter = Counter()

    def process(self, word: str) -> None:
        self.counts[word.lower().strip('.,!?')] += 1

    def top_k(self, k: int) -> list[tuple[str, int]]:
        return self.counts.most_common(k)
```

### 4b — Sliding window (last N words)
```python
from collections import Counter, deque

class SlidingWindowCounter:
    def __init__(self, window_size: int):
        self.window: deque = deque()
        self.counts: Counter = Counter()
        self.size = window_size

    def process(self, word: str) -> None:
        word = word.lower().strip('.,!?')
        self.window.append(word)
        self.counts[word] += 1

        if len(self.window) > self.size:
            evicted = self.window.popleft()
            self.counts[evicted] -= 1
            if self.counts[evicted] == 0:
                del self.counts[evicted]  # avoid memory leak

    def top_k(self, k: int) -> list[tuple[str, int]]:
        return self.counts.most_common(k)
```

### What to Say
> "Deque gives O(1) append and popleft. I maintain a Counter alongside it — increment on arrival, decrement on eviction, delete at zero to avoid memory leak."

### Approximate counting — if they push you
> "For very high throughput where exact counts aren't needed, Count-Min Sketch uses a 2D array with multiple hash functions. O(1) per update with bounded error. Trade-off: probabilistic."

---

## Level 5 — Concurrent Workers

### Problem
```
Multiple threads process portions of the text simultaneously.
They update a shared word count dict.
What goes wrong?
```

### The Bug — Race Condition
```python
# BROKEN
counts = {}

def worker(words):
    for word in words:
        counts[word] = counts.get(word, 0) + 1
        # Two threads both read counts["the"]=5, both write 6. Should be 7.
```

### Fix 1 — Lock (simple, correct, serializes access)
```python
import threading
from collections import defaultdict

counts = defaultdict(int)
lock = threading.Lock()

def worker(words):
    for word in words:
        with lock:
            counts[word] += 1
```

### Fix 2 — Partition by key (no shared state, better)
```python
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

def count_partition(words: list[str]) -> Counter:
    return Counter(words)

def parallel_word_count(text: str, num_workers: int = 4) -> Counter:
    words = text.lower().split()
    chunk_size = max(1, len(words) // num_workers)
    chunks = [words[i:i+chunk_size] for i in range(0, len(words), chunk_size)]

    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        partials = list(ex.map(count_partition, chunks))

    final = Counter()
    for c in partials:
        final.update(c)
    return final
```

### What to Say
> "Race condition is on read-modify-write — two threads read the same value, both increment locally, one write is lost. Fix 1: lock — correct but serializes. Fix 2: partition input so threads have no overlap, merge at the end. No locks needed. This is the MapReduce pattern."

### GIL note
> "In CPython, for CPU-bound work, threading doesn't give real parallelism due to the GIL. Use `ProcessPoolExecutor` instead."

---

## Level 6 — Distributed (Coding Ends, Design Begins)

Don't code this. Just talk through it.

```
"Count words across 1TB of text on 100 machines."

1. PARTITION — assign each machine a slice (S3, HDFS, Kafka)
2. MAP phase — each machine processes its slice independently
               emits (word, local_count) — no inter-machine communication
3. SHUFFLE — route all (word, *) pairs to the same reducer
             hash(word) % num_reducers → consistent hashing
4. REDUCE — each reducer sums counts for its words
5. QUERY — store in Redis or DB, cache top-K (read-heavy)
```

### What to Say
> "Map phase is embarrassingly parallel. Shuffle is the bottleneck — consistent hashing ensures the same word always routes to the same reducer. Reduce is parallel too. For Top-K at this scale I'd pre-compute and cache instead of computing at query time."

---

## Python Patterns Cheatsheet

```python
from collections import Counter, defaultdict, deque
import heapq, re

# Counter
c = Counter("hello world hello".split())
c.most_common(2)        # [('hello', 2), ('world', 1)]
c["missing"]            # returns 0, no KeyError
c.update(["hello"])     # merge from iterable

# defaultdict
d = defaultdict(int)
d["word"] += 1          # no KeyError

# deque
q = deque(maxlen=100)   # auto-evicts oldest — great for fixed sliding window
q.append("x")
q.popleft()             # O(1) vs list.pop(0) which is O(n)

# heapq
heapq.nlargest(k, counts.items(), key=lambda x: x[1])  # O(n log k)

# regex tokenization
words = re.findall(r"[a-z']+", text.lower())
```

---

## Common Traps

| Trap | Wrong | Right |
|---|---|---|
| Punctuation attached | `"hello!"` counted as-is | Strip or use regex |
| Case mismatch | `"Hello" != "hello"` | `.lower()` first |
| Missing key | `counts["word"]` raises | `.get("word", 0)` or Counter |
| Queue pop | `list.pop(0)` is O(n) | `deque.popleft()` is O(1) |
| Top-K with sort | O(n log n) | `heapq.nlargest()` O(n log k) |
| Loading whole file | Memory error | Iterate line by line |
| Mutable default arg | `def f(d={})` — shared state | `def f(d=None): d = d or {}` |

---

## Today's Practice Plan

1. **(2 hrs)** Code Level 1–4 from memory, without looking at this file
2. **(1.5 hrs)** Open a blank editor, set a 5-min timer, say clarifying questions out loud, then code while narrating
3. **(30 min)** Test edge cases: empty string, single word, all same word, punctuation-heavy text

*Tomorrow: System Design.*
