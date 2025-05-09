# Import I4.0 utilities
from server_basics import ExecuteCommandOnDatabase, cfg

# Import other libraries
import json

def SaveData(MessageUser: list[dict[str, str]], MessageAI: list[dict[str, str]]) -> None:
    """
    Saves data into the DB.
    """
    ExecuteCommandOnDatabase(f"INSERT INTO {cfg.current_data['db']['data_save']['table']} ({cfg.current_data['db']['data_save']['message_user']}, {cfg.current_data['db']['data_save']['message_response']}) VALUES (%s, %s)", [json.dumps(MessageUser), json.dumps(MessageAI)])