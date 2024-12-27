# Import libraries
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException
import requests
import json

def __find_and_get_all_items__(BSContent: BeautifulSoup, Item: str) -> str:
    # Find all the items of the specified type
    data = BSContent.findAll(Item)
    text = ""

    try:
        # For each item
        for d in data:
            # Try to extract the text and add it to the text
            text += str(d.text) + "\n"
        
        # Return the text
        return text.strip()
    except:
        try:
            # For each item
            for d in data:
                # Try to convert the text to str
                text += str(d) + "\n"
            
            # Return the text
            return text.strip()
        except:
            # Return an empty string
            return ""

def __apply_limit_to_text__(Text: str, Limit: int, RemoveUnderLength: int = 0) -> str:
    # Create text
    text = ""

    # For each line in the text
    for line in Text.split("\n"):
        # Check if the length of the line is less than the minimum length
        if (len(line.strip()) < RemoveUnderLength):
            # It is, continue
            continue

        # Add the line to the text
        text += line.strip() + "\n"

    # Check if the limit is more than 0
    if (Limit > 0):
        # It is, limit the text
        text = text[:Limit]
        
        # Limit the text to the last dot
        if (text.count(".") > 0):
            text = text[:text.rfind(".") + 1]
    
    # Return the text
    return text

def ReadTextFromWebsite(URL: str, Limit: int = 0, RemoveUnderLength: int = 0) -> str:
    # Open the website
    print(f"Reading website {URL} with the limit of {Limit}.")
    response = requests.get(URL)

    # Check if the website was successfully opened
    if (response.status_code != 200):
        # It wasn't, return an empty string
        return ""
    
    # Parse the website content, get the text and apply the limit
    bs = BeautifulSoup(response.content, "html.parser")
    text = __find_and_get_all_items__(bs, "span")
    text += __find_and_get_all_items__(bs, "p")
    text = __apply_limit_to_text__(text, Limit, RemoveUnderLength)

    # Return the text
    return text.strip()

def Search__Websites(Prompt: str, MaxResults: int) -> list[str]:
    # Create results list
    results = []

    try:
        # Try to search the prompt using the API
        searchResults = DDGS().text(Prompt, max_results = MaxResults)
    except RatelimitException:
        # Rate limit error, try again using DuckDuckGoLite
        searchResults = DDGS().text(Prompt, max_results = MaxResults, backend = "lite")

    # For each result
    for result in searchResults:
        # Append the result URL to the results list
        results.append(result["href"])
    
    # Return the results list
    return results

def Search__News(Prompt: str, MaxResults: int) -> list[str]:
    # Search the prompt in DuckDuckGo (news) and create the results list
    searchResults = DDGS().news(Prompt, max_results = MaxResults)
    results = []
    
    # For each result
    for result in searchResults:
        # Append the result text to the results list
        results.append(f"NEWS #{searchResults.index(result) + 1}:\n> Title: {result['title']}\n> Body: {result['body']}\n> Source: {result['source']}")
    
    # Return the results list
    return results

def Search__Chat(Prompt: str, Model: str) -> str:
    # Check the model
    availableModels = [
        "gpt-4o-mini",      # Not Open-Source
        "claude-3-haiku",   # Not Open-Source
        "llama-3.1-70b",    # Open-Source
        "mixtral-8x7b"      # Open-Source
    ]

    if (Model not in availableModels):
        # Invalid model, print and use mixtral-8x7b
        print(f"Invalid model. Available models are: {', '.join(availableModels)[2:-2]}.\nUsing Mixtral-8x7B.")
        Model = "mixtral-8x7b"

    # Use a chatbot from DuckDuckGo
    response = DDGS().chat(Prompt, Model)

    # Return the chatbot response
    return response

def Search__Maps(Prompt: str, Radius: int, MaxResults: int) -> list[str]:
    # Search the prompt in DuckDuckGo (maps) and create the results list
    try:
        searchResults = DDGS().maps(Prompt, max_results = MaxResults, radius = Radius)
    except Exception as ex:
        print("Error obtaining map. Returning empty list.")
        return []

    results = []

    # Check the length of the results
    if (len(searchResults) == 0):
        # Return empty list
        return []
    
    # For each result
    for result in searchResults:
        # Append the result text to the results list
        results.append(f"LOCATION #{searchResults.index(result) + 1}:\n> Details: {json.dumps(result)}")
    
    # Return the results list
    return results