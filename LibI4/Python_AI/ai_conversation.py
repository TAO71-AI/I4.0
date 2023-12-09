import os
import json

conversations: dict[str, dict[str, list[dict[str, str]]]] = {}

def __filter_name__(Name: str) -> str:
    if (len(Name.strip()) == 0):
        return "none"
    
    return Name

def Init() -> None:
    if (not os.path.exists("Conversations/")):
        os.mkdir("Conversations/")

def CreateConversation(Name: str, Conv: str) -> None:
    Name = __filter_name__(Name)
    Conv = __filter_name__(Conv)

    if (list(conversations.keys()).count(Name) == 0):
        conversations[Name] = {}
    
    if (list(conversations[Name].keys()).count(Conv) == 0):
        conversations[Name][Conv] = []

def GetConversation(Name: str, ConvName: str) -> list[dict[str, str]]:
    Name = __filter_name__(Name)
    ConvName = __filter_name__(ConvName)

    CreateConversation(Name, ConvName)
    return conversations[Name][ConvName]

def ClearConversation(Name: str, Conv: str) -> None:
    Name = __filter_name__(Name)
    Conv = __filter_name__(Conv)

    CreateConversation(Name, Conv)
    conversations[Name][Conv] = []
    SaveConversation(Name)

def SaveConversations() -> None:
    for conv in list(conversations.keys()):
        SaveConversation(conv)

def SaveConversation(Name: str) -> None:
    Init()

    with open("Conversations/" + Name + ".txt", "w+") as f:
        f.write(json.dumps(conversations[Name]))
        f.close()

    UpdateConversation(Name)

def AddToConversation(Name: str, Conv: str, User: str, Response: str) -> None:
    Name = __filter_name__(Name)
    Conv = __filter_name__(Conv)

    CreateConversation(Name, Conv)

    conversations[Name][Conv].append({"role": "user", "content": User})
    conversations[Name][Conv].append({"role": "assistant", "content": Response})

    SaveConversation(Name)

def UpdateConversations() -> None:
    for conv in os.listdir("Conversations/"):
        UpdateConversation(conv[0:conv.rfind(".")])

def UpdateConversation(Name: str) -> None:
    Init()

    Name = __filter_name__(Name)

    for conv in os.listdir("Conversations/"):
        if (conv[0:conv.rfind(".")] == Name):
            with open("Conversations/" + conv, "r") as f:
                conversations[Name] = json.loads(f.read())
                f.close()

def ConversationToStr(Name: str, Conv: str) -> str:
    Name = __filter_name__(Name)
    Conv = __filter_name__(Conv)

    msg = ""
    conversation = GetConversation(Name, Conv)

    for m in conversation:
        try:
            if (m["role"] == "user"):
                msg += "User: "
            else:
                msg += "Response: "
            
            msg += m["content"] + "\n"
        except Exception as ex:
            print("ERROR IN CONVERSATION TO STR: " + str(ex))
            continue
    
    return msg

Init()
UpdateConversations()