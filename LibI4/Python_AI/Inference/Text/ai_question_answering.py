from transformers import AutoModelForQuestionAnswering, AutoTokenizer
import torch
import ai_config as cfg

model: AutoModelForQuestionAnswering | None = None
tokenizer: AutoTokenizer | None = None
device: str = "cpu"

def LoadModel() -> None:
    global model, tokenizer, device

    if (cfg.current_data["models"].count("qa") == 0):
        raise Exception("Model is not in 'models'.")

    if (model != None and tokenizer != None):
        return
    
    data = cfg.LoadModel("qa", cfg.current_data["qa_model"], AutoModelForQuestionAnswering, AutoTokenizer)

    model = data[0]
    tokenizer = data[1]
    device = data[2]

def ProcessPrompt(Context: str, Question: str) -> str:
    LoadModel()

    inputs = tokenizer(Question, Context, return_tensors = "pt")
    inputs = inputs.to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    asi = outputs.start_logits.argmax()
    aei = outputs.end_logits.argmax()

    outputs = inputs.input_ids[0, asi:aei + 1]
    answer = tokenizer.decode(outputs, skip_special_tokens = True)

    return str(answer)