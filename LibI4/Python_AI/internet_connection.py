from bs4 import BeautifulSoup
from googlesearch import search
import requests
import ai_config as cfg

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

def ReadTextFromWebsite(URL: str) -> str:
    if (cfg.current_data["print_prompt"]):
        print("Reading a website from a URL...")
    
    response = requests.get(URL)

    if (response.status_code != 200):
        return ""
    
    bs = BeautifulSoup(response.content, "html.parser")
    text = __find_and_get_all_items__(bs, "span")
    text += __find_and_get_all_items__(bs, "p")
    
    return text

def Search(Prompt: str) -> list[str]:
    if (cfg.current_data["print_prompt"]):
        print("Searching on internet...")

    return search(Prompt, stop = 5)