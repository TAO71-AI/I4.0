from bs4 import BeautifulSoup
from googlesearch import search
import requests

def __find_and_get_all_items__(BSContent: BeautifulSoup, Item: str) -> str:
    data = BSContent.findAll(Item)
    text = ""

    try:
        for d in data:
            text += str(d.text) + "\n"
        
        return text.strip()
    except:
        try:
            for d in data:
                text += str(d) + "\n"
            
            return text.strip()
        except:
            return ""

def __apply_limit_to_text__(Text: str, Limit: int, RemoveUnderLength: int = 0) -> str:
    for line in Text.split("\n"):
        if (len(line.strip()) < RemoveUnderLength):
            Text = Text.replace(line, "")
    
    while (Text.count("\n\n") > 0):
        Text = Text.replace("\n\n", "\n")

    if (Limit > 0):
        Text = Text[:Limit]
        
        if (Text.count(".") > 0):
            Text = Text[:Text.rfind(".") + 1]
    
    return Text

def ReadTextFromWebsite(URL: str, Limit: int = 0, RemoveUnderLength: int = 0) -> str:
    print(f"Reading website {URL} with the limit of {Limit}.")
    response = requests.get(URL)

    if (response.status_code != 200):
        return ""
    
    bs = BeautifulSoup(response.content, "html.parser")
    text = __find_and_get_all_items__(bs, "span")
    text += __find_and_get_all_items__(bs, "p")
    text = __apply_limit_to_text__(text, Limit, RemoveUnderLength)

    return text

def Search(Prompt: str, MaxResults: int) -> list[str]:
    return search(Prompt, stop = MaxResults)