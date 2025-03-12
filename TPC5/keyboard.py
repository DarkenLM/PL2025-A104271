from abc import abstractmethod
from enum import Enum
import termios
import sys
import tty
import os


class KeyboardInput:
    def __init__(self, value):
        self.value = value

class SpecialKeyboardInput(Enum):
    BACKSPACE = 1
    RETURN    = 2
    SPACE     = 3
    TAB       = 4
    ESC       = 5
    UP        = 6
    DOWN      = 7
    RIGHT     = 8
    LEFT      = 9

def getKey():
    """
        Captures and decods a single keycode from the STDIN.
        WARNING: This function depends on termios(3) to capture the keycode bytes directly, and on XTerm-specific 
          ANSI codes for the arrow functions.
        
        Furthermore, I can't be assed to fetch the terminfo data for wider system support, fuck that.
    """
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    try:
        while True:
            b = os.read(sys.stdin.fileno(), 3).decode()
            if b == "\x1b[A":   # Arrow Up
                return SpecialKeyboardInput(SpecialKeyboardInput.UP)
            elif b == "\x1b[B": # Arrow Down
                return SpecialKeyboardInput(SpecialKeyboardInput.DOWN)
            elif b == "\x1b[C": # Arrow Right
                return SpecialKeyboardInput(SpecialKeyboardInput.RIGHT)
            elif b == "\x1b[D": # Arrow Left
                return SpecialKeyboardInput(SpecialKeyboardInput.LEFT)
            elif len(b) == 3:
                # Assume that another ANSI code was recieved and is prefixed with \x1b[, capture the next byte.
                k = ord(b[2])
            else:
                k = ord(b)
                
            key_mapping = {
                127: SpecialKeyboardInput(SpecialKeyboardInput.BACKSPACE),
                10:  SpecialKeyboardInput(SpecialKeyboardInput.RETURN),
                32:  SpecialKeyboardInput(SpecialKeyboardInput.SPACE),
                9:   SpecialKeyboardInput(SpecialKeyboardInput.TAB),
                27:  SpecialKeyboardInput(SpecialKeyboardInput.ESC)
            }
            return key_mapping.get(k, KeyboardInput(chr(k)))
    finally:
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        except ValueError:
            pass # System exited.

class KeyboardInputHandler:
    def __init__(self):
        self.inputPrefix = "\x1b[33m>> \x1b[0m"
        self.inputPrefixLen = 3

    def printInputPrefix(self, flush=False):
        sys.stdout.write(self.inputPrefix)
        if (flush): sys.stdout.flush()

    def clear(self):
        print("\033[H\033[J", end="")

    def clearLine(self, len):
        sys.stdout.write("\r" + " " * (len) + "\r")

class JournaledKeyboardInputHandler(KeyboardInputHandler):
    def __init__(self):
        super().__init__()
        self.inputHistory = []

    def getInput(self):
        historyIndex = len(self.inputHistory)
        currentInput = ""
        cursorPos = 0
        savedInput = ""

        def _processRegularInput(key):
            nonlocal currentInput
            nonlocal cursorPos

            # Insert a character at the cursor position
            ch = key.value
            currentInput = currentInput[:cursorPos] + ch + currentInput[cursorPos:]
            cursorPos += 1

            # Rewrite the current line
            self.clearLine(len(currentInput) + self.inputPrefixLen)
            self.printInputPrefix()
            sys.stdout.write(f"{currentInput}")  
            
            # Move cursor
            cursorOffset = len(currentInput) - cursorPos
            if (cursorOffset > 0): sys.stdout.write(f"\x1b[{cursorOffset}D")

            sys.stdout.flush()

        while True:
            key = getKey()

            if (isinstance(key, SpecialKeyboardInput)):
                match key:
                    case SpecialKeyboardInput.BACKSPACE:
                        if cursorPos > 0:
                            currentInput = currentInput[:cursorPos - 1] + currentInput[cursorPos:]
                            cursorPos -= 1
                            sys.stdout.write("\b \b") # Erase character visually

                            # Rewrite the current current line (+ 1 to also clear the removed character)
                            self.clearLine(len(currentInput) + self.inputPrefixLen + 1)
                            self.printInputPrefix()
                            sys.stdout.write(f"{currentInput}")  

                            # Move cursor
                            cursorOffset = len(currentInput) - cursorPos
                            if (cursorOffset > 0): sys.stdout.write(f"\x1b[{cursorOffset}D")

                            sys.stdout.flush()
                    case SpecialKeyboardInput.RETURN:
                        print() # Move to a new line
                        if currentInput.strip(): 
                            self.inputHistory.append(currentInput)
                            # historyIndex += 1
                            # historyIndex = len(self.inputHistory)

                        currentInput += "\n"
                        return currentInput
                    case SpecialKeyboardInput.RIGHT:
                        if cursorPos < len(currentInput):
                            cursorPos += 1
                            sys.stdout.write("\033[C") # Move cursor right
                            sys.stdout.flush()
                    case SpecialKeyboardInput.LEFT:
                        if cursorPos > 0:
                            cursorPos -= 1
                            sys.stdout.write("\033[D") # Move cursor left
                            sys.stdout.flush()
                    case SpecialKeyboardInput.UP:
                        # If not at the bottom of the stack
                        if (historyIndex > 0):
                            # If at the top of the stack, save unfinished input before history scroll
                            if (historyIndex == len(self.inputHistory)): savedInput = currentInput
                            
                            lastInput = currentInput
                            
                            historyIndex -= 1
                            currentInput = self.inputHistory[historyIndex]
                            cursorPos = len(currentInput)

                            self.clearLine(len(lastInput) + 3)
                            self.printInputPrefix()
                            sys.stdout.write(currentInput)  # Show history
                            sys.stdout.flush()
                    case SpecialKeyboardInput.DOWN:
                        if (len(self.inputHistory) == 0): continue
                        lastInput = currentInput

                        # If not at the top of the stack, increment SP
                        if historyIndex < len(self.inputHistory) - 1:
                            historyIndex += 1
                            currentInput = self.inputHistory[historyIndex]
                        else:
                            # Prevent IOOB. Cap at the top of the stack
                            historyIndex = len(self.inputHistory)
                            currentInput = savedInput # Restore unfinished input

                        cursorPos = len(currentInput)

                        # Rewrite the current line
                        self.clearLine(len(lastInput) + self.inputPrefixLen)
                        self.printInputPrefix()
                        sys.stdout.write(currentInput)

                        sys.stdout.flush()
                    case SpecialKeyboardInput.SPACE:
                        _processRegularInput(KeyboardInput(" "))
                    case SpecialKeyboardInput.TAB:
                        _processRegularInput(KeyboardInput(" "))
            else:
                _processRegularInput(key)
