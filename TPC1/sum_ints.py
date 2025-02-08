import sys

# Constants
__DEBUG = False

# State index aliases
ACTIVE = 1
ACC = 0

#region ============== Helpers ==============
def log(s):
    if __DEBUG: print(s)
#endregion ============== Helpers ==============

def sum_ints(l: str, state):
    i = 0
    while i < len(l):
        c = l[i]
        log(f"Evaluating: '{c}' @ {i}")
        log(f"- Ctrl Candidates: {l[i : i + 2].lower()} {l[i : i + 3].lower()}")
        log(f"- Number candidate: {c.isdigit()}")

        if l[i : i + 2].lower() == "on":
            log("Enabled sum")
            state[ACTIVE] = True
            i = i + 2
        elif l[i : i + 3].lower() == "off":
            log("Disabled sum")
            state[ACTIVE] = False
            i = i + 3
        elif c == '=':
            log(f"- Current state: {state[ACC]} {state[ACTIVE]}")
            print(f"{state[ACC]}")
        elif not state[ACTIVE]: 
            pass
        elif c.isdigit():
            log("- Parsing number")
            _num = c
            j = i + 1

            log(f"-- Current num: {_num} {j}")
            while l[j].isdigit():
                _num += l[j]
                j = j + 1
                log(f"-- Current num: {_num} {j}")

            num = int(_num)
            state[ACC] = state[ACC] + num
            i = j

        i = i + 1
    return

def init():
    state = [0, True]
    for line in sys.stdin:
        sum_ints(line, state)

init()