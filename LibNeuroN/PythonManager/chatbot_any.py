from transformers import AutoModelForCausalLM, AutoTokenizer
import ai_config as cfg

model_name: str = cfg.ReadConfig().any_model
low_cpu_or_memory: bool = cfg.ReadConfig().low_cpu_or_memory
max_length = cfg.ReadConfig().max_length

model: AutoModelForCausalLM = None
tokenizer: AutoTokenizer = None

def LoadModel() -> None:
    global model, tokenizer

    if (model != None and tokenizer != None):
        return
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, low_cpu_mem_usage = low_cpu_or_memory, trust_remote_code = True)

def MakePrompt(prompt: str) -> str:
    LoadModel()

    input_ids = tokenizer.encode(prompt, return_tensors = "pt")
    output = model.generate(input_ids, max_length = max_length)
    response = tokenizer.decode(output[0], skip_special_tokens = True)

    return response