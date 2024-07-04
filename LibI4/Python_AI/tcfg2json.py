import os
import json
import sys

# Set variables
TCFGFilePath: str = "config.tcfg"
JSONOutputPath: str = "config.json"
RemoveTCFG: bool = False
Result: dict[str] = {}

# Set variables from args
for arg in sys.argv:
    if (sys.argv.index(arg) == 0):
        continue

    if (arg.startswith("input=")):
        TCFGFilePath = arg[6:]
    elif (arg.startswith("output=")):
        JSONOutputPath = arg[7:]
    elif (arg == "rinput"):
        RemoveTCFG = True

# Check file
if (not os.path.exists(TCFGFilePath)):
    raise FileNotFoundError("Input (TCFG) file doesn't exist.")

# Print warning
print("WARNING! Using TCFG is deprecated. There are some settings that can't be configured by this script because they doesn't exists on TCFG.")
print("Please remember that you may have to change some settings.")

# Read file
with open(TCFGFilePath, "r") as f:
    FileLines = f.readlines()
    f.close()

# Read lines and append config
for line in FileLines:
    ldata = line.split("=")
    key = ldata[0]
    value = ""

    for lval in ldata:
        if (ldata.index(lval) == 0):
            continue

        value += lval + "="

    if (key == "sys_msg_first_person"):
        key = "system_messages_in_first_person"
    elif (key == "use_gpu"):
        key = "use_gpu_if_available"
    
    value = value[:-1].strip()

    try:
        Result[key] = json.loads(value)
    except:
        try:
            Result[key] = eval(value)
        except:
            try:
                Result[key] = int(value)
            except:
                try:
                    Result[key] = float(value)
                except:
                    Result[key] = value

# Add extra config
Result["styletts2"] = {"models": {}, "steps": 5}

# Write to file
with open(JSONOutputPath, "w") as f:
    json.dump(Result, f, indent = 4)
    f.close()

# Remove old file
if (RemoveTCFG):
    os.remove(TCFGFilePath)

# Print result
print("Done!")