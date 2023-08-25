from transformers import AutoTokenizer, MarianMTModel
import ai_config as cfg

translation_tokenizer_1: AutoTokenizer = None
translation_model_1: MarianMTModel = None

models: dict[str, (MarianMTModel, AutoTokenizer)] = {}

def LoadModels() -> None:
    global translation_model_1, translation_tokenizer_1, models

    if (translation_model_1 == None or translation_tokenizer_1 == None):
        translation_model_1 = MarianMTModel.from_pretrained(cfg.current_data.translation_model_multiple)
        translation_tokenizer_1 = AutoTokenizer.from_pretrained(cfg.current_data.translation_model_multiple)
    
    for model in cfg.current_data.translation_models:
        name = cfg.current_data.translation_models[model]
        models[model] = (MarianMTModel.from_pretrained(name), AutoTokenizer.from_pretrained(name))

def Translate(prompt: str, tokenizer: AutoTokenizer, model: MarianMTModel) -> str:
    LoadModels()

    inputs = tokenizer.encode(prompt, return_tensors = "pt")
    response = model.generate(inputs)
    decoded_response = tokenizer.batch_decode(response, skip_special_tokens = True)[0]

    return decoded_response

def TranslateFrom1To2(prompt: str) -> str:
    return Translate(prompt, translation_tokenizer_1, translation_model_1)

def TranslateFrom2To1(prompt: str, lang: str) -> str:
    try:
        return Translate(prompt, models[lang.lower()][1], models[lang.lower()][0])
    except:
        return prompt