import os

conversations: dict[str, str] = {}

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
            conversations[name] = f.read()
            f.close()
    except:
        pass

def SaveConversations() -> None:
    Init()
    convs = os.listdir("Conversations/")

    for conv in convs:
        if (os.path.isfile("Conversations/" + conv)):
            UpdateConversation(conv[0:conv.rfind(".")])

def SaveConversation(name: str) -> None:
    Init()

    try:
        with open("Conversations/" + name + ".txt", "w+") as f:
            f.write(conversations[name])
            f.close()
        
        UpdateConversation(name)
    except:
        pass

def GetAllConversations() -> list[str]:
    Init()
    convs = os.listdir("Conversations/")
    rconvs = []

    for conv in convs:
        if (os.path.isfile("Conversations/" + conv)):
            rconvs.append(GetConversation(conv[0:conv.rfind(".")]))
    
    return rconvs

def GetConversation(name: str) -> str:
    Init()
    UpdateConversation(name)

    try:
        return conversations[name]
    except:
        return ""

def SaveToConversation(name: str, data: str) -> None:
    Init()

    try:
        conv = conversations[name]
    except:
        conversations[name] = ""

    conversations[name] = conversations[name] + data
    SaveConversation(name)

Init()
UpdateConversations()