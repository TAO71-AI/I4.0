from transformers import Pipeline
import ai_config as cfg

__models__: dict[int, Pipeline] = {}

def LoadModels() -> None:
    # For each model in the config
    for i in range(len(cfg.GetAllInfosOfATask("sc"))):
        # Check if the model is already loaded
        if (i in list(__models__.keys())):
            # It is, continue
            continue

        # Get the model pipeline
        pipe, _ = cfg.LoadPipeline("text-classification", "sc", i)

        # Add the pipeline to the models list
        __models__[i] = pipe

def __offload_model__(Index: int) -> None:
    # Check the index is valid
    if (Index not in list(__models__.keys())):
        # Not valid, return
        return
    
    # Offload the model
    __models__[Index] = None
    
    # Delete from the models list
    __models__.pop(Index)

def Inference(Index: int, Prompt: str) -> str:
    # Load the models
    LoadModels()

    # Get a response from the model pipeline and get the label
    result = __models__[Index](Prompt)
    result = result[0]["label"]

    # Return the label as a string
    return str(result).lower()