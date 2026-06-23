from collections import deque, Counter
import heapq


class SlidingTopKWords:
    def __init__(self, window_size=60):
        self.window_size = window_size

        # (timestamp, word)
        self.window = deque()

        # Current frequency of words in window
        self.counter = Counter()

        # Max heap (implemented as min heap using negative frequencies)
        self.heap = []

    def add_word(self, timestamp, word):
        """
        Add a new word arriving at 'timestamp'
        """

        # -------------------------
        # Add new word
        # -------------------------
        self.window.append((timestamp, word))
        self.counter[word] += 1

        # Push updated frequency
        heapq.heappush(self.heap, (-self.counter[word], word))

        # -------------------------
        # Remove expired words
        # -------------------------
        while self.window and self.window[0][0] <= timestamp - self.window_size:

            _, expired_word = self.window.popleft()

            self.counter[expired_word] -= 1

            if self.counter[expired_word] == 0:
                del self.counter[expired_word]
            else:
                # Push updated (decreased) frequency
                heapq.heappush(
                    self.heap,
                    (-self.counter[expired_word], expired_word)
                )

    def top_k(self, k=5):
        """
        Return top-k words.
        """

        answer = []

        # Store valid entries temporarily
        valid_entries = []

        while self.heap and len(answer) < k:

            neg_freq, word = heapq.heappop(self.heap)

            current_freq = self.counter.get(word, 0)

            # Is this entry stale?
            if current_freq != -neg_freq:
                continue

            answer.append((word, current_freq))
            valid_entries.append((neg_freq, word))

        # Put valid entries back
        for item in valid_entries:
            heapq.heappush(self.heap, item)

        return answer

stream = [
    (1, "apple"),
    (2, "banana"),
    (3, "apple"),
    (4, "cat"),
    (5, "apple"),
    (6, "banana"),
    (7, "dog"),
    (8, "apple"),
]

obj = SlidingTopKWords()

for t, w in stream:
    obj.add_word(t, w)

print(obj.top_k())


"""
"The deque and Counter still scale because inserts and expirations remain amortized O(1). The main bottleneck becomes Counter.most_common(5), since it scans all distinct words on every query. With 60,000 words in the window and potentially tens of thousands of unique words, query latency grows significantly. To address this, I'd maintain the top frequencies incrementally using a max-heap with lazy deletion, a frequency bucket structure, or a balanced tree keyed by frequency. This shifts work to updates and keeps top-5 queries much faster."
Complexity

For D distinct words:

Insert

Increment counter:

O(1)

Push into heap:

O(log D)

Overall

O(log D)

"""


"""
CMS
"A Count-Min Sketch is a probabilistic data structure for approximate frequency
counting in data streams. Instead of storing every key like a Counter, it
uses multiple hash functions to map each item into a fixed-size matrix of 
counters. Updates and queries are O(d), where d is the number of hash functions,
and memory is fixed regardless of the number of unique items. The tradeoff
is accuracy: due to hash collisions, counts can be overestimated but never
underestimated. I'd use it when processing massive streams where memory
efficiency is more important than exact counts, such as trending topics, 
network monitoring, or clickstream analytics."
"""