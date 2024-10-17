# Import libraries
import json

Memories: dict[str, list[str]] = {}

def AddMemory(Key: str, Memory: str):
    # Check if the key exists in the memories
    if (Key not in Memories):
        # Doesn't exists in memory, create it
        Memories[Key] = []
    
    # Save the memory
    Memories[Key].append(Memory)

def RemoveMemories(Key: str) -> None:
    # Check if the key exists in the memories
    if (Key in Memories):
        # Exists in memory, remove it
        Memories.pop(Key)

def RemoveMemory(Key: str, Index: int) -> None:
    # Check if the key and memory exists
    if (Key in Memories and Index >= 0 and Index < len(Memories[Key])):
        # Exists, delete it
        Memories[Key].pop(Index)
    elif (Key in Memories):
        # Invalid index
        raise ValueError("Invalid memory index. Can't delete memory.")

def SaveMemories() -> None:
    # Save the memories into a file
    with open("memories.json", "w+") as f:
        f.write(json.dumps(Memories))
        f.close()

def LoadMemories() -> dict[str, list[str]]:
    global Memories

    # Load the memories from a file
    try:
        # Try to read the file and load the memories
        with open("memories.json", "r") as f:
            mems = json.loads(f.read())
            Memories = mems

            return mems
    except FileNotFoundError:
        # File doesn't exist, create an empty dictionary
        return {}
    
def GetMemories(Key: str) -> list[str]:
    # Check if the key exists
    if (Key in Memories):
        # Return the memories
        return Memories[Key]
    
    # Key doesn't exist, return an empty list
    return []

LoadMemories()