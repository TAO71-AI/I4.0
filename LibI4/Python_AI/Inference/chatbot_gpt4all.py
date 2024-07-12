import gpt4all
import ai_config as cfg
import ai_conversation as conv
import conversation_template as convTemp

model_name: str = cfg.current_data["gpt4all_model"]
system_messages: list[str] = []
model: gpt4all.GPT4All = None

def LoadModel() -> None:
    global model

    if (cfg.current_data["prompt_order"].count("g4a") == 0):
        raise Exception("Model is not in 'prompt_order'.")

    if (len(model_name) == 0 or model != None):
        return

    if (cfg.current_data["print_loading_message"]):
        print("Loading model 'chatbot (GPT4All)'...")

    device = "gpu" if (cfg.current_data["use_gpu_if_available"] and cfg.current_data["move_to_gpu"].count("g4a") > 0) else "cpu"
    model = gpt4all.GPT4All(model_name = model_name, device = device, allow_download = True)

    if (cfg.current_data["print_loading_message"]):
        print("   Loaded model on device '" + device + "'.")

def MakePrompt(prompt: str, use_chat_history: bool = True, conversation_name: list[str] = ["", ""]) -> str:
    global system_messages
    LoadModel()

    sm = ""
    content = ""

    for smsg in system_messages:
        sm += smsg + "\n"
        
    if (sm.endswith("\n")):
        sm = sm[:-1]

    content += convTemp.AutoGetConversation(prompt, "", conv.GetConversation(conversation_name[0], conversation_name[1]), use_chat_history)

    if (cfg.current_data["print_prompt"]):
        print(sm + "\n")
        print(content + "\n### RESPONSE: ")
    
    with model.chat_session(system_prompt = sm, prompt_template = "{0}\n### RESPONSE: "):
        response = model.generate(content, max_tokens = cfg.current_data["max_length"], temp = cfg.current_data["temp"], streaming = False)
    
    if (cfg.current_data["print_prompt"]):
        print(response)

    return "ERROR" if (len(response.strip()) < 1) else response.strip()