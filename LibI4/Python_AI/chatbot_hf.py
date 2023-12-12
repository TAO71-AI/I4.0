from transformers import AutoModelForCausalLM, TFAutoModelForCausalLM, AutoTokenizer
import torch
import ai_config as cfg
import ai_conversation as conv

model: AutoModelForCausalLM | TFAutoModelForCausalLM = None
tokenizer: AutoTokenizer = None
system_messages: list[str] = []
device: str = "cpu"

def __load_model__(model_name: str, device: str):
    if (cfg.current_data.use_tf_instead_of_pt):
        return TFAutoModelForCausalLM.from_pretrained(model_name)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
        return model

def LoadModel() -> None:
    global model, tokenizer, device

    if (model != None and tokenizer != None):
        return
    
    if (cfg.current_data.print_loading_message):
        print("Loading model 'chatbot (hf)' on device '" + device + "'...")
    
    move_to_gpu = torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("hf") and cfg.current_data.use_gpu_if_available
    device = "cuda" if (move_to_gpu) else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(cfg.current_data.hf_model)
    model = __load_model__(cfg.current_data.hf_model, device)

def MakePrompt(prompt: str, use_chat_history: bool = True, conversation_name: list[str] = ["", ""]) -> str:
    if (model == None or tokenizer == None):
        LoadModel()
    
    prompt_str = ""

    for msg in system_messages:
        prompt_str += msg + "\n"
    
    if (len(msg.split()) > 0):
        prompt_str += "\n"
    
    try:
        conv_msg = conv.ConversationToStr(conversation_name[0], conversation_name[1])

        if (use_chat_history and len(conv_msg.strip()) > 0):
            if (not conv_msg.endswith("\n")):
                conv_msg += "\n"

            prompt_str += "### CONVERSATION:\n" + conv_msg + "\n"
    except:
        pass

    prompt_str += "### USER: " + prompt + "\n### RESPONSE: "    

    if (cfg.current_data.print_prompt):
        print(prompt_str)

    user_input_ids = tokenizer.encode(prompt_str, return_tensors = "tf" if (cfg.current_data.use_tf_instead_of_pt) else "pt")

    if (not cfg.current_data.use_tf_instead_of_pt):
        user_input_ids = user_input_ids.to(device)

    with torch.no_grad():
        response = model.generate(user_input_ids, max_new_tokens = cfg.current_data.max_length, temperature = cfg.current_data.temp, do_sample = True)
    
    response = tokenizer.batch_decode(response)[0]
    response = response.replace(prompt_str, "")

    if (cfg.current_data.print_prompt):
        print(response)

    return "ERROR" if (len(response.strip()) < 1) else response.strip()