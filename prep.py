def word_count(sentence: str) -> dict:

    if sentence is None or not isinstance(sentence, str):
        raise ValueError("Input must be a non-empty string.")
    
    words = sentence.lower().split()

    word_freq = {}

    for word in words:
        cleaned_word = word.strip('.,!?;:"()[]{}')
        word_freq[cleaned_word] = word_freq.get(cleaned_word, 0) + 1

    return word_freq
# print(word_count("Hello, world! Hello..."))

import re 

def word_count_regex(sentence:str) -> dict:
    if sentence is None or not isinstance(sentence, str):
        raise ValueError("Input must be a non-empty string.")
    
    words = re.findall(r"\b\w+\b", sentence.lower())

    word_freq = {}

    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1

    return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
# print(word_count_regex("Hello, world! Hello..."))

import heapq
def word_count_regex_sorted(sentence: str) -> dict:
    if sentence is None or not isinstance(sentence, str):
        raise ValueError("Input must be a non-empty string.")
    
    words = re.findall(r"\b\w+\b", sentence.lower())

    word_freq = {}

    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1

    return heapq.nlargest(1, word_freq.items(), key = lambda x: (x[1], x[0]))

# print(word_count_regex_sorted("Hello, world! Hello...world"))

from collections import Counter
def word_count_counter(sentence: str) -> dict:
    if sentence is None or not isinstance(sentence, str):
        raise ValueError("Input must be a non-empty string.")
    
    words = re.findall(r"\b\w+\b", sentence.lower())
    word_freq = Counter(words)

    return dict(word_freq)

# print(word_count_counter("Hello, world! Hello...world"))


def word_count_file(file_name = "sample.txt") -> dict:
    try:
        counter = Counter()
        with open(file_name, 'r') as file:
            for line in file:
                words = re.findall(r"\b\w+\b", line.lower())
                counter.update(words)
        return dict(counter)
    except FileNotFoundError:
        raise ValueError(f"File '{file_name}' not found.")
    except Exception as e:
        raise ValueError(f"An error occurred: {e}")
    
# print(word_count_file())

def lazy_file_word_count(file_name = "sample.txt") -> dict:
    try:
        with open(file_name, 'r') as file:
            for line in file:
                words = re.findall(r"\b\w+\b", line.lower())
                for word in words:
                    yield word
    except FileNotFoundError:
        raise ValueError(f"File '{file_name}' not found.")
    except Exception as e:
        raise ValueError(f"An error occurred: {e}")
    
# counter = Counter(lazy_file_word_count())
# print(dict(counter))

from collections import deque, Counter

class SlidingWindowWordCount:

    def __init__(self, window_size: int):
        self.window_size = window_size
        self.window = deque()
        self.word_freq = Counter()

    
    def add_word(self, timestamp: int, word: str):
        self.window.append((timestamp, word))
        self.word_freq[word] += 1

        if self.window and self.window[0][0] < timestamp - self.window_size:
            old_timestamp, old_word = self.window.popleft()
            self.word_freq[old_word] -= 1
            if self.word_freq[old_word] == 0:
                del self.word_freq[old_word]

        
    def top_k_words(self, k: int) -> list:
        return self.word_freq.most_common(k)
    
wc = SlidingWindowWordCount(window_size=5)
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

print(wc.top_k_words(2))