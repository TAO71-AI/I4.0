# Import I4.0 utilities
from server_basics import ExecuteCommandOnDatabase, cfg

def GetResponse(Keywords: str | list[str]) -> list[str]:
    """
    Get a response from the dataset in the database.
    """
    # Make sure keywords is a list
    if (isinstance(Keywords, str)):
        Keywords = Keywords.split(" ")

    # Create SQL
    sql = f"SELECT {cfg.current_data['db']['dataset']['response']} FROM {cfg.current_data['db']['dataset']['table']} WHERE "
    sql += " AND ".join([f"{cfg.current_data['db']['dataset']['keywords']} LIKE %s" for _ in Keywords])

    # Make sure it doesn't ends in "AND"
    while (sql.endswith(" AND ")):
        sql = sql[:sql.rfind(" AND ")]

    # Execute the command on the server
    results = ExecuteCommandOnDatabase(sql, [f"%{k}%" for k in Keywords])
    resultsList = []

    # For each result
    for result in results:
        # Get the response
        response = str(result[cfg.current_data["db"]["dataset"]["response"]])

        # Append the response to the list
        resultsList.append(response)
    
    # Return the list
    return resultsList