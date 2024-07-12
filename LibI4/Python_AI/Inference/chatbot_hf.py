"""
This chatbot is not deprecated, but we do not recommend to use it. Please use the GPT4All (g4a) chatbot, usually it gives better responses and it's more tested.

THIS CHATBOT IS NOW DEPRECATED, IT MIGHT BE REMOVED IN THE FUTURE AND IT WILL NOT BE UPDATED FROM NOW ON.
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
import ai_config as cfg
import ai_conversation as conv

model: AutoModelForCausalLM = None
tokenizer: AutoTokenizer = None
system_messages: list[str] = []
device: str = "cpu"

def LoadModel() -> None:
    global model, tokenizer, device

    if (not cfg.current_data["prompt_order"].__contains__("hf")):
        raise Exception("Model is not in 'prompt_order'.")

    if (model != None and tokenizer != None):
        return
    
    if (cfg.current_data["print_loading_message"]):
        print("Loading model 'chatbot (hf)'...")
    
    data = cfg.LoadModel("hf", cfg.current_data["hf_model"], AutoModelForCausalLM, AutoTokenizer)

    model = data[0]
    tokenizer = data[1]
    device = data[2]

    if (cfg.current_data["print_loading_message"]):
        print("   Loaded model on device '" + device + "'.")

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

    if (cfg.current_data["print_prompt"]):
        print("### SYSTEM:\n" + sm + "\n\n### CONVERSATION:\n" + conver + "\n\n### USER: " + prompt + "\n### RESPONSE:")

    prompt_data = tokenizer.apply_chat_template(prompts, return_tensors = "pt")
    prompt_data = prompt_data.to(device)

    outputs = model.generate(prompt_data, max_new_tokens = cfg.current_data["max_length"], do_sample = True, temperature = cfg.current_data["temp"])
    outputs = tokenizer.batch_decode(outputs)[0]
    response = outputs.replace(prompt_data, "")

    if (cfg.current_data["print_prompt"]):
        print(response)

    return "ERROR" if (len(response.strip()) < 1) else response.strip()