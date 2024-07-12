import ai_config as cfg

def __get_old_template__(Prompt: str, SystemPrompt: str, Conversation: list[dict[str, str]], UseConversation: bool) -> str:
    conv = SystemPrompt + "\n"

    if (UseConversation):
        conv += "### CONVERSATION:\n"

        for msg in Conversation:
            if (msg["role"] == "user"):
                conv += "User: "
            elif (msg["role"] == "assistant"):
                conv += "Response: "
            
            conv += msg["content"] + "\n"
        
    conv += "### USER: " + Prompt
    conv = conv.strip()

    return conv

def __get_new_template__(Prompt: str, SystemPrompt: str, Conversation: list[dict[str, str]], UseConversation: bool) -> str:
    conv = SystemPrompt + "\n"

    if (UseConversation):
        conv += "### CONVERSATION:\n"

        for msg in Conversation:
            if (msg["role"] == "user"):
                conv += "User: "
            elif (msg["role"] == "assistant"):
                conv += "You: "
            elif (msg["role"] == "thinking" and cfg.current_data["allow_thinking"]):
                conv += "You (thinking): "
            
            if (len(msg["content"].strip()) > 0):
                conv += msg["content"] + "\n"
        
    conv += "### USER: " + Prompt
    conv = conv.strip()

    return conv

def AutoGetConversation(Prompt: str, SystemPrompt: str, Conversation: list[dict[str, str]], UseConversation: bool) -> str:
    if (cfg.current_data["use_new_conversation_template"]):
        return __get_new_template__(Prompt, SystemPrompt, Conversation, UseConversation)
    
    return __get_old_template__(Prompt, SystemPrompt, Conversation, UseConversation)