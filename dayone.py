import re
from collections import Counter

def read_words(filename):
    with open(filename, "r") as file:
        for line in file:
            for word in re.findall(r"\b[A-Za-z]+(?:'[A-Za-z]+)?\b", line.lower()):
                yield word

import re
from collections import Counter

def top_words(path):
    counter = Counter()

    with open(path) as f:
        for line in f:
            words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", line.lower())
            counter.update(words)

    return counter.most_common(10)

# import re
# import heapq

# def word_counter(sentence: str, k: int)-> list[tuple[str,int]]:
#     words = re.findall(r"\b\w+\b",sentence)
#     counter_dict : dict[str, int] = {}
#     for word in words:
#         counter_dict[word] = counter_dict.get(word,0) + 1
#         print(counter_dict)
#     return heapq.nlargest(k, counter_dict.items(), key = lambda x:(x[1],x[0]))



# def word_counter(sentence: str) -> dict:
#     # words = re.findall(r"\b\w+\b", sentence) # don't split "don't"
#     words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", sentence)
#     counter_dict : dict[str, int] = {}
#     for word in words:
#         counter_dict[word] = counter_dict.get(word,0) + 1
#     return counter_dict

# def word_counter(sentence):
#     if not sentence or not isinstance(sentence, str):
#         return {}

#     counter_dict: dict[str, int] = {}
#     for word in sentence.lower().split():
#         word = word.strip('.,!?";:\'()-[]{}')
#         if word:
#             counter_dict[word] = counter_dict.get(word,0) + 1
#     return counter_dict

from collections import deque, Counter

class SlidingWindowWordCounter:

    def __init__ (self, window = 60):
        self.window = window
        self.deque = deque()
        self.counter = Counter()

    def add_word(self,timestamp:int, word:int):
        self.deque.append((timestamp, word))
        self.counter[word] += 1

        #remove old
        while self.deque and self.deque[0][0] <= timestamp - 60:
            old_time, old_word = self.queue.popleft()

            self.counter[old_word] -= 1

            if self.counter[old_word] == 0:
                del self.counter[old_word]

    def top_k_words(self, k: int) -> list:
        return self.counter.most_common(k)


if __name__ == "__main__":
    # sentence = input("Enter the sentence: ")
    # result_dict = word_counter(sentence, 2)
    # print(result_dict)

    # print(word_counter("sample.txt"))
    # counter = Counter(read_words("sample.txt"))

    # print(counter)
    wc = SlidingWindowWordCounter()

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

    for t, word in stream:
        wc.add_word(t, word)

    print(wc.top_k_words(1))
