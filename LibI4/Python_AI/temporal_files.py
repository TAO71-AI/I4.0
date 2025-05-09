# Import libraries
import os
import time

# Create variables
TemporalFile: str = "temp.txt"
FilesTemplate: str = "temporal_{id}.{extension}"
Busy: bool = False

def __create_files__() -> None:
    # Define global variables
    global Busy

    # Set to busy
    Busy = True

    # Create the temporal file
    if (not os.path.exists(TemporalFile)):
        with open(TemporalFile, "w+") as f:
            f.write("")
    
    # Set to not busy
    Busy = False

def __create_file_name__(Extension: str) -> str:
    # Create id
    id = 0
    fileName = FilesTemplate.replace("{id}", str(id)).replace("{extension}", Extension)

    # Check if the file exists
    while (os.path.exists(fileName)):
        id += 1
        fileName = FilesTemplate.replace("{id}", str(id)).replace("{extension}", Extension)
    
    # Return the file name
    return fileName

def __read_temporal_file__() -> str:
    # Define global variables
    global Busy

    # Pause if busy
    __pause__()

    # Create files
    __create_files__()

    # Set to busy
    Busy = True

    # Read the file
    with open(TemporalFile, "r") as f:
        data = f.read()
    
    # Set to not busy
    Busy = False
    
    return data

def __pause__() -> None:
    while (Busy):
        time.sleep(0.1)

def CreateTemporalFile(FileType: str, FileData: bytes) -> str:
    # Define global variables
    global Busy

    # Pause if busy
    __pause__()

    # Create all the files
    __create_files__()

    # Set to busy
    Busy = True

    # Save the file
    if (FileType == "image"):
        fileExt = "png"
    elif (FileType == "audio"):
        fileExt = "wav"
    elif (FileType == "video"):
        fileExt = "mp4"
    else:
        raise Exception("Invalid file type.")

    fileName = __create_file_name__(fileExt)

    with open(fileName, "wb") as f:
        f.write(FileData)
    
    # Read the data from the temporal file
    with open(TemporalFile, "r") as f:
        data = f.read()

    # Save the file name into the temporal file (for later deletion)
    with open(TemporalFile, "w") as f:
        f.write(f"{data}\n{fileName}")
    
    # Set to not busy
    Busy = False
    
    return fileName

def DeleteTemporalFile(Name: str) -> None:
    # Define global variables
    global Busy

    # Check if the name is empty
    if (len(Name.strip()) == 0):
        return

    # Pause if busy
    __pause__()

    # Read the temporal file
    temp = __read_temporal_file__().split("\n")

    # Set to busy
    Busy = True

    # Delete the file
    if (Name in temp):
        os.remove(Name)
        data = "".join(f"{i}\n" if (i != Name) else "" for i in temp)

        with open(TemporalFile, "w") as f:
            f.write(data)
    else:
        print("File not found. Ignoring.")
    
    # Set to not busy
    Busy = False

def DeleteAllFiles() -> None:
    # Read the temporal file
    temp = __read_temporal_file__().split("\n")

    # Delete the files
    for name in temp:
        DeleteTemporalFile(name)