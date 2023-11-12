import os
import datetime

log_name = str(datetime.datetime.now().day) + "-" + str(datetime.datetime.now().month) + "-"
log_name += str(datetime.datetime.now().year) + "_" + str(datetime.datetime.now().hour) + "-"
log_name += str(datetime.datetime.now().minute) + "-" + str(datetime.datetime.now().second)
log_data = ""

def CheckFilesAndDirs() -> None:
    if (not os.path.exists("Logs/")):
        os.mkdir("Logs/")
    
    if (not os.path.exists("Logs/latest.txt")):
        with open("Logs/latest.txt", "w+") as f:
            f.close()

def AddToLog(Data: str, IncludeTime: bool = True, WriteLogToFile: bool = False, WriteLatest: bool = True) -> None:
    global log_data
    log_data += ""

    if (IncludeTime):
        log_data += "["
        log_data += str(datetime.datetime.now().hour) + ":"
        log_data += str(datetime.datetime.now().minute) + ":"
        log_data += str(datetime.datetime.now().second)
        log_data += "] "

    log_data += Data + "\n"

    if (WriteLogToFile):
        WriteToFile(WriteLatest)

def WriteToFile(WriteLatest: bool = True) -> None:
    CheckFilesAndDirs()

    with open("Logs/" + log_name + ".txt", "w+") as f:
        f.write(log_data)
        f.close()
    
    if (WriteLatest):
        with open("Logs/latest.txt", "w+") as f:
            f.write(log_data)
            f.close()