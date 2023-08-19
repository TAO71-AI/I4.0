from transformers import AutoTokenizer, AutoModelForSequenceClassification
import ai_config as cfg

model_name: str = cfg.current_data.text_classification_model

tokenizer: AutoTokenizer = None
model: AutoModelForSequenceClassification = None

def LoadModel() -> None:
    global tokenizer, model

    if ((tokenizer != None and model != None) or len(model_name.strip()) <= 0):
        return
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

def DoPrompt(prompt: str) -> str:
    LoadModel()

    if (tokenizer == None or model == None):
        return "-1"

    inputs = tokenizer.encode(prompt, return_tensors = "pt")
    response = model(inputs).logits
    predicted_class = response.argmax().item()

    return str(predicted_class)