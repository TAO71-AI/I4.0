from transformers import Pipeline
import ai_config as cfg

model_name: str = cfg.current_data["text_classification_model"]

pipe: Pipeline = None
device: str = "cpu"

def LoadModel() -> None:
    global pipe, device

    if (not cfg.current_data["prompt_order"].__contains__("sc")):
        raise Exception("Model is not in 'prompt_order'.")

    if (pipe != None or len(model_name.strip()) == 0):
        return

    if (cfg.current_data["print_loading_message"]):
        print("Loading model 'text classification'...")

    data = cfg.LoadPipeline("text-classification", "sc", cfg.current_data["text_classification_model"])

    pipe = data[0]
    device = data[1]

    if (cfg.current_data["print_loading_message"]):
        print("   Loaded model on device '" + device + "'.")

def DoPrompt(prompt: str) -> str:
    LoadModel()

    if (pipe == None):
        return "-1"

    result = pipe(prompt)
    result = result[0]["label"]

    return str(result).lower()