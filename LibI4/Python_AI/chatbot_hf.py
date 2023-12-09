from transformers import AutoModelForCausalLM, TFAutoModelForCausalLM, AutoTokenizer
import torch
import ai_config as cfg
import ai_conversation as conv

model_name: str = cfg.current_data.hf_model
low_cpu_or_memory: bool = cfg.current_data.low_cpu_or_memory
system_messages: list[str] = []
chat_history: list[str] = []
print_data: bool = False

model: AutoModelForCausalLM | TFAutoModelForCausalLM = None
tokenizer: AutoTokenizer = None

def __load_model__(model_name: str, device: str):
    if (cfg.current_data.use_tf_instead_of_pt):
        return TFAutoModelForCausalLM.from_pretrained(model_name)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_name)
        model.to(device)
        
        return model

def LoadModel() -> None:
    global model, tokenizer

    if (model != None and tokenizer != None):
        return
    
    move_to_gpu = torch.cuda.is_available() and cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("hf")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'chatbot (hf)' on device '" + device + "'...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = __load_model__(model_name, device)

def MakePrompt(prompt: str, use_chat_history: bool = True, conversation_name: list[str] = ["", ""]) -> str:
    global print_data, system_messages, chat_history
    LoadModel()

    content = ""
    sm = ""

    for smsg in system_messages:
        sm += smsg + "\n"
    
    content += sm
    
    if (len(content.strip()) > 0 and not content.endswith("\n")):
        content += "\n\n"
    elif (len(content.strip()) > 0 and content.endswith("\n")):
        content += "\n"

    try:
        conv_msg = conv.ConversationToStr(conversation_name[0], conversation_name[1])

        if (use_chat_history and len(conv_msg.strip()) > 0):
            if (not conv_msg.endswith("\n")):
                conv_msg += "\n"

            content += "### CONVERSATION:\n" + conv_msg + "\n"
    except:
        pass
    
    content += "### USER: " + prompt + "\n### RESPONSE: "

    if (cfg.current_data.print_prompt):
        print(content)

    input_ids = tokenizer.encode(content, return_tensors = ("tf" if cfg.current_data.use_tf_instead_of_pt else "pt"), truncation = True)
    output = model.generate(input_ids, max_new_tokens = cfg.current_data.max_length)
    response = tokenizer.decode(output[0], skip_special_tokens = True)

    if (cfg.current_data.print_prompt):
        print(response)

    return response