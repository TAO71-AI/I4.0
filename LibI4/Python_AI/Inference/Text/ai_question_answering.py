from transformers import AutoModelForQuestionAnswering, AutoTokenizer
import torch
import ai_config as cfg

__models__: dict[int, tuple[AutoModelForQuestionAnswering, AutoTokenizer, str]] = {}

def __load_model__(Index: int) -> None:
    # Check if the model is already loaded
    if (Index in list(__models__.keys()) and __models__[Index] is not None):
        return
        
    # Load the model and add it to the list of models
    model, tokenizer, device = cfg.LoadModel("qa", Index, AutoModelForQuestionAnswering, AutoTokenizer)
    __models__[Index] = (model, tokenizer, device)

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("qa"))):
        __load_model__(i)

def __offload_model__(Index: int) -> None:
    # Check the index is valid
    if (Index not in list(__models__.keys()) or __models__[Index] is None):
        # Not valid, return
        return
    
    # Offload the model
    __models__[Index] = None
    
    # Delete from the models list
    __models__.pop(Index)

def Inference(Index: int, Context: str, Question: str) -> str:
    # Load the model
    __load_model__(Index)

    # Tokenize the question and context
    inputs = __models__[Index][1](Question, Context, return_tensors = "pt")
    inputs = inputs.to(__models__[Index][2])

    # Inference the model
    with torch.no_grad():
        outputs = __models__[Index][0](**inputs)

    asi = outputs.start_logits.argmax()
    aei = outputs.end_logits.argmax()

    # Get the answer (tokenized)
    outputs = inputs.input_ids[0, asi:aei + 1]

    # Decode the answer and return it
    answer = __models__[Index][1].decode(outputs, skip_special_tokens = True)
    return str(answer)