import re
import sys
from typing import Generator
from abc import abstractmethod
from dataclasses import dataclass

# Constants
_DEBUG = False
INPUT_FILE = "test.dbp"

#region ============== Helpers ==============
def log(s):
    if _DEBUG: print(s)

__FILE_POS_STACK = {}

def push(f):
    if (not f in __FILE_POS_STACK): __FILE_POS_STACK[f] = []
    __FILE_POS_STACK[f].append(f.tell())

def pop(f):
    if (not f in __FILE_POS_STACK): return
    f.seek(__FILE_POS_STACK[f].pop())

def drop(f):
    if (not f in __FILE_POS_STACK): return
    __FILE_POS_STACK[f].pop()


def peek(f, n = 1):
    pos = f.tell()
    ch = f.read(n)
    f.seek(pos)
    return ch

def getAt(f, n, pos):
    cpos = f.tell()
    f.seek(pos)
    ch = f.read(n)
    f.seek(cpos)
    return ch

def readWhitespace(f):
    ch = peek(f)
    while ch != "" and ch.isspace():
        f.read(1)
        ch = peek(f)

def readNoLFWhitespace(f):
    ch = peek(f)
    while ch != "" and ch.isspace() and ch != "\n":
        f.read(1)
        ch = peek(f)
#endregion ============== Helpers ==============

class LexicalError(RuntimeError):
    pass

@dataclass
class Token:
    value: str
    start: int = -1
    end: int = -1

    def __repr__(self):
        global _DEBUG
        if (_DEBUG): return f"{type(self).__name__}(value={self.value},start={self.start},end={self.end})"
        else: return f"{type(self).__name__}(value={self.value})"

    def ist(self, kind: type) -> bool:
        return isinstance(self, kind)

    def markLocations(self, start, end):
        self.start = start
        self.end = end

        return self

    def markLocation(self, loc: int):
        self.start = loc
        self.end = loc

        return self

    @staticmethod
    @abstractmethod
    def read(f) -> 'Token':
        raise NotImplementedError()
        pass

    @staticmethod
    def makePredicate(*chars):
        return lambda f: peek(f) in chars

    PASS = lambda f: True
Token.acceptPred = Token.PASS

class MonoToken(Token):
    acceptPred = Token.makePredicate("\n")

    def __init__(self):
        self.value = None

    def __repr__(self):
        global _DEBUG
        if (_DEBUG): return f"{type(self).__name__}(start={self.start},end={self.end})"
        else: return f"{type(self).__name__}"

    @classmethod
    def read(cls, f):
        f.read(1)

        return cls().markLocation(f.tell() - 1)

class NewlineToken(MonoToken):
    acceptPred = Token.makePredicate("\n")

    def __init__(self):
        self.value = None

    def read(f):
        start = f.tell()
        while peek(f) == "\n": f.read(1)

        return NewlineToken().markLocations(start, f.tell() - 1)

class CommentStartToken(MonoToken):
    acceptPred = Token.makePredicate("#")
    noread = True

    def read(f):
        ch = f.read(1)
        while ch != "" and not NewlineToken.acceptPred(f):
            ch = f.read(1)

        readWhitespace(f)

        return None


class NamespaceSeparatorToken(MonoToken):
    acceptPred = Token.makePredicate(":")

class BlockStartToken(MonoToken):
    acceptPred = Token.makePredicate("{")

class BlockEndToken(MonoToken):
    acceptPred = Token.makePredicate("}")

class StatementEndToken(MonoToken):
    acceptPred = Token.makePredicate(".")

class ModifierToken(Token):
    acceptPred = Token.makePredicate("@")

    def read(f):
        start = f.tell()
        f.read(1)
        buf = ""
        while (re.match(r"[a-zA-Z]", peek(f))):
            buf += f.read(1)
        if len(buf) > 0 : f.read(1)
        else:
            raise LexicalError(f"Unexpected identifier: {peek(f)}")

        return ModifierToken(buf).markLocations(start, f.tell() - 1)

class StringLiteralToken(Token):
    acceptPred = Token.makePredicate("\"")

    def read(f):
        start = f.tell()
        f.read(1)
        buf = ""
        while (not StringLiteralToken.acceptPred(f)):
            buf += f.read(1)
        f.read(1)

        return StringLiteralToken(buf).markLocations(start, f.tell() - 1)

class NumberLiteralToken(Token):
    acceptPred = lambda f: re.match(r"\d", peek(f))

    def read(f):
        start = f.tell()
        buf = ""
        while (NumberLiteralToken.acceptPred(f)):
            buf += f.read(1)
        
        value = int(buf)

        return NumberLiteralToken(value).markLocations(start, f.tell() - 1)

class VariableToken(Token):
    acceptPred = Token.makePredicate("?")

    def read(f):
        start = f.tell()
        f.read(1)
        buf = ""
        ch = peek(f)
        while (re.match(r"[a-zA-Z]", peek(f))):
            buf += f.read(1)

        return VariableToken(buf).markLocations(start, f.tell() - 1)

KEYWORDS = sorted(["SELECT", "WHERE", "LIMIT"], key=len)
_KW_MAXLEN = len(KEYWORDS[-1])
_KW_INITIALS = set(map(lambda kw: kw[0], KEYWORDS))
class KeywordToken(Token):
    acceptPred = lambda f: peek(f).upper() in _KW_INITIALS

    def read(f):
        push(f)
        buf = ""
        start = f.tell()
        while len(buf) < _KW_MAXLEN and not buf.upper() in KEYWORDS:
            buf += f.read(1)
        
        if (buf.upper() in KEYWORDS):
            drop(f)
            return KeywordToken(buf.upper()).markLocations(start, f.tell() - 1)
        else:
            pop(f)
            return None

class IdentifierToken(Token):
    acceptPred = lambda f: re.match(r"[a-zA-Z0-9]", peek(f))

    def read(f):
        buf = ""
        start= f.tell()
        while re.match(r"[a-zA-Z0-9]", peek(f)): 
            buf += f.read(1)

        return IdentifierToken(buf).markLocations(start, f.tell() - 1)

TOKEN_LIST = [
    CommentStartToken, 
    KeywordToken,
    NamespaceSeparatorToken,
    BlockStartToken,
    BlockEndToken,
    StatementEndToken,
    ModifierToken,
    StringLiteralToken,
    NumberLiteralToken,
    VariableToken,
    IdentifierToken,
    NewlineToken
]

def tokenize(f) -> Generator[Token, None, None]:
    ch = peek(f)
    buf = ""

    _lastToken = None
    while (ch != ""):
        readNoLFWhitespace(f)
        ch = peek(f)

        resolved = False
        for token in TOKEN_LIST:
            if token.acceptPred(f):
                readToken = token.read(f)
                if readToken is not None:
                    resolved = True
                    if (not getattr(token, "noread", False)): yield readToken

                    readNoLFWhitespace(f)
                    ch = peek(f)
                    break
        
        if not resolved:
            if (_DEBUG):
                print(LexicalError(f"Unexpected token '{ch}' (at {f.tell()})"))
                return
            else:
                raise LexicalError(f"Unexpected token '{ch}' (at {f.tell()})")

if __name__ == "__main__":
    filename = INPUT_FILE
    if (len(sys.argv) > 1): filename = sys.argv[1]

    with open(filename, "rt") as file:
        tokens = list(tokenize(file))
        print(f"TOKENS: {tokens}")
