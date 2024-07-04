from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Pipeline
import emoji
import ai_config as cfg

translation_classifier_model: Pipeline = None
device_classifier: str = "cpu"

models: dict[str, tuple[AutoModelForSeq2SeqLM, AutoTokenizer, str]] = {}
models_loaded: bool = False

def LoadModels() -> None:
    global translation_classifier_model, models, models_loaded, device_classifier

    if (not cfg.current_data["prompt_order"].__contains__("tr")):
        raise Exception("Models are not in 'prompt_order'.")

    if (models_loaded):
        return

    if (cfg.current_data["print_loading_message"]):
        print("Loading model 'translation (classifier)'...")

    if (translation_classifier_model == None):
        dataClassifier = cfg.LoadPipeline("text-classification", "tr", cfg.current_data["translation_classification_model"])

        translation_classifier_model = dataClassifier[0]
        device_classifier = dataClassifier[1]

    if (cfg.current_data["print_loading_message"]):
        print("   Loaded model on device '" + device_classifier + "'.")
    
    for model in cfg.current_data["translation_models"]:
        if (cfg.current_data["print_loading_message"]):
            print("Loading model 'translation (" + str(list(cfg.current_data["translation_models"].keys()).index(model)) + ")'...")
        
        name = cfg.current_data["translation_models"][model]
        data = cfg.LoadModel("tr", name, AutoModelForSeq2SeqLM, AutoTokenizer)

        models[model] = data

        if (cfg.current_data["print_loading_message"]):
            print("   Loaded model on device '" + data[2] + "'.")
    
    models_loaded = True

def GetAvailableLanguages() -> list[str]:
    return list(models.keys())

def __translate__(prompt: str, language: str, tokenizer: AutoTokenizer, model: AutoModelForSeq2SeqLM, device: str) -> str:
    LoadModels()

    if (cfg.current_data["print_prompt"]):
        print("Translating using '" + language + "'.")

    prompt = prompt.strip()
    prompt = emoji.demojize(prompt, delimiters = (";;", ";;"))

    inputs = tokenizer.encode(prompt, return_tensors = "pt")
    inputs = inputs.to(device)

    response = model.generate(inputs)
    decoded_response = tokenizer.batch_decode(response, skip_special_tokens = True)[0]

    decoded_response = str(decoded_response)
    decoded_response = emoji.emojize(decoded_response, delimiters = (";;", ";;"))

    return decoded_response

def Translate(prompt: str, language: str) -> str:
    LoadModels()

    if (language == cfg.current_data["server_language"] + "-" + cfg.current_data["server_language"]):
        return prompt

    availableLanguages = GetAvailableLanguages()

    if (availableLanguages.count(language) == 0):
        return prompt
    
    model = models[language][0]
    tokenizer = models[language][1]
    device = models[language][2]

    return __translate__(prompt, language, tokenizer, model, device)

def GetLanguage(prompt: str) -> str:
    LoadModels()

    prompt = prompt.strip()
    promptNoEmoji = ""

    for c in prompt:
        if (emoji.is_emoji(c)):
            continue

        promptNoEmoji += c
    
    promptNoEmoji = promptNoEmoji.strip()

    result = translation_classifier_model(promptNoEmoji)
    result = result[0]["label"]
    result = str(result).lower()

    if (len(result) == 0):
        return "UNKNOWN"

    return result

def TranslateToServerLanguage(prompt: str, language: str) -> str:
    return Translate(prompt, language + "-" + cfg.current_data["server_language"])

def TranslateFromServerLanguage(prompt: str, language: str) -> str:
    return Translate(prompt, cfg.current_data["server_language"] + "-" + language)