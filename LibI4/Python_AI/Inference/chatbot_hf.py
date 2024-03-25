from transformers import AutoModelForCausalLM, AutoTokenizer
import ai_config as cfg
import ai_conversation as conv

model: AutoModelForCausalLM = None
tokenizer: AutoTokenizer = None

system_messages: list[str] = []
device: str = "cpu"

def __load_model__(model_name: str, device: str) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    m = AutoModelForCausalLM.from_pretrained(model_name).to(device)
    t = AutoTokenizer.from_pretrained(model_name)

    return (m, t)

def LoadModel() -> None:
    global model, tokenizer, device

    if (not cfg.current_data.prompt_order.__contains__("hf")):
        raise Exception("Model is not in 'prompt_order'.")

    if (model != None and tokenizer != None):
        return
    
    if (cfg.current_data.print_loading_message):
        print("Loading model 'chatbot (hf)' on device '" + device + "'...")
    
    device = cfg.GetGPUDevice("hf")
    model, tokenizer = __load_model__(cfg.current_data.hf_model, device)

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

    prompt_data = tokenizer.apply_chat_template(prompts, return_tensors = "pt")
    prompt_data = prompt_data.to(device)

    outputs = model.generate(prompt_data, max_new_tokens = cfg.current_data.max_length, do_sample = True, temperature = cfg.current_data.temp)
    outputs = tokenizer.batch_decode(outputs)[0]
    response = outputs.replace(prompt_data, "")

    if (cfg.current_data.print_prompt):
        print(response)

    return "ERROR" if (len(response.strip()) < 1) else response.strip()