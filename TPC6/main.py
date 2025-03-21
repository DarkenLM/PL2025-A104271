from lexer import tokenize, StringStream
from interpreter import execute
from parser import parse

def init():
    while True:
        exp = input("> ").strip()
        if (exp in ["exit", "e"]): exit(0)

        out = list(execute(parse(tokenize(exp))))
        print(f"= {out[0]}")

init()

