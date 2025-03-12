from abc import abstractmethod
from keyboard import JournaledKeyboardInputHandler
import traceback
import datetime
import signal
import json
import sys
import re

_DEBUG = False
_SYSTEM = "___SYSTEM_IDENTIFIER___"
_SYM_HIDE = "___COMMAND_HIDE___"
_MAINTENANCE_CODE = "admin123"

def log(s):
    if _DEBUG: print(s)

#region ============== Lexer Utils ==============
class LexicalError(RuntimeError):
    def __init__(self, message):
        self.message = message

class StringStream:
    def __init__(self, s):
        self.s: str = s
        self.pos = 0

    def tell(self) -> int:
        return self.pos

    def peek(self) -> str:
        return self.s[self.pos]

    def peekNext(self) -> str:
        return self.s[self.pos + 1]

    def next(self) -> str:
        self.pos += 1
        return self.s[self.pos - 1]
    
    def eof(self):
        return self.pos >= len(self.s) - 1

    def die(self, e):
        raise LexicalError(f"{e} (at {self.pos})")

    def proximaParagem(self, e):
        return LexicalError(f"{e} (at {self.pos})")

def readWhitespace(s):
    ch = s.peek()
    while not s.eof() and ch != "" and ch.isspace():
        s.next()
        ch = s.peek()

def readNoLFWhitespace(s):
    ch = s.peek()
    while not s.eof() and ch != "" and ch.isspace() and ch != "\n":
        s.next()
        ch = s.peek()

def readWord(s):
    buf = ""
    
    while not s.eof() and not s.peek().isspace():
        buf += s.next()

    return buf
#endregion ============== Lexer Utils ==============

class ExecutionError(RuntimeError):
    def __init__(self, message, critical = False):
        self.message = message
        self.critical = critical

        super().__init__(message)

    def isCritical(self):
        return self.critical == True

class MachineState:
    MOEDAS = [200, 100, 50, 20, 10, 5, 1]

    def __init__(self, filename):
        self.filename = filename
        # self.file = None
        self._stock = None
        self.stock = {}
        self.credit = 0

        self.man_loggedIn = False

    #region -------------- User Methods --------------
    def load(self):
        with open(self.filename, "r") as file:
            self._stock = json.loads(file.read())

            self.stock = {}
            for elem in self._stock:
                if (elem["cod"] in self.stock): raise ExecutionError(f"Item duplicado: {self.cod}")

                self.stock[elem["cod"]] = {
                    "nome": elem["nome"],
                    "quant": elem["quant"],
                    "preco": int(float(elem["preco"]) * 100)
                }

    def save(self):
        if self._stock == None: raise ExecutionError("Stock não carregado.")

        stock = []
        for cod in self.stock:
            elem = self.stock[cod]
            stock.append({ "cod": cod, "nome": elem["nome"], "quant": elem["quant"], "preco": elem["preco"] / 100 })

        enc = json.dumps(stock, indent=4, ensure_ascii=False)
        with open(self.filename, "w") as file:
            file.write(enc)

    def hasCode(self, code):
        return code in self.stock
    
    def _hasCredit(self, code):
        return self.credit >= self.stock[code]["preco"]
    
    def dispense(self, code):
        if (not self.hasCode(code)): raise ExecutionError("Código Inválido.")
        if (self.stock[code]["quant"] == 0): raise ExecutionError("Stock insuficiente para satisfazer o seu pedido.")
        if (not self._hasCredit(code)): raise ExecutionError(
            "Saldo insufuciente para satisfazer o seu pedido.\n"
            f"Saldo = {self.formatMoney(self.credit)}; Pedido = {self.formatMoney(self.stock[code]['preco'])}"
        )

        self.stock[code]["quant"] -= 1
        self.consumeCredit(self.stock[code]["preco"])

        return self.stock[code].copy()

    def getCredit(self):
        return self.credit

    def printCredit(self):
        printMaq(f"Saldo = {self.formatMoney(self.credit)}")

    def addCredit(self, cents):
        if (cents <= 0): raise ExecutionError("Quantidade inválida.")
        self.credit += cents

    def consumeCredit(self, cents):
        if (cents <= 0): raise ExecutionError("Quantidade inválida.")
        self.credit -= cents

    def setCredit(self, cents):
        self.credit = min(0, cents)

    def formatMoney(self, money, breakCoins = False):
        if (not breakCoins):
            euros = money // 100
            cents = money % 100

            buf = ""
            if (euros > 0): buf += f"{euros}e"
            if (cents > 0): buf += f"{cents}c"

            if (euros == 0 and cents == 0): buf = f"0e0c"
            return buf
            
            # return f"{euros}e{cents}c"
        else:
            # quant = [200, 100, 50, 20, 10, 5, 1]
            quant = MachineState.MOEDAS
            qlist = list(map(lambda _: 0, quant))
            ql = len(quant)
            qi = 0

            buf = money

            # Set starting point to first coin that can represent the part of the quantity 
            while buf < quant[qi] and qi < ql - 1: qi += 1

            while qi < ql and buf >= quant[qi]:
                buf -= quant[qi]
                qlist[qi] += 1

                # Set next starting point to first coin that can represent the part of ther remainder 
                while buf < quant[qi] and qi < ql - 1: qi += 1

            fmt = ""
            for i in range(0, ql):
                if (qlist[i] == 0): continue

                q = quant[i]
                kind = "e" if q >= 100 else "c"
                knum = q // 100 if q >= 100 else q

                fmt += f"{qlist[i]}x {knum}{kind}"
                if (i < ql - 1): fmt += ", "
                else: fmt += "."
            
            if (fmt == ""): return "-"
            else: return fmt
    #endregion -------------- User Methods --------------

    #region -------------- Maintenance Methods --------------
    def man_isCodeValid(self, code):
        return code == _MAINTENANCE_CODE

    def man_isLoggedIn(self):
        return self.man_loggedIn

    def man_login(self, code):
        if (self.man_isCodeValid(code)):
            self.man_loggedIn = True
            return True
        else:
            return False

    def man_logout(self):
        self.man_loggedIn = False

    def man_getProductPointer(self, code):
        if (not self.hasCode(code)): raise ExecutionError("Código Inválido.")
        return self.stock[code]

    def man_getProduct(self, code):
        return self.man_getProductPointer(code).copy()

    def man_restock(self, code, quant):
        if (not self.hasCode(code)): raise ExecutionError("Código Inválido.")
        if (quant <= 0): raise ExecutionError("Quantidade inválida.")

        self.stock[code]["quant"] += quant 

    def man_addnew(self, code, name, quant, preco):
        if (self.hasCode(code)): raise ExecutionError("Código já existe.")
        if (quant <= 0): raise ExecutionError("Quantidade inválida.")
        if (preco <= 0): raise ExecutionError("Preço inválido.")

        self.stock[code] = { "nome": name, "quant": quant, "preco": preco }

    def man_remove(self, code, quant):
        if (not self.hasCode(code)): raise ExecutionError("Código não existe.")
        if (quant <= 0): raise ExecutionError("Quantidade inválida.")
        
        self.stock[code]["quant"] -= min(quant, self.stock[code]["quant"])
        return self.stock[code]["quant"]
    #endregion -------------- Maintenance Methods --------------

class Command:
    keyword: list[str]
    caseSensitive: bool = False
    description: str = "Figure it out ¯\_(ツ)_/¯"
    usage: str = "N/A"
    name: str | None = None
    hidden: bool = False

    def __repr__(self):
        return f"{type(self).__name__}"

    @classmethod
    def getName(cls):
        if (cls.name is None):
            return cls.__name__.replace("Command", "")
        else:
            return cls.name

    @classmethod
    def accepts(cls, w):
        if cls.caseSensitive:
            return any(w == kw for kw in cls.keyword)
        else:
            return any(w.upper() == kw.upper() for kw in cls.keyword)

    @classmethod
    @abstractmethod
    def process(cls, s: StringStream):
        raise NotImplementedError()
        pass

    @abstractmethod
    def execute(self, state):
        raise NotImplementedError()
        pass

    def _setMatch(self, word):
        self._match = word
        return self

class MonoCommand(Command):
    usage = ""

    def __init__(self):
        pass

    @classmethod
    def process(cls, s: StringStream):
        return cls()

class ListarCommand(MonoCommand):
    keyword = ["LISTAR", "L"]
    description = "Lista os produtos em stock."

    def execute(self, state):
        maxCodLen   = 3
        maxNomeLen  = 4
        maxQuantLen = 10
        maxPrecoLen = 5

        for key in state.stock:
            elem = state.stock[key]
            maxCodLen = max(maxCodLen, len(key))
            maxNomeLen = max(maxNomeLen, len(elem["nome"]))
            maxQuantLen = max(maxQuantLen, len(str(elem["quant"])))
            maxPrecoLen = max(maxPrecoLen, len(str(elem["preco"])))

        printMaq(" ")
        print(f"{'cod'.ljust(maxCodLen)} | {'nome'.ljust(maxNomeLen)} | {'quantidade'.ljust(maxQuantLen)} | preco")
        print("-" * (maxCodLen + maxNomeLen + maxQuantLen + maxPrecoLen + 9))
        for key in state.stock:
            elem = state.stock[key]
            # print((
            #     f"{key.ljust(maxCodLen + 2)} {elem['nome'].ljust(maxNomeLen + 2)} "
            #     f"{str(elem['quant']).ljust(maxQuantLen + 2)} {str(elem['preco'])}"
            # ))
            print((
                f"{key.ljust(maxCodLen + 2)} {elem['nome'].ljust(maxNomeLen + 2)} "
                f"{str(elem['quant']).ljust(maxQuantLen + 2)} {state.formatMoney(elem['preco'])}"
            ))

class SaldoCommand(MonoCommand):
    keyword = ["SALDO", "SAL", "..."]
    description = "Mostra o saldo atual."

    def execute(self, state):
        state.printCredit()

class EjetarCommand(MonoCommand):
    keyword = ["EJETAR", "EJECT", "E"]
    description = "Ejeta o saldo atual na forma de moedas."

    def execute(self, state: MachineState):
        cred = state.getCredit()
        state.setCredit(0)
        printMaq(f"Pode retirar o troco: {state.formatMoney(cred, True)}")

class SairCommand(MonoCommand):
    keyword = ["SAIR", "S"]
    description = "Sai da interface da máquina e ejeta o saldo retido."

    def execute(self, state):
        if (self == _SYSTEM): print()

        EjetarCommand.execute(_SYSTEM, state)
        state.save()

        printMaq("Até à próxima")
        exit(0)
        pass

class ClearCommand(MonoCommand):
    keyword = ["LIMPAR", "CLEAR", "CLS"]
    description = "Limpa a consola da máquina."

    def execute(self, state):
       clear()


class HelpCommand(Command):
    keyword = ["AJUDA", "HELP", "INSTRUÇÕES", "INSTRUCOES", "A", "H"]
    description = "Lista os comandos da máquina, ou informação sobre um comando específico."
    usage = ["AJUDA", "AJUDA <comando>"]

    def __init__(self, cmd):
        self.cmd = cmd

    @classmethod
    def process(cls, s: StringStream):
        buf = ""

        while (not s.eof() and not(ch := s.next()).isspace()):
            buf += ch

        return cls(buf)

    def execute(self, state):
        if (self.cmd == ""):
            msg = "Máquina de Vending 4ABCD\n\nComandos:\n"
            for cmd in COMMAND_LIST:
                if (cmd.hidden and not state.man_isLoggedIn()): continue
                isManCmd = cmd.hidden and state.man_isLoggedIn()

                msg += f" - {'*' if isManCmd else ''}{cmd.getName()}\n"
                msg += f"   {cmd.description}\n"
            
            printMaq(msg)
        else:
            tcmds = list(filter(lambda c: c.accepts(self.cmd), COMMAND_LIST))
            if (len(tcmds) == 0): raise ExecutionError("Comando desconhecido.")

            tcmd = tcmds[0]
            if (tcmd.hidden and not state.man_isLoggedIn()): raise ExecutionError("Comando desconhecido.")
            isManCmd = tcmd.hidden and state.man_isLoggedIn()

            msg = f"Máquina de Vending 4ABCD\n\n{'*' if isManCmd else ''}{tcmd.keyword[0].upper()}:\n"
            msg += f"  - Aliases: {', '.join(tcmd.keyword[1:])}\n"
            msg += f"  - Descrição: {tcmd.description}\n"
            if (tcmd.usage != "N/A"): 
                if (tcmd.usage == ""): 
                    msg += f"  - Usage example(s): {tcmd.keyword[0].upper()}"
                elif (isinstance(tcmd.usage, list)):
                    _nl = "\n" 
                    msg += f"  - Usage example(s): \n    - {f'{_nl}    - '.join(tcmd.usage)}"
                else: 
                    msg += f"  - Usage example(s): {tcmd.usage}"
            printMaq(msg)

class MoedaCommand(Command):
    keyword = ["MOEDA", "M"]
    description = "Insere crédito na máquina por moedas na forma <quantia>(e|c), separadas por vírgulas e terminadas por um ponto."
    usage = ["MOEDA 5c.", "MOEDA 1e.", "MOEDA 1e, 50c, 20c."]

    def __init__(self, moedas):
        self.moedas = moedas

    def __repr__(self):
        return f"{type(self).__name__}[{', '.join(m for m in self.moedas)}]"

    @classmethod
    def process(cls, s: StringStream):
        moedas = []
        buf = ""

        # Permissive. Statement ends with ".", but can be ommited.
        while (not s.eof() and (ch := s.peek()) != "." and ch != "\n"):
            if ch.isdigit() or ch == "c" or ch == "e": 
                buf += ch
                s.next()
            elif ch == ",":
                if (buf[-1] != "c" and buf[-1] != "e"): s.die(f"Quantia desconhecida: {repr(buf[-1])}")
                moedas.append(buf)
                buf = ""

                s.next()
                readWhitespace(s)
            else:
                s.die(f"Caráter desconhecido: {repr(ch)}")

        if len(buf) > 0: 
            if (buf[-1] != "c" and buf[-1] != "e"): s.die(f"Quantia desconhecida: {repr(buf[-1])}")
            moedas.append(buf)

        # Stream does not need to be flushed, because it's lifetime ends at the end of processing.
        return cls(moedas)

    def execute(self, state: MachineState):
        if (len(self.moedas) == 0): raise ExecutionError("Moedas não fornecidas.")

        for moeda in self.moedas:
            kind = moeda[-1]
            mult = 100 if (kind == "e") else 1
            quant = int(moeda[:-1])
            tq = quant * mult

            if (MachineState.MOEDAS.count(tq) == 0): raise ExecutionError(f"Moeda inválida: {moeda}")

            state.addCredit(quant * mult)
        
        state.printCredit()

class SelecionarCommand(Command):
    keyword = ["SELECIONAR", "SEL"]
    description = "Seleciona um produto para adquirir. Caso não possúa saldo suficiente, será retornado um erro."
    usage = "SELECIONAR [produto]"

    def __init__(self, product):
        self.product = product

    def __repr__(self):
        return f"{type(self).__name__}[{self.product}]"

    @classmethod
    def process(cls, s: StringStream):
        buf = ""
        while (not s.eof() and (ch := s.next()) != "\n"):
            if (ch.isdigit() or ch.isalpha()):
                buf += ch
            else:
                s.die(f"Caráter desconhecido: {repr(ch)}")

        return cls(buf)

    def execute(self, state: MachineState):
        if (len(self.product) == 0): raise ExecutionError("Código de produto inválido.")
        if (not state.hasCode(self.product)): raise ExecutionError("Código de produto inexistente.")

        prod = state.dispense(self.product)
        printMaq(f"Pode retirar o produto dispensado \"{prod['nome']}\"")
        state.printCredit()

class MaintenanceCommand(Command):
    keyword = ["MANUNTENÇÃO", "MAN"]
    description = "(Des)ativa o modo de manuntenção."
    usage = "MANUNTANÇÃO [código]"
    hidden = True

    def __init__(self, cod):
        self.cod = cod

    def __repr__(self):
        return f"{type(self).__name__}[{self.cod}]"

    @classmethod
    def process(cls, s: StringStream):
        buf = ""
        while (not s.eof() and (ch := s.next()) != "\n"):
            if (re.match(r"[a-zA-Z0-9\-_\.]", ch)):
                buf += ch
            else:
                s.die(f"Caráter desconhecido: {repr(ch)}")

        return cls(buf)

    def execute(self, state: MachineState):
        if (self.cod == "" and state.man_isLoggedIn()):
            state.man_logout()
            printMaq("Modo de manuntanção terminado.")
            return

        if (not state.man_login(self.cod)):
            printError("Código inválido.")
        else:
            printMaq("Bem-vindo ao modo de manuntenção. Use AJUDA para ver os comandos disponíveis.")

class AddStockCommand(Command):
    keyword = ["ADICIONAR", "ADD", "A"]
    description = "Adiciona mais stock de um dado produto da máquina."
    usage = "ADICIONAR [código] [quantidade]"
    hidden = True
    name = "Adicionar"

    def __init__(self, cod, quant):
        self.cod = cod
        self.quant = quant

    @classmethod
    def process(cls, s: StringStream):
        cod = ""
        while (not s.eof() and (ch := s.next()) != "\n"):
            if (ch.isdigit() or ch.isalpha()):
                cod += ch
            elif (ch.isspace()):
                break
            else:
                printDevError(s.proximaParagem(f"Caráter desconhecido para código de produto: {repr(ch)}"))

        readNoLFWhitespace(s)

        quant = ""
        while (not s.eof() and (ch := s.next()) != "\n"):
            if (ch.isdigit()):
                quant += ch
            else:
                printDevError(s.proximaParagem(f"Caráter desconhecido para quantia: {repr(ch)}"))

        return cls(cod, quant)
    
    def execute(self, state: MachineState):
        if (not state.man_isLoggedIn()): return _SYM_HIDE # Silently fail if not logged in. Command should not be revealed.

        if (len(self.cod) == 0): raise ExecutionError("Código de produto inválido.")
        if (not state.hasCode(self.cod)): raise ExecutionError("Código de produto inexistente.")

        try:
            quant = int(self.quant)
        except Exception:
            raise ExecutionError("Quantia inválida.")

        state.man_restock(self.cod, quant)
        printMaq(f"Adicionado(s) {self.quant}x {self.cod} ao stock.")

class ModifyStockCommand(Command):
    keyword = ["MODIFICAR", "MOD"]
    description = "Edita o stock da máquina."
    usage = [
        "MODIFICAR ADD [código] [nome] [quant] [preco]", 
        "MODIFICAR EDIT preco [código] [preco]", 
        "MODIFICAR REMOVE [código] <quant>",
        "MODIFICAR REMOVE [código] all"
    ]
    hidden = True
    name = "Modificar"

    def __init__(self, subcmd, args):
        self.subcmd = subcmd
        self.args = args

    @classmethod
    def process(cls, s: StringStream):
        subcmd = ""
        while (not s.eof() and (ch := s.next()) != "\n"):
            if (ch.isalpha()):
                subcmd += ch
            elif (ch.isspace()):
                break
            else:
                printDevError(s.proximaParagem(f"Caráter desconhecido para subcomando: {repr(ch)}"))

        readNoLFWhitespace(s)

        args = []
        buf = ""
        while (not s.eof() and (ch := s.next()) != "\n"):
            if (ch == '"'):
                if (buf != ""): 
                    args.append(buf)
                    buf = ""

                # s.next()
                while (not s.eof() and (ch := s.next()) != "\""): buf += ch
                if (ch != "\""): s.die("String não terminada.")

                args.append(buf)
                buf = ""
                s.next()
                readNoLFWhitespace(s)
            elif (ch.isspace()):
                args.append(buf)
                buf = ""
                readNoLFWhitespace(s)
            else:
                buf += ch

        if (len(buf) > 0): args.append(buf)

        return cls(subcmd, args)
    
    def execute(self, state: MachineState):
        if (not state.man_isLoggedIn()): return _SYM_HIDE # Silently fail if not logged in. Command should not be revealed.

        match (self.subcmd.upper()):
            case "ADD":
                if (len(self.args) < 4): raise ExecutionError(f"Utilização: {self.usage[0]}")
                [cod, nome, _quant, _preco] = self.args

                if (len(cod) == 0): raise ExecutionError("Código de produto inválido.")
                if (not re.match(r"^[A-Z]\d+$", cod)): raise ExecutionError("Código de produto inválido.")
                if (state.hasCode(cod)): raise ExecutionError("Código de produto já existe.")

                try: quant = int(_quant)
                except Exception: raise ExecutionError("Quantia inválida.")

                try: preco = int(_preco)
                except Exception: raise ExecutionError("Preço inválido.")

                state.man_addnew(cod, nome, quant, preco)
                printMaq(f"Produto {nome} adicionado ao stock com o código {cod}")
            case "EDIT":
                if (len(self.args) < 1): raise ExecutionError(f"Utilização: {self.usage[1]}")

                match (self.args[0]):
                    case "preco":
                        if (len(self.args) < 3): raise ExecutionError(f"Utilização: {self.usage[1]}")

                        cod = self.args[1]

                        if (len(cod) == 0): raise ExecutionError("Código de produto inválido.")
                        if (not re.match(r"^[A-Z]\d+$", cod)): raise ExecutionError("Código de produto inválido.")
                        if (not state.hasCode(cod)): raise ExecutionError("Código de produto não existe.")

                        try: preco = int(self.args[2])
                        except Exception: raise ExecutionError("Preço inválido.")

                        prod = state.man_getProductPointer(cod)
                        oldPreco = prod["preco"]
                        prod["preco"] = preco

                        printMaq(f"Alterado preço do produto {prod['nome']}: {oldPreco} -> {preco}")
                    case _:
                        raise ExecutionError(f"Operação de edição desconhecida.")
                pass
            case "REMOVE":
                if (len(self.args) < 2): raise ExecutionError(f"Utilização: \n  - {self.usage[2]}\n  - {self.usage[3]}")
                cod = self.args[0]
                _quant = self.args[1]
                # _quant = self.args[1] if len(self.args) > 1 else "0x7fffffff"

                if (len(cod) == 0): raise ExecutionError("Código de produto inválido.")
                if (not re.match(r"^[A-Z]\d+$", cod)): raise ExecutionError("Código de produto inválido.")
                if (not state.hasCode(cod)): raise ExecutionError("Código de produto não existe.")
                
                if (_quant.upper() == "ALL"): quant = 0x7fffffff
                else:
                    try: quant = int(_quant)
                    except Exception: raise ExecutionError("Quantia inválida.")

                prod = state.man_getProduct(cod)
                nquant = state.man_remove(cod, quant)
                printMaq(f"Removidos {prod['quant'] - nquant}x {prod['nome']}.\nNova quantidade: {nquant}")
            case _:
                raise ExecutionError(f"Subcomando desconhecido.")



COMMAND_LIST = [
    ListarCommand,
    SaldoCommand,
    EjetarCommand,
    SairCommand,
    ClearCommand,
    HelpCommand,
    MoedaCommand,
    SelecionarCommand,

    MaintenanceCommand,
    AddStockCommand,
    ModifyStockCommand
]

def processCommand(l):
    s = StringStream(l)

    try:
        while not s.eof():
            word = readWord(s)
            # log(repr(word))

            for _cmd in COMMAND_LIST:
                if (_cmd.accepts(word)):
                    readWhitespace(s)
                    return (None, _cmd.process(s)._setMatch(word))

            if _DEBUG:
                if (s.eof()): s.proximaParagem(f"Lexical error: Reached EOF.")
                else: s.proximaParagem(f"Lexical error: Unexpected character at position: {repr(s.peek())}")
            
            return ((-2, word), None)
    except LexicalError as e:
        # printError(e.message)
        return ((-1, e.message), None)

    return ((0, None), None)

#region ============== CLI Utils ==============
def printMaq(s):
    lines = s.splitlines()
    for line in lines: sys.stdout.write(f"\x1b[36mmaq: \x1b[0m{line}\n")
    
    sys.stdout.flush()

def printError(e):
    sys.stdout.write(f"\x1b[31m{e}\x1b[0m\n")
    sys.stdout.flush()

def printDevError(e):
    if not _DEBUG: return

    tb_str = '  '.join(traceback.format_exception(e))
    # print(f"{type(e).__name__} at {__file__}:{e.__traceback__.tb_lineno}: {e}\n  {tb_str}")
    print(tb_str)

def clear():
    print("\033[H\033[J", end="")
#endregion ============== CLI Utils ==============

#region ============== CLI ==============
def timeToDie(sig, frame):
    SairCommand.execute(_SYSTEM, state)
    exit(0)
signal.signal(signal.SIGINT, timeToDie)

printMaq("A iniciar...")
try:
    state = MachineState("stock.json")
    state.load()
except RuntimeError as e:
    printError("Erro ocorreu ao iniciar máquina.")
    printDevError(e)
    exit(1)

clear()
printMaq(f"{datetime.datetime.now().isoformat()[:10]}, Stock carregado, Estado atualizado.")
printMaq("Bom dia. Estou disponível para atender o seu pedido.")

kbd = JournaledKeyboardInputHandler()
kbd.printInputPrefix(True)
# while (line := sys.stdin.readline()):

while (line := kbd.getInput()):
    (err, cmd) = processCommand(line)
    if (err is not None):
        (ecod, emsg) = err
        if (ecod == 0): # Ignore
            pass
        elif (ecod == -1):
            printError(emsg)
        elif (ecod == -2):
            printError(f"Comando desconhecido: {emsg}")
        else:
            printError(f"Erro desconhecido")
        
        kbd.printInputPrefix(True)
        continue

    log(f"COMMAND: {cmd}")
    try:
        ret = cmd.execute(state)
        if (ret == _SYM_HIDE):
            printError(f"Comando desconhecido: {cmd._match}")
    except ExecutionError as e:
        # printError(f"Erro ocorreu durante a execução: {e.message}")
        printError(e.message)
    except Exception as e:
        printError("Erro desconhecido ocorreu durante a execução.")
        printDevError(e)

    kbd.printInputPrefix(True)
#endregion ============== CLI ==============
