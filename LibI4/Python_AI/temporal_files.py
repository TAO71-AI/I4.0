# Import libraries
import os

# Create global variables
FilesTemplate: str = "temporal_{id}.{extension}"
TemporalDirectory: str = "/tmp"

def __create_file_name__(Extension: str) -> str:
    # Create id
    id = 0
    fileName = f"{TemporalDirectory}/{FilesTemplate.replace('{id}', str(id)).replace('{extension}', Extension)}"

    # Check if the file exists
    while (os.path.exists(fileName)):
        id += 1
        fileName = f"{TemporalDirectory}/{FilesTemplate.replace('{id}', str(id)).replace('{extension}', Extension)}"
    
    # Return the file name
    return fileName

def CreateTemporalFile(FileType: str, FileData: bytes) -> str:
    # Save the file
    fileName = __create_file_name__(FileType)

    with open(fileName, "wb") as f:
        f.write(FileData)
    
    # Return the file path
    return fileName