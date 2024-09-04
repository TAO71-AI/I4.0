from transformers import AutoModelForQuestionAnswering, AutoTokenizer
import torch
import ai_config as cfg

__models__: list[tuple[AutoModelForQuestionAnswering, AutoTokenizer, str]] = []

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("qa"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            continue
        
        # Load the model and add it to the list of models
        model = cfg.LoadModel("qa", i, AutoModelForQuestionAnswering, AutoTokenizer)
        __models__.append(model)

def Inference(Index: int, Context: str, Question: str) -> str:
    # Load the models
    LoadModels()

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