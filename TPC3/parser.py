from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Generator, Any
from util.peekIter import PeekableIterator
from tokenizer import (
    Token, HeaderToken, NewlineToken, LiteralToken, TextAttribToken, ListToken, 
    LinkAltStartToken, LinkAltEndToken, LinkLinkStartToken, LinkLinkEndToken,
    LinkAttribToken
)

__DEBUG = False

class SyntaxError(RuntimeError):
    pass

class TokenStream:
    def __init__(self, tokens):
        self.tokens = PeekableIterator(tokens)
        self._last = None

    def tell(self) -> int:
        cur = self.peek()
        if (cur is None): return -1
        return cur.start

    def peekBack(self) -> Token:
        return self.tokens.peekBack()

    def peek(self) -> Token:
        return self.tokens.peek()

    def peekNext(self) -> Token:
        return self.tokens.peek(1)

    def next(self) -> Token:
        self._last = next(self.tokens, None)
        return self._last
    
    def eof(self):
        return self.tokens.peek() is None

    def die(self, e):
        raise SyntaxError(f"{e} (at {self.peek().start})")

    def proximaParagem(self, e):
        print(SyntaxError(f"{e} (at {self.peek().start})"))

@dataclass
class Node:
    value: Any
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
    def read(s: TokenStream) -> 'Node':
        raise NotImplementedError()
        pass

    PASS = lambda ch: True

class NewlineNode(Node):
    startToken = lambda s: s.peek().ist(NewlineToken)

    def read(s):
        while (s.peek().ist(NewlineToken)): s.next()

        return None

class HeaderNode(Node):
    # startToken = lambda s: s.peek().ist(HeaderToken)
    startToken = lambda s: (s.peekBack() is None or s.peekBack().ist(NewlineToken)) and s.peek().ist(HeaderToken)
    
    def __init__(self, level, title):
        self.level = level
        self.value = title

    def read(s):
        if s.eof(): s.die("Reached end of file")
        start = s.peek().start
        level = len(s.next().value)

        # if not s.peek().ist(LiteralToken): s.die("Invalid token for header")
        # return HeaderNode(level, s.next().value.strip()).markLocation(start)

        # if not isTextNode(s): s.die("Expected text")
        # text = readTextNode(s)
        # if not s.peek().ist(LiteralToken): s.die("Expected text")
        # end = s.peek().end
        # text = s.next().value.strip() # Don't use readTextNode because it will consume the token that is on the next line.
        # if text is None: s.die("Expected text.")

        value = []
        if not isTextNode(s): s.die("Expected text")
        while isTextNode(s):
            text = readTextNode(s)
            value.append(text)
            end = text.end

        return HeaderNode(level, value).markLocation(start, end)

    def __repr__(self):
        return f"{type(self).__name__}(level={self.level},title={self.value},start={self.start},end={self.end})"

#region ============== Text Nodes ==============
class PlainTextNode(Node):
    startToken = lambda s: s.peek().ist(LiteralToken)
    
    def __init__(self, title):
        self.value = title

    def read(s):
        if s.eof(): s.die("Reached end of file")

        start = s.peek().start
        end = -1
        buf = ""
        while (not s.eof() and s.peek().ist(LiteralToken)):
            end = s.peek().end
            buf += s.next().value

        return PlainTextNode(buf.strip()).markLocation(start, end)

class ItalicTextNode(Node):
    startToken = lambda s: s.peek().ist(TextAttribToken) and s.peek().value == "*"
    
    def __init__(self, title):
        self.value = title

    def read(s):
        if s.eof(): s.die("Reached end of file")
        start = s.next().start

        buf = ""
        while (s.peek().ist(LiteralToken)):
            buf += s.next().value

        end = s.peek().end
        closingToken = s.next()
        if (not closingToken.ist(TextAttribToken) or not closingToken.value == "*"):
            s.die("Syntax error: Expected closing italic marker at position")

        return ItalicTextNode(buf.strip()).markLocation(start, end)

class BoldTextNode(Node):
    startToken = lambda s: s.peek().ist(TextAttribToken) and s.peek().value == "**"
    
    def __init__(self, title):
        self.value = title

    def read(s):
        if s.eof(): s.die("Reached end of file")
        start = s.next().start

        buf = ""
        while (s.peek().ist(LiteralToken)):
            buf += s.next().value

        end = s.peek().end
        closingToken = s.next()
        if (not closingToken.ist(TextAttribToken) or not closingToken.value == "**"):
            s.die("Syntax error: Expected closing bold marker at position")

        return BoldTextNode(buf.strip()).markLocation(start, end)

class ItalicBoldTextNode(Node):
    startToken = lambda s: s.peek().ist(TextAttribToken) and s.peek().value == "***"
    
    def __init__(self, title):
        self.value = title

    def read(s):
        if s.eof(): s.die("Reached end of file")
        start = s.next().start

        buf = ""
        while (s.peek().ist(LiteralToken)):
            buf += s.next().value

        end = s.peek().end
        closingToken = s.next()
        if (not closingToken.ist(TextAttribToken) or not closingToken.value == "***"):
            s.die("Syntax error: Expected closing bold marker at position")

        return ItalicBoldTextNode(buf.strip()).markLocation(start, end)

class LinkNode(Node):
    startToken = lambda s: s.peek().ist(LinkAltStartToken)
    
    def __init__(self, alt, href):
        self.alt = alt
        self.href = href

    def read(s):
        if s.eof(): s.die("Reached end of file")
        start = s.next().start

        alt = []
        while (isTextNode(s)):
            text = readTextNode(s)
            if text is None: s.die("Syntax error: Invalid link alt text.")
            alt.append(text)

        if (not s.next().ist(LinkAltEndToken)):
            s.die("Syntax Error: Expected Link alt end marker at position")
        if (not s.next().ist(LinkLinkStartToken)):
            s.die("Syntax Error: Expected Link start marker at position")

        if (not s.peek().ist(LiteralToken)): s.die("Syntax Error: Invalid href")
        href = s.next().value

        end = s.peek().end
        if (not s.next().ist(LinkLinkEndToken)):
            s.die("Syntax Error: Expected Link href end marker at position")

        return LinkNode(alt, href).markLocation(start, end)

    def __repr__(self):
        return f"{type(self).__name__}(alt={self.alt},href={self.href}),start={self.start},end={self.end}"

class ImgNode(LinkNode):
    startToken = lambda s: s.peek().ist(LinkAttribToken)
    
    # def __init__(self, alt, href):
    #     self.alt = alt
    #     self.href = href

    def read(s):
        if s.eof(): s.die("Reached end of file")
        start = s.next().start

        if (not LinkNode.startToken(s)): s.die("Expected link")
        link = LinkNode.read(s)

        return ImgNode(link.alt, link.href).markLocation(start, link.end)

    # def __repr__(self):
    #     return f"{type(self).__name__}(alt={self.alt},href={self.href}),start={self.start},end={self.end}"


class ParagraphNode(Node):
    # startToken = lambda s: s.peek().ist(LiteralToken)
    startToken = lambda s: isParagraphNode(s)

    def __init__(self, nodes):
        self.value = nodes

    def read(s):
        start = s.peek().start
        end = -1

        # value = []
        # while (not s.eof() and isTextNode(s)):
        #     text = readTextNode(s)

        value = []
        while (not s.eof() and isParagraphNode(s)):
            text = readParagraphNode(s)
            if text is None: break

            value.append(text)
            end = text.end

        return ParagraphNode(value).markLocation(start, end)


# TEXT_NODES = [PlainTextNode, ItalicBoldTextNode, BoldTextNode, ItalicTextNode, ImgNode, LinkNode]
TEXT_NODES = [PlainTextNode, ItalicBoldTextNode, BoldTextNode, ItalicTextNode]
PARAGRAPH_NODES = [PlainTextNode, ItalicBoldTextNode, BoldTextNode, ItalicTextNode, ImgNode, LinkNode]

def isTextNode(s):
    for node in TEXT_NODES:
        if (node.startToken(s)): return True
    
    return False

def readTextNode(s):
    for node in TEXT_NODES:
        if (node.startToken(s)):
            return node.read(s)

    return None

def isParagraphNode(s):
    for node in PARAGRAPH_NODES:
        if (node.startToken(s)): return True
    
    return False

def readParagraphNode(s):
    for node in PARAGRAPH_NODES:
        if (node.startToken(s)):
            return node.read(s)

    return None
#endregion ============== Text Nodes ==============

#region ============== List Nodes ==============
class ListElementNode(Node):
    startToken = lambda s: s.peek().ist(ListToken)
    
    def __init__(self, num, title):
        self.num = num
        self.value = title

    def read(s):
        if s.eof(): s.die("Reached end of file")

        start = s.peek().start
        end = -1
        num = int(s.next().value.replace(".", ""))

        value = []
        while (isTextNode(s)):
            text = readTextNode(s)
            if text is None: s.die("Syntax error: List element index must be followed by text.")
            value.append(text)
            end = text.end

        return ListElementNode(num, value).markLocation(start, end)

    def __repr__(self):
        return f"{type(self).__name__}(num={self.num},value={self.value}),start={self.start},end={self.end}"

class ListNode(Node):
    startToken = ListElementNode.startToken

    def __init__(self, elems):
        self.value = elems
        self.len = len(elems)

    def read(s):
        if s.eof(): s.die("Reached end of file")

        start = s.peek().start
        elems = []
        while (ListElementNode.startToken(s)):
            elems.append(ListElementNode.read(s))
            if (s.peek().ist(NewlineToken)): s.next()

        return ListNode(elems).markLocation(start, s.peek().end)
#endregion ============== List Nodes ==============

NODE_LIST = [
    (NewlineNode,         0),
    (HeaderNode,          0),
    # (ItalicTextNode,      0),
    # (BoldTextNode,        0),
    # (ItalicBoldTextNode, 0),
    # (PlainTextNode,       0),
    (ParagraphNode,       0),
    (ListNode,            0),
    # (LinkNode,            0),
]

def parse(tokens: Iterable[Token]) -> Generator[Node, None, None]:
    s = TokenStream(tokens)
    while (not s.eof()):
        processed = False
        for node in NODE_LIST:
            if node[1] == 0:
                if node[0].startToken(s):
                    processed = True
                    rnode = node[0].read(s)
                    if rnode is not None: yield rnode
                    break
            else:
                raise RuntimeError(f"Invalid node mode for {type(node[0]).__name__}: {node[1]}")
        
        if not processed:
            if __DEBUG:
                s.proximaParagem(f"Syntax error: Unexpected token at position: {type(s.peek()).__name__}")
                return None
            else: 
                s.die(f"Syntax error: Unexpected token at position: {type(s.peek()).__name__}")
