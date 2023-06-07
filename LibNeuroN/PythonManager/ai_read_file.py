import os
import json

def read_text_from_file(file_path: str) -> str:
    text = ""

    with open(file_path, "r") as file:
        text = file.read()
        file.close()
    
    return text

def read_lines_from_file(file_path: str):
    if (os.path.exists(file_path) == False):
        return ""
    else:
        lines = []

        with open(file_path, "r") as file:
            lines = file.readlines()
            file.close()
        
        return lines

def read_vars_from_file(file_path: str, s1: str, s2: str, s3: str, s4: str) -> dict:
    text = read_lines_from_file(file_path)
    vars = {}
    ignore = []

    for line in text:
        if (ignore.__contains__(text.index(line))):
            continue

        if (line.startswith("//") or line.startswith("#") or line.strip() == ""):
            continue
        elif (line.startswith("[INCLUDE]")):
            vars2 = read_vars_from_file(line[9:len(line)], s1, s2, s3, s4)

            for i in vars2:
                vars[i] = vars2[i]
            
            continue

        try:
            try:
                k = line[line.index("[" + s1 + "]") + len(s1) + 2:line.index("[" + s2 + "]")]
                v = line[line.index("[" + s3 + "]") + len(s3) + 2:line.index("[" + s4 + "]")]
            except:
                continue
        except:
            continue

        vars[k] = v
    
    return vars

def read_from_json(file_path: str):
    intents = None

    with open(file_path, "r") as f:
        intents = json.load(f)
        f.close()

    return intents