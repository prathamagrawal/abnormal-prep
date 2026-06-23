# System Design Concepts — Reference Sheet
### Core concepts you need for the Abnormal AI interview

> This complements your system-specific notes (Day2_SystemDesign.md).
> These are the foundational concepts that explain WHY you make the design choices you do.

---

## 1. CAP Theorem

### What It Is

Any distributed system can guarantee at most 2 of these 3 properties:

```
C — Consistency:    Every read sees the most recent write
A — Availability:   Every request gets a response (no timeouts)
P — Partition Tolerance: The system continues working even when network partitions occur

IMPORTANT: In a distributed system, partitions WILL happen.
So you always choose P + either C or A.
```

### CP vs AP

```
CP (Consistent + Partition Tolerant):
  → Sacrifice availability when partitioned
  → Returns error rather than stale data
  → Examples: HBase, Zookeeper, traditional RDBMS
  → Use when: banking, billing, inventory (can't show wrong count)

AP (Available + Partition Tolerant):
  → Returns possibly stale data rather than erroring
  → Eventually consistent
  → Examples: Cassandra, DynamoDB, CouchDB
  → Use when: social feeds, word counts, trending topics
```

### How to say it in the interview

> "For word counts I'd use Cassandra — it's AP: highly available, eventually consistent. We don't need to know the exact count of 'the' in real-time; a slightly stale number is fine. But for tenant configuration or billing records, I'd use Postgres — CP — because I need strong consistency: if a tenant's plan changes, every read must reflect that immediately."

---

## 2. Consistent Hashing

### Why `hash(word) % N` is broken

```
If you have 4 reducers and add a 5th:
  hash("the") % 4 = 2  → reducer 2
  hash("the") % 5 = 3  → reducer 3 ← ALL keys move!

With naive modulo: adding/removing one node remaps ~all keys.
This causes a massive reshuffle — catastrophic for distributed systems.
```

### What Consistent Hashing Does

```
Place nodes AND keys on a virtual ring (0 to 2^32).
A key belongs to the first node clockwise from its position on the ring.

Adding a node:  only keys between the new node and its predecessor move.
Removing a node: only keys from that node move to its successor.

On average, only K/N keys are remapped when adding one node
(where K = number of keys, N = number of nodes).
```

### Visual

```
Ring (0 to 360 degrees):

     Node A (at 60°)
   /
Ring ── Node B (at 180°) ── Node C (at 300°)

key "the"  hashes to 90° → goes to Node B (first node clockwise)
key "cat"  hashes to 220° → goes to Node C

Add Node D at 150°:
  key "the" (90°) → still Node B (closest clockwise is now D at 150°... wait: 150 > 90, yes)
  Actually "the" at 90° → D at 150° is next clockwise → only "the" moved, not "cat"
```

### Virtual Nodes

```
Problem: uneven distribution if nodes are few.
Solution: each physical node has multiple "virtual nodes" on the ring (e.g., 150 virtual nodes each).
This evens out the load distribution.

Used by: Cassandra, DynamoDB, Amazon S3
```

### How to say it in the interview

> "Simple modulo hashing breaks when you add or remove reducers — you'd have to rehash all keys. Consistent hashing puts nodes and keys on a virtual ring; a key belongs to the next node clockwise from it. Adding a node only moves the keys between it and its predecessor — roughly 1/N of keys. I'd use this for the shuffle phase in distributed word count so the system can scale horizontally without full reshuffling."

---

## 3. Kafka Deep Dive

### Core Concepts

```
Topic     → a named stream of messages (e.g., "word-events")
Partition → a topic is split into N ordered partitions (the unit of parallelism)
Offset    → position of a message within a partition (monotonically increasing)
Producer  → writes messages to a partition
Consumer  → reads from a partition, tracks its own offset
Consumer Group → set of consumers; Kafka assigns each partition to one consumer in the group
```

### Partition Assignment

```
Producer decides partition via:
  1. Explicit key → hash(key) % num_partitions
  2. Round-robin → if no key

For word count streaming:
  Partition key = word (or first letter)
  → All instances of "the" go to the same partition
  → One consumer handles all of "the" — no need to merge across consumers
```

### Why Kafka is Fast

```
1. Append-only writes → sequential disk I/O (fast)
2. Zero-copy transfer → data goes disk → network without CPU copy
3. Consumer reads → sequential reads from offset
4. Batching → producers buffer messages, flush in batches
```

### Consumer Groups and Scaling

```
1 topic, 4 partitions, 1 consumer group with 4 consumers:
  → Each consumer handles 1 partition
  → Perfect parallelism

Add 5th consumer to 4-partition topic:
  → One consumer sits idle — can't have more consumers than partitions

Scale: increase partition count (but it's a breaking change for keyed topics)
```

### Failure Handling in Kafka

```
At-most-once:  commit offset before processing → can lose messages on crash
At-least-once: commit after processing → may reprocess on crash (duplicates)
Exactly-once:  Kafka transactions (complex, expensive) → use idempotent consumers

For word count: at-least-once is fine (slight overcounting acceptable)
For billing: exactly-once required
```

### In the Interview

> "For 100K words/second I'd use Kafka. I'd partition the topic by word — hash(word) % num_partitions — so all instances of the same word go to the same partition and the same consumer. Each consumer maintains a local Counter and flushes to Cassandra periodically. Kafka handles backpressure, replay, and durability. The consumer group allows horizontal scaling up to the partition count."

---

## 4. Caching — Redis Patterns

### Redis Data Structures to Know

```
STRING      → simple key-value. SET word:the 4
HASH        → like a dict. HSET wordcounts the 4 cat 2
ZSET        → sorted set by score. ZADD top_words 4 "the" 2 "cat"
              ZREVRANGE top_words 0 9  ← top 10 by score
LIST        → ordered list. LPUSH / RPOPLPUSH
SET         → unordered unique members. SADD
```

### Top-K in Redis with ZSET

```
# Add or increment a word's score
ZINCRBY top_words 1 "the"

# Get top 10 words with their counts
ZREVRANGE top_words 0 9 WITHSCORES

# Why ZSET:
#   O(log N) insert/update
#   O(log N + K) for top-K query
#   Built-in sorted order — no need to sort at read time
```

### Cache Patterns

```
Cache-Aside (Lazy Loading):
  Read: check cache → if miss, load from DB, populate cache, return
  Write: write to DB, invalidate/update cache
  ✓ Simple, only loads what's needed
  ✗ Cache miss = 2 trips (cache + DB), initial cold start

Write-Through:
  Write: write to DB AND cache atomically
  ✓ Cache always warm
  ✗ Writes slower, may cache data that's never read

Write-Behind (Write-Back):
  Write: write to cache immediately, async flush to DB later
  ✓ Very fast writes
  ✗ Risk of data loss if cache crashes before flush
  → Good for word counts (losing a few counts is fine)
```

### Cache Invalidation Strategies

```
TTL-based:      Cache expires after N seconds → simplest, slight staleness
Event-based:    Invalidate cache when data changes → fresh but complex
LRU eviction:   Redis evicts least recently used when memory full
```

### In the Interview

> "For top-K word count queries, I'd maintain a Redis ZSET. Every time a word count is updated, I call ZINCRBY. Top-K reads are O(log N + K) using ZREVRANGE. This is a leaderboard pattern — the same approach used for gaming leaderboards, trending hashtags etc. I'd set a TTL or refresh on a schedule rather than maintaining real-time consistency."

---

## 5. Rate Limiting

### Why It Comes Up

If they ask about the API layer for the word count service or any API design, rate limiting is a standard component.

### Token Bucket Algorithm

```
Each user gets a "bucket" with max capacity T tokens.
Tokens refill at rate R per second.
Each request consumes 1 token.
If no tokens: reject with 429.

Properties:
  ✓ Allows short bursts up to T (bucket capacity)
  ✓ Steady-state rate = R requests/sec
  ✓ Simple to implement with Redis + TTL

Implementation:
  On each request:
    tokens = redis.get(user_id) or T
    if tokens > 0:
      redis.decr(user_id)
      allow_request()
    else:
      return 429
```

### Sliding Window Counter

```
Ironic: same pattern as the sliding window word count problem.

Track request timestamps in a deque.
On each request:
  - Remove timestamps older than window_size
  - If len(deque) < limit: allow, add timestamp
  - Else: reject 429

Or with Redis sorted set (ZSET):
  key = "ratelimit:{user_id}"
  ZADD key current_timestamp current_timestamp
  ZREMRANGEBYSCORE key -inf (now - window_size)
  count = ZCARD key
  if count > limit: reject
```

### In the Interview

> "For rate limiting I'd use token bucket — it allows short bursts while enforcing a steady-state rate. I'd store tokens in Redis per user with an atomic DECR operation. For stricter sliding window enforcement, I'd use a Redis ZSET with timestamps as scores, removing entries older than the window on each request."

---

## 6. Database — Indexing Deep Dive

### When to Index

```
Index these:
  ✓ Columns in WHERE clauses (especially high-cardinality)
  ✓ Columns in JOIN ON conditions
  ✓ Columns in ORDER BY on large tables
  ✓ Foreign keys

Don't index:
  ✗ Low-cardinality columns (status with 3 values — not worth it)
  ✗ Columns that are rarely queried
  ✗ Write-heavy tables with many indexes (each write must update all indexes)
```

### Index Types

```
B-Tree index (default):
  → Range queries: WHERE count BETWEEN 10 AND 100
  → Equality: WHERE word = 'the'
  → Order: ORDER BY count DESC

Hash index:
  → Equality only: WHERE word = 'the'
  → Faster than B-Tree for equality, useless for ranges

Composite index:
  → CREATE INDEX ON events(tenant_id, created_at)
  → Useful for: WHERE tenant_id = X AND created_at > Y
  → ORDER MATTERS: (tenant_id, created_at) ≠ (created_at, tenant_id)
  → Leftmost prefix rule: index works for (tenant_id) or (tenant_id, created_at)
                           but NOT for (created_at) alone
```

### The Trade-off in One Sentence

> "Every index speeds up reads but slows down writes — it must be updated on every INSERT, UPDATE, DELETE. On a write-heavy table like word_counts, over-indexing is dangerous."

---

## 7. Scalability Patterns — Quick Reference

### Horizontal vs Vertical Scaling

```
Vertical (scale up):   bigger machine, more RAM/CPU. Simple, has limits.
Horizontal (scale out): more machines. Requires stateless services, load balancer.

Stateless services: any instance can handle any request → trivially horizontal
Stateful services:  sticky sessions, or shared state via DB/cache
```

### Load Balancing Strategies

```
Round-robin:       equal distribution, simple
Least connections: route to instance with fewest active connections
IP hash:           same client always hits same server (session affinity)
```

### Sharding

```
Horizontal partitioning: split rows of a table across multiple DBs.
  By user_id: user 1-1M on DB1, 1M-2M on DB2
  By hash: hash(user_id) % num_shards
  By range: A-M on shard 1, N-Z on shard 2

Problems:
  Cross-shard queries: expensive or impossible
  Hotspots: if one shard gets more traffic
  Resharding: painful when you add shards
```

---

## Quick Reference — Storage Choices

| Requirement | Choose |
|---|---|
| Word frequency (write-heavy, simple lookup) | Cassandra / DynamoDB |
| Top-K word cache / leaderboard | Redis ZSET |
| Time-windowed analytics queries | ClickHouse / BigQuery |
| Tenant config (relational, ACID) | PostgreSQL |
| Session/cache with TTL | Redis STRING |
| Cardinality estimation (distinct count) | HyperLogLog (Redis PFADD) |
| Approximate frequency at scale | Count-Min Sketch |
| Real-time streaming ingestion | Kafka |
| Batch large files | S3 + Spark / Hadoop |

---

## The "Why" Behind Every Design Choice

Always explain your choices with this framework:
```
"I chose X because [requirement]. The trade-off is [downside].
If we needed [different requirement], I'd switch to [alternative]."
```

Example:
> "I chose Cassandra for word counts because we have massive write throughput and eventual consistency is acceptable — a slightly stale count of 'the' is fine. The trade-off is we lose strong consistency and complex queries. If we needed ACID guarantees — say for billing — I'd use Postgres instead."
