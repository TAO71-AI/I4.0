def GetTemplate(Prompt: str, SystemPrompt: str, Conversation: list[dict[str, str]], AllowsFiles: bool) -> str:
    conv = SystemPrompt + "\n"
    
    if (len(Conversation) > 0):
        conv += "### CONVERSATION:\n"

        for msg in Conversation:
            if (msg["role"] == "user"):
                conv += "User: "
            elif (msg["role"] == "assistant"):
                conv += "You: "
                
            if (len(msg["content"].strip()) > 0):
                if (AllowsFiles):
                    conv += str(msg["content"]) + "\n"
                else:
                    conv += msg["content"] + "\n"
        
    conv += "\n### USER: " + Prompt
    conv = conv.strip()

    return conv