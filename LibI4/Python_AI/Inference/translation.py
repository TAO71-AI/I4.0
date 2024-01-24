from transformers import AutoTokenizer, MarianMTModel, TFMarianMTModel
import torch
import ai_config as cfg

translation_tokenizer_1: AutoTokenizer = None
translation_model_1: MarianMTModel | TFMarianMTModel = None
device: str = "cpu"

models: dict[str, (MarianMTModel | TFMarianMTModel, AutoTokenizer)] = {}
models_loaded: bool = False

def __load_model__(model_name: str, device: str):
    if (cfg.current_data.use_tf_instead_of_pt):
        return TFMarianMTModel.from_pretrained(model_name)
    else:
        model = MarianMTModel.from_pretrained(model_name).to(device)
        return model

def LoadModels() -> None:
    global translation_model_1, translation_tokenizer_1, models, models_loaded, device

    if (not cfg.current_data.prompt_order.__contains__("tr")):
        raise Exception("Models are not in 'prompt_order'.")

    if (models_loaded):
        return

    move_to_gpu = cfg.current_data.use_gpu_if_available and torch.cuda.is_available() and cfg.current_data.move_to_gpu.__contains__("tr")
    device = "cuda" if (move_to_gpu) else "cpu"

    if (cfg.current_data.print_loading_message):
        print("Loading model 'translation' on device '" + device + "'...")

    if (translation_model_1 == None or translation_tokenizer_1 == None):
        translation_model_1 = __load_model__(cfg.current_data.translation_model_multiple, device)
        translation_tokenizer_1 = AutoTokenizer.from_pretrained(cfg.current_data.translation_model_multiple)
    
    for model in cfg.current_data.translation_models:
        name = cfg.current_data.translation_models[model]
        models[model] = (__load_model__(name, device), AutoTokenizer.from_pretrained(name))
    
    models_loaded = True

def Translate(prompt: str, tokenizer: AutoTokenizer, model: MarianMTModel | TFMarianMTModel) -> str:
    LoadModels()

    inputs = tokenizer.encode(prompt, return_tensors = ("tf" if cfg.current_data.use_tf_instead_of_pt else "pt"))

    if (not cfg.current_data.use_tf_instead_of_pt):
        inputs = inputs.to(device)

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