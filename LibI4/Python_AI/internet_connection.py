# Import libraries
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import requests

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
    # Search the prompt in DuckDuckGo
    searchResults = DDGS().text(Prompt, max_results = MaxResults)
    results = []

    # For each result
    for result in searchResults:
        # Append the result URL to the results list
        results.append(result["href"])
    
    # Return the results list
    return results

def Search__Answers(Prompt: str, MaxResults: int) -> list[str]:
    # Search the prompt in DuckDuckGo
    searchResults = DDGS().answers(Prompt)
    results = []

    # Check length
    if (len(searchResults) > MaxResults):
        # Limit the results
        searchResults = searchResults[:MaxResults]
    
    # For each result
    for result in searchResults:
        # Append the result text to the results list
        results.append(f"ANSWER #{searchResults.index(result) + 1}:\n> Text: {result['text']}\n> Source: {result['url']}")
    
    # Return the results list
    return results

def Search__News(Prompt: str, MaxResults: int) -> list[str]:
    # Search the prompt in DuckDuckGo
    searchResults = DDGS().news(Prompt, max_results = MaxResults)
    results = []
    
    # For each result
    for result in searchResults:
        # Append the result text to the results list
        results.append(f"NEWS #{searchResults.index(result) + 1}:\n> Title: {result['title']}\n> Body: {result['body']}\n> Source: {result['source']}")
    
    # Return the results list
    return results