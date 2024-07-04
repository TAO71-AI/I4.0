from transformers import AutoModelForQuestionAnswering, AutoTokenizer
import torch
import ai_config as cfg

model: AutoModelForQuestionAnswering = None
tokenizer: AutoTokenizer = None
device: str = "cpu"

def LoadModel() -> None:
    global model, tokenizer, device

    if (not cfg.current_data["prompt_order"].__contains__("qa")):
        raise Exception("Model is not in 'prompt_order'.")

    if (model != None and tokenizer != None):
        return
    
    if (cfg.current_data["print_loading_message"]):
        print("Loading model 'question answering'...")
    
    data = cfg.LoadModel("qa", cfg.current_data["qa_model"], AutoModelForQuestionAnswering, AutoTokenizer)

    model = data[0]
    tokenizer = data[1]
    device = data[2]

    if (cfg.current_data["print_loading_message"]):
        print("   Loaded model on device '" + device + "'.")

def ProcessPrompt(Context: str, Question: str) -> str:
    LoadModel()

    if (cfg.current_data["print_prompt"]):
        print("Processing with Question Answering...\n\nContext:\n" + Context + "\n\nQuestion:\n" + Question)

    inputs = tokenizer(Question, Context, return_tensors = "pt")
    inputs = inputs.to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    asi = outputs.start_logits.argmax()
    aei = outputs.end_logits.argmax()

    outputs = inputs.input_ids[0, asi:aei + 1]
    answer = tokenizer.decode(outputs, skip_special_tokens = True)

    if (cfg.current_data["print_prompt"]):
        print("Response: " + answer)

    return str(answer)