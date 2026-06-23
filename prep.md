# Word Count Interview Practice Guide

A collection of realistic coding, design, and Python interview questions, ordered by difficulty and topic. These are the kinds of follow-up questions an interviewer is likely to ask, especially during backend and systems interviews.

---

# 1. Coding — Word Count Escalations

## Round 1 — Warm-up

### Question 1

Implement:

```python
word_count(text)
```

Requirements:

* Count word frequencies
* Ignore punctuation
* Case-insensitive
* Handle empty input
* No imports except built-ins

Think about:

* Time complexity
* Space complexity
* Edge cases

---

### Question 2

Rewrite the solution using only:

```python
re.findall(...)
```

Discuss:

* Which regex would you use?
* What cases does it correctly handle that `str.split()` does not?
* What are the trade-offs?

---

## Round 2 — Top-K

### Question 3

Given a text corpus, return the **Top 3 most frequent words**.

Implement it:

* Without `collections.Counter`
* Without `sorted()`
* Using only a raw heap

Explain:

* Heap operations
* Complexity

---

### Question 4

Compare:

```python
heapq.nlargest(k, items)
```

vs

```python
sorted(items, reverse=True)[:k]
```

Discuss:

* Time complexity
* Memory usage
* When one is preferable over the other

---

### Question 5

Two words have identical frequencies.

Your function sometimes returns:

```
apple
banana
```

and sometimes:

```
banana
apple
```

Questions:

* Why does this happen?
* What determines the ordering?
* How can you make the output deterministic?

---

## Round 3 — Memory & Large Files

### Question 6

You have:

* A **100 GB** log file
* Only **512 MB RAM**

Find the **Top 10 most frequent words**.

Walk through the complete design.

Discuss:

* Streaming
* Chunk processing
* External sorting
* Multi-pass approaches
* Memory limitations

---

### Question 7

What's wrong with this code?

```python
def count_file(path):
    return Counter(open(path).read().split())
```

List **every** problem you can find.

Examples include:

* Memory usage
* File handling
* Resource leaks
* Tokenization issues
* Error handling
* Encoding assumptions

---

### Question 8

Write a generator that:

* Reads a file lazily
* Cleans each word
* Yields one word at a time

Then use it to build a `Counter`.

Finally explain:

* Why generators are preferable
* Memory advantages
* Streaming benefits

---

## Round 4 — Streaming Systems

### Question 9

Words arrive:

* One word every second
* Forever

Design a data structure that supports:

* Top 5 words
* Over the **last 60 seconds**

At any moment.

Discuss:

* Sliding window
* Data structures
* Complexity of each operation

---

### Question 10

Now the arrival rate increases to:

**1000 words/sec**

Questions:

* Does your previous design still work?
* What becomes the bottleneck?
* How would you redesign it?

---

### Question 11

Explain:

**Count-Min Sketch**

Cover:

* What problem it solves
* When to use it
* Accuracy guarantees
* Memory savings
* Trade-offs versus an exact `Counter`

---

## Round 5 — Concurrency

### Question 12

Demonstrate a race condition on a shared dictionary.

Show:

* Two threads
* Interleaved execution
* Exactly how incorrect counts occur

---

### Question 13

You protected the shared dictionary with:

```python
threading.Lock()
```

Now performance is **worse than single-threaded**.

Explain:

* Why?
* What causes contention?
* How would you eliminate the lock?

---

### Question 14

Compare:

* `ThreadPoolExecutor`
* `ProcessPoolExecutor`

For each discuss:

* CPU-bound workloads
* I/O-bound workloads
* GIL implications
* Which is better for word counting?

---

### Question 15

You have:

* 1 million words
* 8 worker threads

How would you:

1. Partition the work?
2. Prevent overlapping work?
3. Merge the partial counts efficiently?

---

# 2. System Design Questions

These are verbal questions. Practice answering them aloud.

---

### Question 16

Design a word-count system supporting:

```text
add(word)
get_count(word)
top_k(k)
```

Goal:

* O(1) operations if possible

Discuss:

* Whether this is achievable
* Real-world complexity
* Trade-offs

---

### Question 17

Your service receives:

**100,000 words/second** from a Kafka topic.

Design the architecture.

Cover:

* Consumers
* Partitioning
* Aggregation
* Storage
* Scaling
* Failure handling
* Bottlenecks

---

### Question 18

A provisioning workflow has:

```
Step 1 ✅
Step 2 ✅
Step 3 ✅
Step 4 ✅
Step 5 ❌
Step 6
Step 7
Step 8
```

What are your options?

Discuss:

* Retry
* Rollback
* Compensation
* Resume from checkpoint
* Idempotency
* Trade-offs

---

### Question 19

Your SQL query is becoming slow:

```sql
SELECT word, count
FROM word_counts
ORDER BY count DESC
LIMIT 10;
```

How would you optimize it?

Consider:

* Indexes
* Materialized views
* Caching
* Denormalization
* Heap-based approaches
* Precomputed rankings

---

# 3. Tricky Python & Edge Cases

### Question 20

What does this return?

```python
Counter("hello world".split()) + Counter("world foo".split())
```

Explain exactly why.

---

### Question 21

What's wrong with this sliding window?

```python
def process(self, word):
    self.window.append(word)

    if len(self.window) > self.size:
        self.window.pop(0)
```

Discuss:

* Time complexity
* Better data structures
* Why `deque` is preferred

---

### Question 22

Why is this dangerous?

```python
def word_count(text, stopwords=[]):
```

A caller modifies `stopwords`.

The next call unexpectedly sees those changes.

Explain:

* Why it happens
* Python's function defaults
* The correct fix

---

### Question 23

You are processing **50 files** using:

```python
ProcessPoolExecutor
```

Each worker returns a `Counter`.

How would you merge them efficiently?

Discuss:

* `Counter.update()`
* `Counter +=`
* Memory considerations
* Complexity

---

# 4. Practice Strategy

### Coding Practice

* Pick **5 questions**
* Set a **25-minute timer**
* Solve while narrating your thought process aloud

---

### Design Practice

For each design question:

* Do **not** write code
* Speak continuously for **5 minutes**
* Explain assumptions, trade-offs, bottlenecks, and complexity

---

### Self-Review Checklist

After every question, ask yourself:

* ✅ Did I state the time complexity?
* ✅ Did I state the space complexity?
* ✅ Did I cover edge cases?
* ✅ Did I explain trade-offs?
* ✅ Did I justify my design choices?

---

# ⭐ Highest-Priority Questions

If you're short on time, focus on these first:

1. **Question 6** — Large file processing (100 GB log)
2. **Question 9** — Sliding window streaming design
3. **Question 13** — Lock contention and concurrency
4. **Question 16** — Word count system design
5. **Question 18** — Provisioning failure recovery

These questions tend to separate strong backend candidates from average ones.
