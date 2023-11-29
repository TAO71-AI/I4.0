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

    device = "gpu" if cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("g4a") else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'chatbot (GPT4All)' on device '" + device + "'...")

    model = gpt4all.GPT4All(model_name = model_name, device = device, allow_download = True)

def MakePrompt(prompt: str, use_chat_history: bool = True, conversation_name: str = "server") -> str:
    global system_messages
    LoadModel()

    sm = ""
    content = ""

    for smsg in system_messages:
        sm += smsg + "\n"
    
    if (sm.endswith("\n")):
        sm = sm[:-1]

    try:
        conv_msg = conv.ConversationToStr(conversation_name)

        if (use_chat_history and len(conv_msg.strip()) > 0):
            if (not conv_msg.endswith("\n")):
                conv_msg += "\n"

            content += "### CONVERSATION:\n" + conv_msg + "\n"
    except:
        pass
    
    content += "### USER: " + prompt

    if (cfg.current_data.print_prompt):
        print(sm + "\n")
        print(content + "\n### RESPONSE: ")
    
    with model.chat_session(sm, "{0}\n### RESPONSE: "):
        response = model.generate(content, max_tokens = cfg.current_data.max_length, temp = cfg.current_data.temp)
    
    if (cfg.current_data.print_prompt):
        print(response)

    return "ERROR" if (len(response.strip()) < 1) else response.strip()