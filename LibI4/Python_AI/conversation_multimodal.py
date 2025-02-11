# Import libraries
import json

# Import I4.0 utilities
from server_basics import ExecuteCommandOnDatabase, cfg

def GetConversations(User: str) -> dict[str, list[dict[str, str | list[dict[str, str]]]]]:
    """
    Gets the conversations from the DB.
    """
    # Get the conversations
    results = ExecuteCommandOnDatabase(f"SELECT {cfg.current_data['db']['conversations']['conversation_name']}, {cfg.current_data['db']['conversations']['conversation_data']} FROM {cfg.current_data['db']['conversations']['table']} WHERE {cfg.current_data['db']['conversations']['user']} = %s", [User])
                                       
    # Parse the conversations
    conversations = {}

    for result in results:
        convName = str(result[cfg.current_data["db"]["conversations"]["conversation_name"]])
        convData = str(result[cfg.current_data["db"]["conversations"]["conversation_data"]])

        try:
            conversations[convName] = cfg.JSONDeserializer(convData)
        except:
            continue
    
    return conversations

def GetConversation(User: str, ConversationName: str) -> list[dict[str, str | list[dict[str, str]]]]:
    """
    Get a single conversation from the DB
    """
    # Get the conversation
    results = ExecuteCommandOnDatabase(f"SELECT {cfg.current_data['db']['conversations']['conversation_data']} FROM {cfg.current_data['db']['conversations']['table']} WHERE {cfg.current_data['db']['conversations']['user']} = %s AND {cfg.current_data['db']['conversations']['conversation_name']} = %s LIMIT 1", [User, ConversationName])

    # Check if the conversation exists
    if (len(results) > 0):
        # Exists! Return the conversation
        return cfg.JSONDeserializer(results[0][cfg.current_data["db"]["conversations"]["conversation_data"]])
    
    # Doesn't exist!
    return []

def SaveConversation(User: str, ConversationData: dict[str, list[dict[str, str | list[dict[str, str]]]]] | tuple[str, str | list[dict[str, str]]] | list[tuple[str, str | list[dict[str, str]]]]) -> None:
    """
    Saves a conversation to the DB.
    """
    # Parse the type of conversation
    if (isinstance(ConversationData, tuple)):
        convName = ConversationData[0]
        convData = ConversationData[1] if (isinstance(ConversationData[1], str)) else json.dumps(ConversationData[1])
    elif (isinstance(ConversationData, list)):
        for data in ConversationData:
            SaveConversation(User, data)
            
        return
    elif (isinstance(ConversationData, dict)):
        for convName in list(ConversationData.keys()):
            SaveConversation(User, (convName, ConversationData[convName]))
            
        return
    else:
        raise Exception("Invalid conversation data.")
    
    # Check if the conversation already exists
    results = ExecuteCommandOnDatabase(f"SELECT * FROM {cfg.current_data['db']['conversations']['table']} WHERE {cfg.current_data['db']['conversations']['user']} = %s AND {cfg.current_data['db']['conversations']['conversation_name']} = %s LIMIT 1", [User, convName])

    # Check if the key was found
    if (len(results) > 0):
        # Found!
        # Update the key
        ExecuteCommandOnDatabase(f"UPDATE {cfg.current_data['db']['conversations']['table']} SET {cfg.current_data['db']['conversations']['conversation_data']} = %s WHERE {cfg.current_data['db']['conversations']['conversation_name']} = %s AND {cfg.current_data['db']['conversations']['user']} = %s", [convData, convName, User])
    else:
        # Not found, create
        ExecuteCommandOnDatabase(f"INSERT INTO {cfg.current_data['db']['conversations']['table']} ({cfg.current_data['db']['conversations']['user']}, {cfg.current_data['db']['conversations']['conversation_name']}, {cfg.current_data['db']['conversations']['conversation_data']}) VALUES (%s, %s, %s)", [User, convName, convData])

def DeleteConversation(User: str, ConversationName: str) -> None:
    """
    Deletes a conversation from the DB.
    """
    ExecuteCommandOnDatabase(f"DELETE FROM {cfg.current_data['db']['conversations']['table']} WHERE {cfg.current_data['db']['conversations']['user']} = %s AND {cfg.current_data['db']['conversations']['conversation_name']} = %s", [User, ConversationName])

def DeleteConversations(User: str) -> None:
    """
    Deletes all the conversations from the DB.
    """
    ExecuteCommandOnDatabase(f"DELETE FROM {cfg.current_data['db']['conversations']['table']} WHERE {cfg.current_data['db']['conversations']['user']} = %s", [User])