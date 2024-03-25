from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import emoji
import ai_config as cfg

translation_tokenizer_1: AutoTokenizer = None
translation_model_1: AutoModelForSeq2SeqLM = None
device: str = "cpu"

models: dict[str, (AutoModelForSeq2SeqLM, AutoTokenizer)] = {}
models_loaded: bool = False

def __load_model__(model_name: str, device: str):
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
    return model

def LoadModels() -> None:
    global translation_model_1, translation_tokenizer_1, models, models_loaded, device

    if (not cfg.current_data.prompt_order.__contains__("tr")):
        raise Exception("Models are not in 'prompt_order'.")

    if (models_loaded):
        return

    device = cfg.GetGPUDevice("tr")

    if (cfg.current_data.print_loading_message):
        print("Loading model 'translation' on device '" + device + "'...")

    if (translation_model_1 == None or translation_tokenizer_1 == None):
        translation_model_1 = __load_model__(cfg.current_data.translation_model_multiple, device)
        translation_tokenizer_1 = AutoTokenizer.from_pretrained(cfg.current_data.translation_model_multiple)
    
    for model in cfg.current_data.translation_models:
        name = cfg.current_data.translation_models[model]
        models[model] = (__load_model__(name, device), AutoTokenizer.from_pretrained(name))
    
    models_loaded = True

def Translate(prompt: str, tokenizer: AutoTokenizer, model: AutoModelForSeq2SeqLM) -> str:
    LoadModels()

    prompt = prompt.strip()
    prompt_noemoji = ""
    
    for character in prompt:
        if (emoji.is_emoji(character)):
            continue
            
        prompt_noemoji += character

    inputs = tokenizer.encode(prompt_noemoji, return_tensors = "pt")
    inputs = inputs.to(device)

    response = model.generate(inputs)
    decoded_response = tokenizer.batch_decode(response, skip_special_tokens = True)[0]

    decoded_response = str(decoded_response)
    return decoded_response

def TranslateFrom1To2(prompt: str) -> str:
    return Translate(prompt, translation_tokenizer_1, translation_model_1)

def TranslateFrom2To1(prompt: str, lang: str) -> str:
    try:
        return Translate(prompt, models[lang.lower()][1], models[lang.lower()][0])
    except:
        return prompt