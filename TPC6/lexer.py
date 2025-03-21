import re
import sys
import traceback
from typing import Generator
from abc import abstractmethod
from dataclasses import dataclass

_DEBUG = False
def log(s):
    if _DEBUG: print(s)

#region ============== Lexer Utils ==============
class LexicalError(RuntimeError):
    def __init__(self, message):
        self.message = message

class StringStream:
    def __init__(self, s):
        self.s: str = s
        self.pos = 0

    def tell(self) -> int:
        return self.pos

    def peek(self) -> str:
        return self.s[self.pos]

    def peekNext(self) -> str:
        return self.s[self.pos + 1]

    def next(self) -> str:
        self.pos += 1
        return self.s[self.pos - 1]
    
    def eof(self):
        return self.pos >= len(self.s)

    def die(self, e):
        raise LexicalError(f"{e} (at {self.pos})")

    def proximaParagem(self, e):
        return LexicalError(f"{e} (at {self.pos})")

def readWhitespace(s):
    ch = s.peek()
    while not s.eof() and ch != "" and ch.isspace():
        s.next()
        ch = s.peek()

def readNoLFWhitespace(s):
    ch = s.peek()
    while not s.eof() and ch != "" and ch.isspace() and ch != "\n":
        s.next()
        ch = s.peek()

def readWord(s):
    buf = ""
    
    while not s.eof() and not s.peek().isspace():
        buf += s.next()

    return buf
#endregion ============== Lexer Utils ==============

@dataclass
class Token:
    value: str
    start: int = -1
    end: int = -1

    def __repr__(self):
        global _DEBUG
        if (_DEBUG): return f"{type(self).__name__}(value={self.value},start={self.start},end={self.end})"
        else: return f"{type(self).__name__}(value={self.value})"

    @classmethod
    def _name(cls):
        return cls.__name__

    def ist(self, kind: type) -> bool:
        return isinstance(self, kind)

    def markLocations(self, start: int, end: int):
        self.start = start
        self.end = end

        return self

    def markLocation(self, loc: int):
        self.start = loc
        self.end = loc

        return self

    @staticmethod
    @abstractmethod
    def read(s: StringStream) -> 'Token':
        raise NotImplementedError()
        pass

    @staticmethod
    def makePredicate(*chars):
        return lambda s: not s.eof() and s.peek() in chars

    PASS = lambda f: True
Token.acceptPred = Token.PASS

class OpToken(Token):
    def __init__(self):
        self.value = None

    def __repr__(self):
        global _DEBUG
        if (_DEBUG): return f"{type(self).__name__}(start={self.start},end={self.end})"
        else: return f"{type(self).__name__}"

    @classmethod
    def read(cls, s: StringStream):
        s.next()

        return cls().markLocation(s.tell() - 1)

class MinusOpToken(OpToken):
    acceptPred = Token.makePredicate("-")

class PlusOpToken(OpToken):
    acceptPred = Token.makePredicate("+")

class MultOpToken(OpToken):
    acceptPred = Token.makePredicate("*")

class DivOpToken(OpToken):
    acceptPred = Token.makePredicate("/")

class ParenOpenOpToken(OpToken):
    acceptPred = Token.makePredicate("(")

class ParenCloseOpToken(OpToken):
    acceptPred = Token.makePredicate(")")

class NumberToken(Token):
    acceptPred = lambda s: not s.eof() and s.peek().isdigit()

    @classmethod
    def read(cls, s: StringStream):
        buf = ""
        start = s.tell()
        while (not s.eof() and s.peek().isdigit()):
            buf += s.next()

        return cls(buf).markLocations(start, s.tell() - 1)

TOKEN_LIST = [
    MinusOpToken,
    PlusOpToken,
    MultOpToken,
    DivOpToken,
    ParenOpenOpToken,
    ParenCloseOpToken,
    NumberToken
]

def tokenize(input: str) -> Generator[Token, None, None]:
    s = StringStream(input)
    ch = s.peek()
    buf = ""

    _lastToken = None
    while (not s.eof()):
        readWhitespace(s)
        ch = s.peek()

        resolved = False
        for token in TOKEN_LIST:
            if token.acceptPred(s):
                readToken = token.read(s)
                if readToken is not None:
                    resolved = True
                    if (not getattr(token, "noread", False)): yield readToken
                    break
        
        if not resolved:
            if (_DEBUG):
                print(LexicalError(f"Unexpected token '{ch}' (at {s.tell()})"))
                return
            else:
                raise LexicalError(f"Unexpected token '{ch}' (at {s.tell()})")