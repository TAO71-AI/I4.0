from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Pipeline
import emoji
import random
import ai_config as cfg

__models__: list[tuple[AutoModelForSeq2SeqLM, AutoTokenizer, str, dict[str, any]]] = []
__classifiers__: list[Pipeline] = []

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("tr"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            continue
        
        # Get the info of the model
        info = cfg.GetInfoOfTask("tr", i)

        # Check if contains a valid model
        if (info["lang"].count("-") != 1):
            # Return an error
            raise Exception(f"Invalid language for model {info["model"]}. Expected 'INPUT LANGUAGE-OUTPUT LANGUAGE'; got '{info["lang"]}'.")

        # Load the model
        model, tokenizer, device = cfg.LoadModel("tr", i, AutoModelForSeq2SeqLM, AutoTokenizer)

        # Add the model to the list of models
        __models__.append((model, tokenizer, device, info))

def LoadClassifiers() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("ld"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            continue
        
        # Load the model
        model, _ = cfg.LoadPipeline("text-classification", "ld", i)

        # Add the model to the list of models
        __classifiers__.append(model)

def GetAvailableLanguages() -> list[str]:
    # Create list
    langs = []

    # For each model
    for model in __models__:
        # Get the language and add it to the list
        langs.append(model[3]["lang"])
    
    # Return the list
    return langs

def InferenceModel(Index: int, Prompt: str) -> str:
    # Load the models
    LoadModels()

    # Strip and demojize the prompt
    Prompt = Prompt.strip()
    Prompt = emoji.demojize(Prompt, delimiters = (":", ":"), language = "alias")

    # Strip the prompt (for better translation)
    Prompt = Prompt.strip("\n")
    response = ""

    # Get the model to use
    model, tokenizer, device, _ = __models__[Index]

    # For each line
    for line in Prompt:
        # Check the length of the line
        if (len(line.strip()) == 0):
            # If the length of the stripped line is 0, add the line to the response and not translate
            response += line
            continue

        # Tokenize the line
        inputs = tokenizer.encode(line.strip(), return_tensors = "pt").to(device)

        # Generate the response
        translationResponse = model.generate(inputs)

        # Detokenize the response
        translationResponse = tokenizer.batch_decode(translationResponse, skip_special_tokens = True)[0]

        # Add it to the response
        response += str(translationResponse) + "\n"
    
    # Strip the response
    response = response.strip()

    # Emojize the response
    emoji.emojize(response, delimiters = (":", ":"), language = "alias")

    # Return the response
    return response

def InferenceClassifier(Prompt: str, Index: int = -1) -> str:
    # Load the classifiers
    LoadClassifiers()

    # Remove the emojis from the prompt and strip
    Prompt = "".join([p if (not emoji.is_emoji(p)) else "" for p in Prompt])
    Prompt = Prompt.strip()

    # Check the index of the classifier
    if (Index < 0):
        # Set the index of the classifier to a random classifier
        Index = random.randint(0, len(__classifiers__) - 1)
    
    # Inference the classifiers
    result = __classifiers__[Index](Prompt)

    # Get the label
    result = result[0]["label"]

    # Strip and lower the result
    result = result.strip().lower()

    # Check the result
    if (len(result) == 0):
        # The language is unknown
        return "unknown"

    # Return the label
    return result

def AutoTranslate(Prompt: str, InputLanguage: str = "unknown", OutputLanguage: str = "", IndexModel: int = 0, IndexClassifier: int = -1) -> str:
    # Strip and lower the languages
    InputLanguage = InputLanguage.lower().strip()
    OutputLanguage = OutputLanguage.lower().strip()

    # Check if the input language is the same as the output language
    if (InputLanguage == OutputLanguage):
        # It is, return the prompt
        return Prompt

    # Check the input language
    if (InputLanguage == "unknown" or len(InputLanguage) == 0):
        # The input language is unknown, use the classifier to detect the language
        InputLanguage = InferenceClassifier(Prompt, IndexClassifier)
    
    # Check the output language
    if (OutputLanguage == "unknown" or len(OutputLanguage) == 0):
        # Return an error
        raise Exception("Output language is unknown.")
    
    # Get the index of the model to use, considering the input and output languages
    # Create the models list
    models = []

    # For each model
    for model in __models__:
        # Get the info of the model
        info = model[3]

        # Check if the desired input and output languages are available
        if (info["lang"].lower().strip() == InputLanguage + "-" + OutputLanguage):
            # They are, add the model index to the list
            models.append(__models__.index(model))
    
    # Inference the model with the desired index and return the result
    return InferenceModel(models[IndexModel], Prompt)