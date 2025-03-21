from abc import abstractmethod
from typing import Generator, Any
from collections.abc import Iterable
from util.peekIter import PeekableIterator
from parser import (
    Node, Operator,
    ExpressionNode, NumberNode
)

_DEBUG = False
def log(*s):
    if _DEBUG: print(*s)

#region ============== Parser Utils ==============
class ExecutionError(RuntimeError):
    def __init__(self, message):
        self.message = message

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
        raise ExecutionError(f"{e} (at {self.peek().start})")

    def proximaParagem(self, e):
        print(ExecutionError(f"{e} (at {self.peek().start})"))
#endregion ============== Parser Utils ==============

class ExecutionTarget:
    @staticmethod
    @abstractmethod
    def execute(s: NodeStream):
        raise NotImplementedError()
        pass

    @staticmethod
    def makePredicate(*nodes):
        return lambda s: not s.eof() and any(map(s.peek().ist, nodes))

    PASS = lambda ch: True
ExecutionTarget.acceptPred = ExecutionTarget.PASS

class ExpressionET(ExecutionTarget):
    acceptPred = ExecutionTarget.makePredicate(ExpressionNode)

    @classmethod
    def _handleSide(cls, n: Node):
        nv = None

        if (n == None): return 0
        if (n.ist(NumberNode)): nv = n.value
        elif (n.ist(ExpressionNode)): 
            if (n.partial):
                nv = cls._executeUnary(n)
            else:
                nv = cls._execute(n)
        else: s.die(f"Execution error: Expected number or expression")

        return nv

    @classmethod
    def _executeUnary(cls, e: ExpressionNode):
        if (e.lhs == None): # Prefix Operation
            rhs = cls._handleSide(e.rhs)

            match (e.op):
                case Operator.MINUS:
                    return -rhs

        return None

    @classmethod
    def _execute(cls, e: ExpressionNode):
        lhs = cls._handleSide(e.lhs)
        rhs = cls._handleSide(e.rhs)

        log("LHS:", lhs)
        log("OP:", e.op)
        log("RHS:", rhs)

        match (e.op): # Binary Operation
            case Operator.MINUS:
                return lhs - rhs
            case Operator.PLUS:
                return lhs + rhs
            case Operator.MULT:
                return lhs * rhs
            case Operator.DIV:
                return lhs / rhs

        return None

    @classmethod
    def execute(cls, s: NodeStream):
        return cls._execute(s.next())

EXECUTION_TARGET_LIST = [
    ExpressionET
]

def execute(nodes: Iterable[Node]) -> Generator[Any, None, None]:
    s = NodeStream(nodes)
    while (not s.eof()):
        processed = False
        for et in EXECUTION_TARGET_LIST:
            if et.acceptPred(s):
                ret = et.execute(s)
                if ret is not None: 
                    processed = True
                    yield ret
                break
        
        if not processed:
            if _DEBUG:
                s.proximaParagem(f"Execution error: Unexpected node at position: {type(s.peek()).__name__}")
                return None
            else: 
                s.die(f"Execution error: Unexpected node at position: {type(s.peek()).__name__}")
