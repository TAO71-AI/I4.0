from transformers import Pipeline
import ai_config as cfg

model_name: str = cfg.current_data["text_classification_model"]
pipe: Pipeline | None = None
device: str = "cpu"

def LoadModel() -> None:
    global pipe, device

    if (cfg.current_data["models"].count("sc") == 0):
        raise Exception("Model is not in 'models'.")

    if (pipe != None or len(model_name.strip()) == 0):
        return

    data = cfg.LoadPipeline("text-classification", "sc", cfg.current_data["text_classification_model"])

    pipe = data[0]
    device = data[1]

def DoPrompt(prompt: str) -> str:
    LoadModel()

    if (pipe == None):
        return "-1"

    result = pipe(prompt)
    result = result[0]["label"]

    return str(result).lower()