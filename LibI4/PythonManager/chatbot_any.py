from transformers import AutoModelForCausalLM, AutoTokenizer
import ai_config as cfg
import ai_conversation as conv

model_name: str = cfg.current_data.any_model
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

def MakePrompt(prompt: str, use_chat_history: bool = True, conversation_name: str = "server") -> str:
    global print_data, system_messages, chat_history

    LoadModel()
    content_str = ""
    conversation = conv.GetConversation(conversation_name)
    
    if (len(system_messages) > 0):
        for i in system_messages:
            content_str += i + " "
        
        content_str += "\n"
    
    if (len(conversation) > 0 and not conversation.endswith("\n")):
        conversation += "\n"
    
    if (use_chat_history):
        content_str += "### ASSISTANT: " + conversation

        for i in chat_history:
            content_str += i + " "
        
        content_str += "\n"
    
    content_str += "### USER: " + prompt + "\n### RESPONSE: "

    if (print_data):
        print(content_str)

    input_ids = tokenizer.encode(content_str, return_tensors = "pt", truncation = True)
    output = model.generate(input_ids, max_new_tokens = cfg.current_data.max_length)
    response = tokenizer.decode(output[0], skip_special_tokens = True)

    return response