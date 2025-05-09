# Import I4.0 utilities
from server_basics import ExecuteCommandOnDatabase, cfg

def GetCachedResponse(SystemPrompt: str, UserPrompt: str) -> str | None:
    """
    Get the cached response from the database. Returns `None` if not found.
    """
    # Get the cached response
    results = ExecuteCommandOnDatabase(f"SELECT * FROM {cfg.current_data['db']['cache']['table']} WHERE {cfg.current_data['db']['cache']['system_prompt']} = %s AND {cfg.current_data['db']['cache']['user_prompt']} = %s LIMIT 1", [SystemPrompt, UserPrompt])

    if (len(results) == 0):
        return None
    
    return results[0][cfg.current_data["db"]["cache"]["ai_response"]]

def SaveData(SystemPrompt: str, UserPrompt: str, AIResponse: str) -> None:
    """
    Caches the prompt and response into the DB.
    """
    ExecuteCommandOnDatabase(f"INSERT INTO {cfg.current_data['db']['cache']['table']} ({cfg.current_data['db']['cache']['system_prompt']}, {cfg.current_data['db']['cache']['user_prompt']}, {cfg.current_data['db']['cache']['ai_response']}) VALUES (%s, %s, %s)", [SystemPrompt, UserPrompt, AIResponse])