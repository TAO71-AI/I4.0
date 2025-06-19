# Import I4.0's utilities
import Inference.PredefinedModels.models as models

# Import other libraries
from huggingface_hub import hf_hub_download

def __parse_custom_model__(Model: list[str] | tuple[str, str] | str, Download: bool) -> str | tuple[str, str]:
    # Get model from the config
    repo = ""

    if (isinstance(Model, str)):
        if (Model.count(":") > 0):
            # Split the model string
            model = Model.split(":")
            repo = model[0]
            model = model[1]
        else:
            model = Model
    elif (isinstance(Model, list) or isinstance(Model, tuple)):
        repo = Model[0]
        model = Model[1]
    else:
        raise ValueError("CHATBOT_PARSE_ERR: Invalid model type. Must be a string or a list.")
    
    # Download everything
    if (Download and len(repo.strip()) > 0):
        modelPath = hf_hub_download(repo, model)
    else:
        modelPath = (repo, model)

    # Model is expected to be: "Model file path" or "Model repository:Model file in the repository" or ["Model repository", "Model file in the repository"] or ["", "Model file path"]
    return modelPath

def __get_quantization_and_repo_from_dict__(Dict: dict[str, any], DesiredQuantization: str) -> str:
    # Get quantization
    if (list(Dict.keys()).count(DesiredQuantization) == 0):
        # Invalid quantization, set default
        quantization = Dict[Dict["default"]]

        # Check that the quantization exists
        if (list(Dict.keys()).count(quantization) == 0):
            # It doesn't exists
            raise ValueError(f"Invalid quantization '{DesiredQuantization}'; '{quantization}'. Available quantizations are: {[i for i in list(Dict.keys()) if (i != 'default')]}.")
    else:
        # Use the desired quantization
        quantization = Dict[DesiredQuantization]
    
    # Return the quantization and repository
    return quantization

def __parse_pretrained_model__(Name: str, ModelQuantization: str, Download: bool) -> str | tuple[str, str] | None:
    # Lower and strip the quantizations
    ModelQuantization = ModelQuantization.lower().strip()

    # Check if the model exists in the list
    if (Name not in list(models.Chatbot_NF_LCPP.keys())):
        return None
    
    # Model
    modelQ = __get_quantization_and_repo_from_dict__(models.Chatbot_NF_LCPP[Name]["model"], ModelQuantization)

    # Download everything
    if (Download):
        modelPath = hf_hub_download(models.Chatbot_NF_LCPP[Name]["repo"], modelQ)
    else:
        modelPath = (Name, modelQ)

    # Return the model
    return modelPath

def AutoParse(Model: list[str] | tuple[str, str] | str, Download: bool) -> str | tuple[str, str]:
    # Convert model to a valid string
    if (isinstance(Model, str)):
        model = Model.split(":")
    elif (isinstance(Model, list) or isinstance(Model, tuple)):
        model = [Model[0], Model[1]]
    else:
        raise ValueError("CHATBOT_PARSE_ERR: Invalid model type. Must be a string or a list.")

    # Check model length
    if (len(model) == 2):
        # Try to get the model from the pretrained
        model[0] = model[0].lower()
        parsedModel = __parse_pretrained_model__(model[0], model[1], Download)

        # Check if the model is not null
        if (parsedModel is None):
            # Try to get from custom
            parsedModel = __parse_custom_model__(Model, Download)
    else:
        # Try to get from custom
        parsedModel = __parse_custom_model__(Model, Download)
    
    # Return the parsed model
    return parsedModel