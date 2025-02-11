from transformers import Pipeline
import ai_config as cfg

__models__: dict[int, Pipeline] = {}

def __load_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models__.keys())):
        return

    # Get the model pipeline
    pipe, _ = cfg.LoadPipeline("text-classification", "sc", Index)

    # Add the pipeline to the models list
    __models__[Index] = pipe

def LoadModels() -> None:
    # For each model in the config
    for i in range(len(cfg.GetAllInfosOfATask("sc"))):
        __load_model__(i)

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
    # Load the model
    __load_model__(Index)

    # Get a response from the model pipeline and get the label
    result = __models__[Index](Prompt)
    result = result[0]["label"]

    # Return the label as a string
    return str(result).lower()