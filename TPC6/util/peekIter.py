from collections import deque

class PeekableIterator:
    def __init__(self, iterable, histsize=5):
        self.iterator = iter(iterable)
        self.peeked = deque()
        self.history = deque(maxlen=histsize)

    def __iter__(self):
        return self

    def __next__(self):
        # if self.peeked:
        #     return self.peeked.popleft()
        # return next(self.iterator)
        value = None
        if self.peeked: value = self.peeked.popleft()
        else: value = next(self.iterator)

        self.history.append(value)
        return value

    def peek(self, ahead=0):
        while len(self.peeked) <= ahead:
            self.peeked.append(next(self.iterator, None))
        return self.peeked[ahead]

    def peekBack(self, behind=1):
        if behind <= 0 or behind > len(self.history): return None
        return self.history[-behind]