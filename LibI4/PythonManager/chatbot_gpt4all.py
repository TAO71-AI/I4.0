import gpt4all
import ai_config as cfg
import ai_conversation as conv

model_name: str = cfg.current_data.gpt4all_model
system_messages: list[str] = []
model: gpt4all.GPT4All = None

def LoadModel() -> None:
    global model

    if (len(model_name) <= 0 or model != None):
        return

    try:
        model = gpt4all.GPT4All(model_name = model_name)
    except Exception as ex:
        print("ERROR LOADING GPT4ALL MODEL: " + str(ex))

def MakePrompt(prompt: str, use_chat_history: bool = True, conversation_name: str = "server") -> str:
    global system_messages

    LoadModel()
    content_str = ""
    system_prompt = ""
    conversation = conv.GetConversation(conversation_name)
    
    if (len(system_messages) > 0):
        for i in system_messages:
            content_str += i + " "
            system_prompt += i + " "
        
        content_str += "\n"
    
    if (use_chat_history):
        if (len(conversation) > 0 and not conversation.endswith("\n")):
            conversation += "\n"

        content_str += "### ASSISTANT: \n" + conversation
    
    content_str += "### USER: " + prompt + "\n### RESPONSE: "

    if (cfg.current_data.print_prompt):
        print(content_str)
    
    if (use_chat_history):
        with model.chat_session(system_prompt, "### USER: {0}\n### RESPONSE: "):
            response = model.generate(prompt, max_tokens = cfg.current_data.max_length, temp = cfg.current_data.temp)
    else:
        response = model.generate(content_str, max_tokens = cfg.current_data.max_length, temp = cfg.current_data.temp)

    if (cfg.current_data.print_prompt):
        print(response)

    return "ERROR" if (len(response.strip()) < 1) else response.strip()