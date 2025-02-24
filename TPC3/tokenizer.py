from dataclasses import dataclass
from typing import Generator
from abc import abstractmethod
import re

# Constants
__DEBUG = False

#region ============== Helpers ==============
def log(s):
    if __DEBUG: print(s)

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
#endregion ============== Helpers ==============

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

@dataclass
class Token:
    value: str
    start: int = -1
    end: int = -1

    def ist(self, kind: type) -> bool:
        return isinstance(self, kind)

    def markLocation(self, start, end):
        self.start = start
        self.end = end

        return self

    @staticmethod
    @abstractmethod
    def read(f) -> 'Token':
        raise NotImplementedError()
        pass

    @staticmethod
    def makePredicate(*chars):
        return lambda f: peek(f) in chars

    PASS = lambda ch,_,__: True

class NewlineToken(Token):
    startPred = lambda f,_,__: peek(f) == "\n"

    def __init__(self, value):
        self.value = value

    def read(f):
        buf = ""

        start = f.tell()
        while (peek(f) == "\n"): f.read(1)
        end = f.tell()
        return NewlineToken(buf).markLocation(start, end)

class HeaderToken(Token):
    # startPred = lambda f: (f.tell() == 0 and peek(f) == "#") or peek(f, 2) == "\n#"
    # startPred = lambda f,_: peek(f) == "#"
    startPred = lambda f,_lastToken,_buf: (_lastToken is None or (_lastToken.ist(NewlineToken) and _buf is "")) and peek(f) == "#"

    def __init__(self, value):
        self.value = value

    def read(f):
        buf = ""

        start = f.tell()
        # if (peek(f) == "\n"): f.read(1)
        while (peek(f) == "#"):
            buf += peek(f)
            f.read(1)

        end = f.tell()
        return HeaderToken(buf).markLocation(start, end)

class ListToken(Token):
    # startPred = lambda f: (f.tell() == 0 and re.match(r"\d\.", peek(f, 2)) is not None) or (
    #     re.match(r"\n\d\.", peek(f, 3)) is not None
    # )
    startPred = lambda f,_lastToken,_: (_lastToken is None or _lastToken.ist(NewlineToken)) and (re.match(r"\d\.", peek(f, 2)) is not None)

    def __init__(self, value):
        self.value = value

    def read(f):
        # buf = f.read(2) if f.tell() == 0 else f.read(3)[1:]
        # return ListToken(f.read(3)[1:]).markLocation(f.tell() - 2, f.tell())

        buf = ""
        while (peek(f).isdigit()): buf += f.read(1)

        last = f.read(1)
        if (last != "."): return None
        buf += last

        return ListToken(buf).markLocation(f.tell() - len(buf), f.tell())

class TextAttribToken(Token):
    startPred = lambda f,_,__: peek(f) == "*"

    def __init__(self, value):
        self.value = value

    def read(f):
        buf = ""

        start = f.tell()
        for i in range(1, 4):
            if (peek(f) != "*"): break

            buf += "*"
            f.read(1)
        
        end = f.tell()
        return TextAttribToken(buf).markLocation(start, end)

class LinkAltStartToken(Token):
    startPred = lambda f,_,__: peek(f) == "["
    def read(f): return LinkAltStartToken(f.read(1)).markLocation(f.tell() - 1, f.tell() - 1)

class LinkAltEndToken(Token):
    startPred = lambda f,_,__: peek(f) == "]"
    def read(f): return LinkAltEndToken(f.read(1)).markLocation(f.tell() - 1, f.tell() - 1)

class LinkLinkStartToken(Token):
    startPred = lambda f,_,__: peek(f) == "("
    def read(f): return LinkLinkStartToken(f.read(1)).markLocation(f.tell() - 1, f.tell() - 1)

class LinkLinkEndToken(Token):
    startPred = lambda f,_,__: peek(f) == ")"
    def read(f): return LinkLinkEndToken(f.read(1)).markLocation(f.tell() - 1, f.tell() - 1)

class LinkAttribToken(Token):
    startPred = lambda f,_,__: peek(f) == "!"

    def __init__(self, value):
        self.value = value

    def read(f):
        buf = ""
        return LinkAttribToken(f.read(1)).markLocation(f.tell() - 1, f.tell() - 1)

class LiteralToken(Token):
    startPred = Token.PASS

    def __init__(self, value):
        self.value = value

TOKEN_LIST = [
    (NewlineToken,    0),
    (HeaderToken,     2),
    (ListToken,       0),
    (TextAttribToken, 2),
    (LinkAltStartToken,    2),
    (LinkAltEndToken,      2),
    (LinkLinkStartToken,   2),
    (LinkLinkEndToken,     2),
    (LinkAttribToken,      2)
]

def tokenize(f) -> Generator[Token, None, None]:
    ch = peek(f)
    buf = ""

    _lastToken = None
    while (ch != ""):
        resolved = False
        for token in TOKEN_LIST:
            if (token[1] == 0): 
                if token[0].startPred(f, _lastToken, buf): # Read with no whitespace consumption
                    if len(buf) > 0:
                        _lastToken = LiteralToken(buf).markLocation(f.tell() - len(buf), f.tell() - 1)
                        yield _lastToken
                        buf = ""

                    _lastToken = token[0].read(f)
                    yield _lastToken
                    ch = peek(f)
                    resolved = True
                    break
            elif (token[1] == 1 and token[0].startPred(f, _lastToken, buf)): # Read with whitespace consumption
                if len(buf) > 0:
                    _lastToken = LiteralToken(buf).markLocation(f.tell() - len(buf), f.tell() - 1)
                    yield _lastToken
                    buf = ""

                _lastToken = token[0].read(f)
                yield _lastToken
                readWhitespace(f)
                ch = peek(f)
                resolved = True
                break
            elif (token[1] == 2 and token[0].startPred(f, _lastToken, buf)): # Read with whitespace consumption, no line breaks
                if len(buf) > 0:
                    _lastToken = LiteralToken(buf).markLocation(f.tell() - len(buf), f.tell() - 1)
                    yield _lastToken
                    buf = ""

                _lastToken = token[0].read(f)
                yield _lastToken
                readNoLFWhitespace(f)
                ch = peek(f)
                resolved = True
                break

        if not resolved:
            if (ch == "\n"):
                if len(buf) > 0:
                    _lastToken = LiteralToken(buf).markLocation(f.tell() - len(buf), f.tell() - 1)
                    yield _lastToken
                    buf = ""

                # readWhitespace(f) # Do not use, because headers must be placed at the end of the line.
                f.read(1)
                # readNoLFWhitespace(f)
                _lastToken = NewlineToken.read(f)
                yield _lastToken
                ch = peek(f)
            else:
                buf += ch
                f.read(1)
                ch = peek(f)

    if (len(buf) > 0):
        yield LiteralToken(buf).markLocation(f.tell() - len(buf), f.tell() - 1)