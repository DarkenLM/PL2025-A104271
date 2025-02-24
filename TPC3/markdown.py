import sys
import re
import os
from tokenizer import tokenize
from parser import parse
from codegen import generate

# Constants
__DEBUG = False

INPUT_FILE = "test.md"

#region ============== Helpers ==============
def log(s):
    if __DEBUG: print(s)
#endregion ============== Helpers ==============

def processMarkdownFile(filePath):
    with open(filePath, "rt") as file:
        # tokens = list(tokenize(file))
        # print(f"TOKENS: {tokens}\n\n\n")

        # ast = list(parse(tokens))
        # print(f"AST: {ast}")

        # out = generate(ast)
        # print(f"============== BEGIN OUTPUT ==============\n{out}\n=============== END OUTPUT ===============")

        out = generate(parse(tokenize(file)))
        
        nameMatch = re.match(r"(.+)\.md", os.path.basename(filePath))
        name = "output"
        if (nameMatch is not None): name = nameMatch.group(1)

        with open(f"{name}.html", "wt") as outfile:
            outfile.write(out)

def init():
    file = INPUT_FILE
    if (len(sys.argv) > 1): file = sys.argv[1]
    processMarkdownFile(file)

init()
