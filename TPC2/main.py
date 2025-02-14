from functools import reduce

# Constants
__DEBUG = False

EXPECTED_KEYS = ["nome", "desc", "anoCriacao", "periodo", "compositor", "duracao", "_id"]

INPUT_FILE = "obras.csv"
RESULTS_COMPOSERS = "result_composers.json"
RESULTS_PERIODS = "result_periods.json"
RESULTS_MIXED = "result_mixed.json"

#region ============== Helpers ==============
def log(s):
    if __DEBUG: print(s)

def peek(f, n = 1):
    pos = f.tell()
    ch = f.read(n)
    f.seek(pos)
    return ch

def zip(template, props):
    ret = {}
    for i in range(len(template)):
        if i >= len(props): break

        # log(f"LINE: {i} {template[i]} {props[i]}")
        ret[template[i]] = props[i]

    return ret
#endregion ============== Helpers ==============
    
def readCSVLine(f):
    ret = []

    temp = ""
    i = 0
    capture = False

    ch = f.read(1)
    while (ch):
        match (ch):
            case "\n":
                if (capture): 
                    # Skip whitespace
                    while (peek(f).isspace()): f.read(1)
                    ch = peek(f)
                else:
                    ret.append(temp)
                    break
            case ";": 
                if (capture): pass
                else:
                    ret.append(temp)
                    temp = ""
                    ch = f.read(1)

                    continue
            case "\"":
                # If capturing and encounters '""', it's an escaped quote. Capture only one.
                if (peek(f, 1) == "\""): 
                    f.read(1)
                else:
                    capture = not capture

                    # Override regular behavior. Do not add the quote to the acc.
                    ch = f.read(1)
                    continue

        temp += ch
        ch = f.read(1)
    
    return ret

def readCSVFile(filePath):
    with open(filePath, "rt") as file:
        head = readCSVLine(file)
        log(f"HEAD: {head}")
        
        table = []
        while peek(file) != "":
            rowData = readCSVLine(file)
            table.append(zip(head, rowData))

        log(f"TABLE: {table[1]}")

        return (head,table)

def processDataset(ds: (list[str],list[str])):
    (head,table) = ds

    if EXPECTED_KEYS != head: raise "Unsupported format for input file."

    for row in table:
        if "," in row["compositor"]:
            row["compositor"] = " ".join(reversed(row["compositor"].split(", ")))


def init():
    ds = readCSVFile(INPUT_FILE)
    processDataset(ds)

    #region ------- List of composers, sorted alphabetically -------
    composers = list(set(map(lambda row: row["compositor"], ds[1])))
    composers.sort(key=str.lower)

    composersJson = "[\n"
    for composer in composers:
        composersJson += f"    \"{composer}\",\n"
    composersJson = composersJson[:-2] + "\n"
    composersJson += "]"
    
    with open(RESULTS_COMPOSERS, "wt") as composersFile: composersFile.write(composersJson)
    #endregion ------- List of composers, sorted alphabetically -------

    #region ------- List of number of works per period -------
    def periodReducer(a,c):
        if c["periodo"] not in a: a[c["periodo"]] = 1
        else: a[c["periodo"]] += 1
        return a

    periods = reduce(periodReducer, ds[1], {})

    periodsJson = "{\n"
    for (key,value) in periods.items():
        periodsJson += f"    \"{key}\": {value},\n"
    periodsJson = periodsJson[:-2] + "\n"
    periodsJson += "}"
    
    with open(RESULTS_PERIODS, "wt") as periodsFile: periodsFile.write(periodsJson)
    #endregion ------- List of composers, sorted alphabetically -------

    #region ------- List of works per period -------
    def periodWorksReducer(a,c):
        if c["periodo"] not in a: a[c["periodo"]] = []
        else: a[c["periodo"]].append(c["nome"])
        return a

    periodWorks = reduce(periodWorksReducer, ds[1], {})
    for period in periodWorks.values(): period.sort(key=str.lower)

    periodWorksJson = "{\n"
    for (key,value) in periodWorks.items():
        periodWorksJson += f"    \"{key}\": [\n"
        for work in value:
            periodWorksJson += f"        \"{work}\",\n"

        periodWorksJson = periodWorksJson[:-2] + "\n"
        periodWorksJson += f"    ],\n"

    periodWorksJson = periodWorksJson[:-2] + "\n"
    periodWorksJson += "}"
    
    with open(RESULTS_MIXED, "wt") as periodWorksFile: periodWorksFile.write(periodWorksJson)
    #endregion ------- List of composers, sorted alphabetically -------



init()
