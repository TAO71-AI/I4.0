from transformers import pipeline, Pipeline
import torch
import ai_config as cfg
import ai_conversation as conv

model: Pipeline = None
system_messages: list[str] = []
device: str = "cpu"

def __load_model__(model_name: str, device: str):
    return pipeline(task = "text-generation", model = model_name, device = device)

def LoadModel() -> None:
    global model, device

    if (not cfg.current_data.prompt_order.__contains__("hf")):
        raise Exception("Model is not in 'prompt_order'.")

    if (model != None):
        return
    
    if (cfg.current_data.print_loading_message):
        print("Loading model 'chatbot (hf)' on device '" + device + "'...")
    
    move_to_gpu = torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("hf") and cfg.current_data.use_gpu_if_available
    device = "cuda" if (move_to_gpu) else "cpu"

    model = __load_model__(cfg.current_data.hf_model, device)

def MakePrompt(prompt: str, use_chat_history: bool = True, conversation_name: list[str] = ["", ""]) -> str:
    LoadModel()

    prompts = []
    sm = ""
    conver = ""

    for msg in system_messages:
        sm += msg + "\n"
    
    sm = sm.strip()
    prompts.append({"role": "system", "content": sm})
    
    try:
        conv_msgs = conv.GetConversation(conversation_name[0], conversation_name[1])

        if (use_chat_history and len(conv_msgs) > 0):
            for msg in conv_msgs:
                for role in msg:
                    prompts.append({"role": role, "content": msg[role]})
                    conver += "(" + role + ") " + msg[role] + "\n"
            
            conver = conver.strip()
    except:
        pass

    prompts.append({"role": "user", "content": prompt}) 

    if (cfg.current_data.print_prompt):
        print("### SYSTEM:\n" + sm + "\n\n### CONVERSATION:\n" + conver + "\n\n### USER: " + prompt + "\n### RESPONSE:")

    prompt_data = model.tokenizer.apply_chat_template(prompts, tokenize = False, add_generation_prompt = True)
    outputs = model(prompt_data, max_new_tokens = cfg.current_data.max_length, do_sample = True, temperature = cfg.current_data.temp)
    outputs = outputs[0]["generated_text"]
    response = outputs.replace(prompt_data, "")

    if (cfg.current_data.print_prompt):
        print(response)

    return "ERROR" if (len(response.strip()) < 1) else response.strip()