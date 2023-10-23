import os
import json

conversations: dict[str, list[dict[str, str]]] = {}

def Init() -> None:
    if (not os.path.exists("Conversations/")):
        os.mkdir("Conversations/")

def UpdateConversations() -> None:
    Init()
    convs = os.listdir("Conversations/")

    for conv in convs:
        if (os.path.isfile("Conversations/" + conv)):
            UpdateConversation(conv[0:conv.rfind(".")])

def UpdateConversation(name: str) -> None:
    Init()

    try:
        with open("Conversations/" + name + ".txt", "r+") as f:
            try:
                conversations[name] = json.loads(f.read())
            except:
                conversations[name] = []

            f.close()
    except:
        pass

def SaveConversations() -> None:
    Init()
    convs = os.listdir("Conversations/")

    for conv in convs:
        if (os.path.isfile("Conversations/" + conv)):
            SaveConversation(conv[0:conv.rfind(".")])

def SaveConversation(name: str) -> None:
    Init()

    try:
        with open("Conversations/" + name + ".txt", "w+") as f:
            f.write(json.dumps(conversations[name]))
            f.close()
        
        UpdateConversation(name)
    except:
        pass

def GetAllConversations() -> list[list[dict[str, str]]]:
    Init()
    convs = os.listdir("Conversations/")
    rconvs = []

    for conv in convs:
        if (os.path.isfile("Conversations/" + conv)):
            rconvs.append(GetConversation(conv[0:conv.rfind(".")]))
    
    return rconvs

def GetConversation(name: str) -> list[dict[str, str]]:
    Init()
    UpdateConversation(name)

    try:
        return conversations[name]
    except:
        return []

def SaveToConversation(name: str, user: str, response: str) -> None:
    Init()

    if (list(conversations.keys()).count(name) == 0):
        conversations[name] = []
    
    conversations[name] += [
        {"role": "user", "content": user},
        {"role": "response", "content": response}
    ]
    SaveConversation(name)

def ConversationToStr(name: str) -> str:
    msg = ""
    conversation = GetConversation(name)

    for m in conversation:
        try:
            if (m["role"] == "user"):
                msg += "User: "
            else:
                msg += "Response: "
            
            msg += m["content"] + "\n"
        except:
            continue
    
    return msg

Init()
UpdateConversations()