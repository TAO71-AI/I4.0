# Import I4.0 utilities
from server_basics import ExecuteCommandOnDatabase, cfg

def GetMemories(User: str) -> list[str]:
    """
    Gets the memories from the DB.
    """
    # Get all the memories from the database
    results = ExecuteCommandOnDatabase(f"SELECT {cfg.current_data['db']['memories']['memory']} FROM {cfg.current_data['db']['memories']['table']} WHERE {cfg.current_data['db']['memories']['user']} = %s", [User])
    memories = []

    # For each result
    for result in results:
        # Get the memory
        memories.append(str(result[cfg.current_data["db"]["memories"]["memory"]]))
    
    # Return the memories
    return memories

def GetMemory(User: str, MemoryIndex: int) -> str:
    """
    Get a single memory from the DB
    """
    # Get all the memories
    mems = GetMemories(User)

    # Check if the memory exists
    if (len(mems) > MemoryIndex):
        # Exists! Return the memory
        return mems[MemoryIndex]
    
    # Doesn't exist!
    return ""

def SaveMemory(User: str, Memory: str | list[str] | dict[str, list[str]]) -> None:
    """
    Saves a memory to the DB.
    """
    # Parse the type of memory
    if (isinstance(Memory, list)):
        for memory in Memory:
            SaveMemory(User, memory)
            
        return
    elif (isinstance(Memory, dict)):
        for user in list(Memory.keys()):
            SaveMemory(user, Memory[user])
        
        return
    elif (not isinstance(Memory, str)):
        raise Exception("Invalid memory data.")
    
    # Execute the command
    ExecuteCommandOnDatabase(f"INSERT INTO {cfg.current_data['db']['memories']['table']} ({cfg.current_data['db']['memories']['user']}, {cfg.current_data['db']['memories']['memory']}) VALUES (%s, %s)", [User, Memory])

def DeleteMemory(User: str, Memory: str) -> None:
    """
    Deletes a memory from the DB.
    """
    ExecuteCommandOnDatabase(f"DELETE FROM {cfg.current_data['db']['memories']['table']} WHERE {cfg.current_data['db']['memories']['user']} = %s AND {cfg.current_data['db']['conversations']['memory']} = %s", [User, Memory])

def DeleteMemories(User: str) -> None:
    """
    Deletes all the memories from the DB.
    """
    ExecuteCommandOnDatabase(f"DELETE FROM {cfg.current_data['db']['memories']['table']} WHERE {cfg.current_data['db']['memories']['user']} = %s", [User])