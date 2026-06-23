# Count-Min Sketch + Approximate Counting
### For high-throughput streaming where exact counts aren't needed

---

## Why You Need This

At Level 4 of the WordCount escalation, if the interviewer says:
> "Words arrive at 1 million/second. You can't store every word. What do you do?"

**Answer: Count-Min Sketch** (or HyperLogLog for cardinality). Know this cold.

---

## The Problem with Exact Counting at Scale

```
1 million words/second → after 1 hour:
  - 3.6 billion words processed
  - If 10 million unique words, Counter needs ~10M entries in RAM
  - At 50 bytes per entry = 500MB just for the counter
  - For terabytes of data: impossible

Solution: Accept bounded error in exchange for O(1) memory.
```

---

## Count-Min Sketch — What It Is

A probabilistic data structure that:
- Uses a 2D array of counters (`d` rows × `w` columns)
- Uses `d` independent hash functions (one per row)
- Gives you approximate frequency with bounded error
- Uses **constant memory** regardless of vocabulary size

### The core idea

```
Table (d=3 rows, w=5 cols):

         col0  col1  col2  col3  col4
hash_0:  [  0,   3,   0,   1,   0 ]
hash_1:  [  0,   0,   4,   0,   0 ]
hash_2:  [  1,   0,   0,   3,   0 ]

To add word "cat":
  row 0: hash_0("cat") % 5 = 2 → table[0][2] += 1
  row 1: hash_1("cat") % 5 = 2 → table[1][2] += 1
  row 2: hash_2("cat") % 5 = 0 → table[2][0] += 1

To estimate count("cat"):
  min(table[0][2], table[1][2], table[2][0])
  → Take the MINIMUM across all rows (that's the "min" in Count-Min)
```

### Python sketch (minimal, readable)

```python
import hashlib

class CountMinSketch:
    def __init__(self, width: int = 1000, depth: int = 5):
        self.width = width
        self.depth = depth
        self.table = [[0] * width for _ in range(depth)]
        self.seeds = list(range(depth))  # different seeds = different hash fns

    def _hash(self, word: str, seed: int) -> int:
        h = hashlib.md5(f"{seed}{word}".encode()).hexdigest()
        return int(h, 16) % self.width

    def add(self, word: str) -> None:
        for row, seed in enumerate(self.seeds):
            col = self._hash(word, seed)
            self.table[row][col] += 1

    def estimate(self, word: str) -> int:
        return min(
            self.table[row][self._hash(word, seed)]
            for row, seed in enumerate(self.seeds)
        )

# Usage
sketch = CountMinSketch(width=1000, depth=5)
for word in stream:
    sketch.add(word)

print(sketch.estimate("the"))  # approximate count, may overestimate, never underestimate
```

---

## How to Explain It in the Interview

> "For high-throughput streaming where exact counts aren't necessary — like tracking trending topics — I'd use a Count-Min Sketch. It's a 2D array with `d` rows and `w` columns. Each word hashes to one column per row using different hash functions, and we increment those cells. To estimate a count, we take the minimum across all rows. It can overestimate due to hash collisions, but never underestimates, and the error is bounded. Memory is constant — just `d × w` integers — regardless of how many unique words you've seen."

---

## Error Guarantees

```
With width=w and depth=d:

  Error bound:  estimate ≤ true_count + ε × N
    where ε = e/w  (e ≈ 2.718)
    and N = total items processed

  Failure probability: δ = e^(-d)

  To achieve ε=0.01 and δ=0.01:
    w = ceil(e / 0.01) = 272
    d = ceil(ln(1/0.01)) = 5

So a 5 × 272 table (1360 integers) tracks frequencies with 1% error.
```

---

## Count-Min Sketch vs Exact Counter

| Property | Counter (dict) | Count-Min Sketch |
|---|---|---|
| Memory | O(unique words) | O(d × w) — constant |
| Accuracy | Exact | Approximate — may overcount |
| Speed | O(1) amortized | O(d) |
| Undercount? | Never | Never |
| Overcount? | Never | Yes (bounded) |
| When to use | Small vocab, exact billing | Huge vocab, trending, analytics |

---

## HyperLogLog — For Cardinality (Distinct Count)

If they ask "how many UNIQUE words have you seen?" — this is HyperLogLog, not Count-Min Sketch.

```
Count-Min Sketch  → "how often does word X appear?"
HyperLogLog       → "how many distinct words have appeared?"
```

### How HyperLogLog works (just know the concept)

```
Key insight: In a random bit stream, the probability of seeing
k leading zeros is 1/2^k.

HyperLogLog hashes each item and records the max leading zeros seen.
The distinct count estimate is 2^(max_leading_zeros).

Uses ~1.5 KB of memory for ±2% error, regardless of cardinality.

Redis has HLL built-in: PFADD, PFCOUNT
```

### In the interview

> "If you're asking about distinct word count rather than frequency, HyperLogLog is the right tool. It uses O(log log n) space and gives ±2% error. Redis has it built-in as PFADD/PFCOUNT."

---

## When to Use Each Approach

```
Exact counting (dict/Counter):
  → Small vocabulary (< millions of unique words)
  → Billing, deduplication — must be exact
  → Batch jobs where memory isn't a constraint

Count-Min Sketch:
  → High throughput streaming (100K+ events/sec)
  → Approximate trending topics, frequency estimation
  → When you can tolerate slight overcount

HyperLogLog:
  → Distinct count queries (unique visitors, unique words)
  → Very large cardinality (billions of distinct items)
  → Can tolerate 2% error

External Sort / MapReduce:
  → Exact counts across terabytes that don't fit in RAM
  → Batch — not real-time
```

---

## One-Liner for Interview

> "Count-Min Sketch: O(1) memory, O(d) update, approximate counts that never underestimate, bounded overcount. Use it when exact counts aren't required and throughput is extreme."
