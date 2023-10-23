from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import ai_config as cfg
import ai_conversation as conv

model_name: str = cfg.current_data.hf_model
low_cpu_or_memory: bool = cfg.current_data.low_cpu_or_memory
system_messages: list[str] = []
chat_history: list[str] = []
print_data: bool = False

model: AutoModelForCausalLM = None
tokenizer: AutoTokenizer = None

def LoadModel() -> None:
    global model, tokenizer

    if (model != None and tokenizer != None):
        return
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, low_cpu_mem_usage = low_cpu_or_memory, trust_remote_code = True)

    move_to_gpu = torch.cuda.is_available() and cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("3")
    device = "cuda" if (move_to_gpu) else "cpu"

    model = model.to(device)

def MakePrompt(prompt: str, use_chat_history: bool = True, conversation_name: str = "server") -> str:
    global print_data, system_messages, chat_history
    LoadModel()

    content = ""

    for smsg in system_messages:
        content += smsg + "\n"
    
    if (len(content.strip()) > 0):
        content += "\n"

    try:
        conv_msg = conv.ConversationToStr(conversation_name)

        if (use_chat_history and len(conv_msg.strip()) > 0):
            if (not conv_msg.endswith("\n")):
                conv_msg += "\n"

            content += "### CONVERSATION:\n" + conv_msg + "\n"
    except:
        pass
    
    content += "### USER: " + prompt + "\n### RESPONSE: "

    if (cfg.current_data.print_prompt):
        print(content)

    input_ids = tokenizer.encode(content, return_tensors = "pt", truncation = True)
    output = model.generate(input_ids, max_new_tokens = cfg.current_data.max_length)
    response = tokenizer.decode(output[0], skip_special_tokens = True)

    if (cfg.current_data.print_prompt):
        print(response)

    return response