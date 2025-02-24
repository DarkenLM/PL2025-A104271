from abc import abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from util.peekIter import PeekableIterator
from parser import (
    Node, HeaderNode, ItalicTextNode, BoldTextNode, ItalicBoldTextNode, 
    PlainTextNode, ParagraphNode, ListNode, LinkNode, ImgNode,
    # TEXT_NODES
)

__DEBUG = False

class SemanticError(RuntimeError):
    pass

class NodeStream:
    def __init__(self, nodes):
        self.nodes = PeekableIterator(nodes)
        self._last = None

    def tell(self) -> int:
        cur = self.peek()
        if (cur is None): return -1
        return cur.start

    def peek(self) -> Node:
        return self.nodes.peek()

    def peekNext(self) -> Node:
        return self.nodes.peek(1)

    def next(self) -> Node:
        self._last = next(self.nodes, None)
        return self._last
    
    def eof(self):
        return self.nodes.peek() is None

    def die(self, e):
        raise SemanticError(f"{e} (at {self.peek().start})")

    def proximaParagem(self, e):
        print(SemanticError(f"{e} (at {self.peek().start})"))

def isTextNode(node):
    TEXT_NODES = [PlainTextNode, ItalicTextNode, BoldTextNode, ItalicBoldTextNode, ParagraphNode]
    for tn in TEXT_NODES:
        if (node.ist(tn)): return True

    return False

def generateTextList(node):
    out = ""
    it = node.value if isinstance(node, Node) else node

    # for component in it:
    for i in range(0, len(it)):
        component = it[i]
        out += generateText(component)
        if (i < len(it) - 1): out += " "
    
    return out

def generateText(node):
    out = ""

    if (node.ist(PlainTextNode)): out += f"{node.value}"
    elif (node.ist(ItalicTextNode)): out += f"<i>{node.value}</i>"
    elif (node.ist(BoldTextNode)): out += f"<strong>{node.value}</strong>"
    elif (node.ist(ItalicBoldTextNode)): out += f"<i><strong>{node.value}</strong></i>"
    # MUST be before LinkNode, because it inherits from it
    elif (node.ist(ImgNode)): out += f"<img href='{node.href}' alt='{generateTextList(node.alt)}'></img>"
    elif (node.ist(LinkNode)): out += f"<a href='{node.href}'>{generateTextList(node.alt)}</a>"
    elif (node.ist(ParagraphNode)):
        out += "<p>"
        # for component in node.value:
        #     out += generateText(component)
        #     out += " "
        out += generateTextList(node)
        out += "</p>\n"
    
    return out

def generateList(node):
    out = "<ol>\n"
    for elem in node.value:
        out += "    <li>"
        # out += "        " + generateText(elem.value)
        for enode in elem.value:
            out += generateText(enode)
        out += "</li>\n"
    
    out += "</ol>\n"
    return out


def generate(nodes: Iterable[Node]) -> str:
    s = NodeStream(nodes)
    out = ""

    while (not s.eof()):
        node = s.next()
        if (node.ist(HeaderNode)):
            out += f"<h{node.level}>{generateTextList(node)}</h{node.level}>\n"
        elif isTextNode(node):
            out += generateText(node)
        elif (node.ist(ListNode)):
            out += generateList(node)
        # elif (node.ist(LinkNode)):
        #     out += f"<a href='{node.href}'>{generateText(node.alt)}</a>"
        else:
            if __DEBUG:
                s.proximaParagem(f"Unexpected token")
                return out # Return the current buffer, to see what was generated up to this point
            else: 
                s.die(f"Unexpected token")

    return out