from enum import Enum
from abc import abstractmethod
from typing import Generator, Any
from dataclasses import dataclass
from collections.abc import Iterable
from util.peekIter import PeekableIterator
from lexer import (
    Token, TOKEN_LIST,
    OpToken,
    MinusOpToken, PlusOpToken, MultOpToken, DivOpToken, ParenOpenOpToken, ParenCloseOpToken, NumberToken
)

#region ============== Constants ==============
_DEBUG = False

# Expression
OPP_NUD = 0
"""Index for Null Denotation for Pratt's Algorithm. See ExpressionNode.OPERATOR_PRECEDENCE."""
OPP_LED = 1
"""Index for Left Denotation for Pratt's Algorithm. See ExpressionNode.OPERATOR_PRECEDENCE."""
OPP_RID = 2
"""Index for Right Denotation for Pratt's Algorithm. See ExpressionNode.OPERATOR_PRECEDENCE."""
#endregion ============== Constants ==============

def log(s):
    if _DEBUG: print(s)

#region ============== Parser Utils ==============
class SyntaxError(RuntimeError):
    def __init__(self, message):
        self.message = message

class TokenStream:
    def __init__(self, tokens):
        self.tokens = PeekableIterator(tokens)
        self._last = None

    def tell(self) -> int:
        cur = self.peek()
        if (cur is None): return -1
        return cur.start

    def peek(self) -> Token:
        return self.tokens.peek()

    def peekNext(self) -> Token:
        return self.tokens.peek(1)

    def next(self) -> Token:
        _last = next(self.tokens, None)
        if (_last != None): self._last = _last
        return _last
    
    def eof(self):
        return self.tokens.peek() is None

    def die(self, e):
        raise SyntaxError(f"{e} (at {self._last.start if self.eof() else self.peek().start})")

    def proximaParagem(self, e):
        print(SyntaxError(f"{e} (at {self._last.start if self.eof() else self.peek().start})"))
#endregion ============== Parser Utils ==============

@dataclass
class Node:
    value: Any
    start: int = -1
    end: int = -1

    def __repr__(self):
        global _DEBUG
        if (_DEBUG): return f"{type(self).__name__}(value={self.value},start={self.start},end={self.end})"
        else: return f"{type(self).__name__}({self.value})"

    def ist(self, kind: type) -> bool:
        return isinstance(self, kind)

    def markLocation(self, pos):
        self.start = pos
        self.end = pos

        return self

    def markLocations(self, start, end):
        self.start = start
        self.end = end

        return self

    @staticmethod
    @abstractmethod
    def read(s: TokenStream) -> 'Node':
        raise NotImplementedError()
        pass

    @staticmethod
    def makePredicate(*tokens):
        return lambda s: not s.eof() and any(map(s.peek().ist, tokens))

    PASS = lambda ch: True
Node.acceptPred = Node.PASS

class NumberNode(Node):
    acceptPred = Node.makePredicate(NumberToken)

    @classmethod
    def read(cls, s: TokenStream):
        return cls(int(s.next().value))
        
class Operator(Enum):
    MINUS = 1,
    PLUS  = 2,
    MULT  = 3,
    DIV   = 4

    @classmethod
    def fromToken(cls, t: Token):
        if (not t.ist(OpToken)): raise TypeError(f"Not an operator (at {t.start})")

        if (t.ist(MinusOpToken)): return cls.MINUS
        elif (t.ist(PlusOpToken)): return cls.PLUS
        elif (t.ist(MultOpToken)): return cls.MULT
        elif (t.ist(DivOpToken)): return cls.DIV
        else: raise TypeError(f"Not a valid operator (at {t.start})")

class ExpressionNode(Node):
    acceptPred = Node.makePredicate(*TOKEN_LIST)

    def __init__(self, lhs, op = None, rhs = None, partial = True):
        self.partial = partial
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    def __repr__(self, level=1):
        global _DEBUG

        ret  = f"{type(self).__name__}"
        if (self.partial): ret += "{PARTIAL}"
        ret += "(\n"

        if (self.lhs != None):
            ret += " " * (level * 2) + f"- {self.lhs.__repr__(level=level + 1) if self.lhs.ist(ExpressionNode) else self.lhs}\n"
        else:
            # ret += " " * (level * 2) + "- None\n"
            pass
        ret += " " * (level * 2) + f"- {self.op}\n"
        ret += " " * (level * 2) + f"- {self.rhs.__repr__(level=level + 1) if self.rhs.ist(ExpressionNode) else self.rhs}\n"

        if (_DEBUG): 
            ret += " " * (level * 2) + f"- START: {self.start}\n"
            ret += " " * (level * 2) + f"- END: {self.end}\n"
        ret += " " * ((level - 1) * 2) + f")"

        return ret

    @classmethod
    def _process(cls, s: TokenStream, mbp: int):
        tok = s.next()

        # Process Left-Hand Side
        lhs = None
        if (tok.ist(NumberToken)):
            lhs = NumberNode(int(tok.value)).markLocation(s.tell() - 1)
        else:
            if (tok.ist(ParenOpenOpToken)):
                lhs = cls._process(s, 0)
                closeTok = s.next()
                if (closeTok == None or not closeTok.ist(ParenCloseOpToken)): s.die(f"Syntax error: Non-closed parenthesized expression.")
            else:
                prec = cls.OPERATOR_PRECEDENCE[tok._name()]
                if (prec == None or prec[OPP_NUD] == -1): s.die(f"Syntax error: Unknown or invalid operator.")

                rhs = cls._process(s, prec[OPP_NUD])
                top = Operator.fromToken(tok)
                lhs = ExpressionNode(None, top, rhs, True)

        # Process Operator and Right-Hand Side
        op = None
        while (not s.eof() and (op := s.peek()).ist(OpToken)):
            opprec = cls.OPERATOR_PRECEDENCE[op._name()]
            if (opprec == None): s.die(f"Syntax error: Unknown operator.")
            if (opprec[OPP_LED] < mbp): break
            s.next()

            # Process Right-Hand Side
            rhs = cls._process(s, opprec[OPP_RID]) # Use LED if not working
            top = Operator.fromToken(op)
            lhs = cls(lhs, top, rhs, False)

        # return cls(lhs, op, rhs, False)
        return lhs


    @classmethod
    def read(cls, s: TokenStream):
        return cls._process(s, 0)
# <op>: (<nud>, <led>, <red>)
ExpressionNode.OPERATOR_PRECEDENCE = {
    MinusOpToken._name():      (+5, +1, +2),
    PlusOpToken._name():       (-1, +1, +2),
    MultOpToken._name():       (-1, +3, +4),
    DivOpToken._name():        (-1, +3, +4),
    ParenOpenOpToken._name():  (-1, -1, -1),
    ParenCloseOpToken._name(): (-1, -1, -1)
}

NODE_LIST = [
    ExpressionNode
]

def parse(tokens: Iterable[Token]) -> Generator[Node, None, None]:
    s = TokenStream(tokens)
    while (not s.eof()):
        processed = False
        for node in NODE_LIST:
            if node.acceptPred(s):
                rnode = node.read(s)
                if rnode is not None: 
                    processed = True
                    yield rnode
                break
        
        if not processed:
            if __DEBUG:
                s.proximaParagem(f"Syntax error: Unexpected token at position: {type(s.peek()).__name__}")
                return None
            else: 
                s.die(f"Syntax error: Unexpected token at position: {type(s.peek()).__name__}")
