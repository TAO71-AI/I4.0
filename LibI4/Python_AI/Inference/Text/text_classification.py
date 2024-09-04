from transformers import Pipeline
import ai_config as cfg

__models__: list[Pipeline] = []

def LoadModels() -> None:
    # For each model in the config
    for i in range(len(cfg.GetAllInfosOfATask("sc"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            # It is, continue
            continue

        # Get the model pipeline
        pipe, _ = cfg.LoadPipeline("text-classification", "sc", i)

        # Add the pipeline to the models list
        __models__.append(pipe)

def Inference(Index: int, Prompt: str) -> str:
    # Load the models
    LoadModels()

    # Get a response from the model pipeline and get the label
    result = __models__[Index](Prompt)
    result = result[0]["label"]

    # Return the label as a string
    return str(result).lower()