from transformers import AutoTokenizer, AutoModelForSequenceClassification, TFAutoModelForSequenceClassification
import torch
import ai_config as cfg

model_name: str = cfg.current_data.text_classification_model

tokenizer: AutoTokenizer = None
model: AutoModelForSequenceClassification | TFAutoModelForSequenceClassification = None

def __load_model__(model_name: str, device: str):
    if (cfg.current_data.use_tf_instead_of_pt):
        return TFAutoModelForSequenceClassification.from_pretrained(model_name)
    else:
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        model.to(device)
        
        return model

def LoadModel() -> None:
    global tokenizer, model

    if ((tokenizer != None and model != None) or len(model_name.strip()) <= 0):
        return
    
    move_to_gpu = torch.cuda.is_available() and cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("sc")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'text classification' on device '" + device + "'...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = __load_model__(model_name, device)

def DoPrompt(prompt: str) -> str:
    LoadModel()

    if (tokenizer == None or model == None):
        return "-1"

    inputs = tokenizer.encode(prompt, return_tensors = ("tf" if cfg.current_data.use_tf_instead_of_pt else "pt"))
    response = model(inputs).logits
    predicted_class = response.argmax().item()

    return str(predicted_class)