import os
import json

class ConfigData:
    gpt4all_model: str = "ggml-gpt4all-j-v1.3-groovy"
    any_model: str = "gpt2"
    text_classification_model: str = "nlptown/bert-base-multilingual-uncased-sentiment"
    translation_model_multiple: str = "Helsinki-NLP/opus-mt-mul-en"
    translation_models: dict[str, str] = {
        "spanish": "Helsinki-NLP/opus-mt-en-es"
    }
    whisper_model: str = "tiny"
    tf_data_file: str = "tf_train_data_es.txt"
    openai_model: str = "gpt-3.5-turbo"
    internet_model: str = "facebook/bart-large-cnn"
    image_generation_model: str = "deepghs/animefull-latest"
    tf_epochs: int = 100
    force_api_key: bool = True
    cb_tf_version: int = 1
    low_cpu_or_memory: bool = False
    max_length: int = 1000
    use_chat_history: bool = True
    use_dynamic_system_args: bool = True
    prompt_order: str = "540367128"
    use_gpu_if_available: bool = True
    ai_args: str = "+self-aware"
    custom_system_messages: str = ""
    system_messages_in_first_person: bool = False
    use_default_system_messages: bool = True
    welcome_message: str = ""
    temp: float = 0.5
    save_conversations: bool = True
    keys_db: dict[str, str] = {
        "use": "false",
        "server": "127.0.0.1",
        "user": "root",
        "password": "",
        "database": "",
        "table": "keys"
    }
    print_prompt: bool = False

def Init():
    if (not os.path.exists("config.tcfg")):
        with open("config.tcfg", "w+") as f:
            f.close()

def ReadConfig() -> ConfigData:
    Init()
    data = ConfigData()

    with open("config.tcfg", "r") as f:
        config_dict: dict[str, str] = {}

        for line in f.readlines():
            if (not line.__contains__("=")):
                continue

            try:
                key = line[0:line.index("=")]
                value = line[line.index("=") + 1:len(line)]
            except:
                key = ""
                value = line

            config_dict[key] = value.strip().replace("\n", "")
        
        for i in config_dict:
            il = i.lower()

            if (il == "gpt4all_model"):
                data.gpt4all_model = config_dict[i]
            elif (il == "any_model"):
                data.any_model = config_dict[i]
            elif (il == "text_classification_model"):
                data.text_classification_model = config_dict[i]
            elif (il == "translation_model_mult"):
                data.translation_model_multiple = config_dict[i]
            elif (il == "translation_models"):
                try:
                    models = json.loads(config_dict[i])
                except Exception as ex:
                    models = {
                        "spanish": "Helsinki-NLP/opus-mt-en-es"
                    }
                
                for lang in models:
                    data.translation_models[lang.lower()] = models[lang]
            elif (il == "whisper_model"):
                data.whisper_model = config_dict[i]
            elif (il == "tf_data_file"):
                data.tf_data_file = config_dict[i]
            elif (il == "openai_model"):
                data.openai_model = config_dict[i]
            elif (il == "internet_model"):
                data.internet_model = config_dict[i]
            elif (il == "image_generation_model"):
                data.image_generation_model = config_dict[i]
            elif (il == "tf_epochs"):
                try:
                    data.tf_epochs = int(config_dict[i])
                except:
                    data.tf_epochs = 100
            elif (il == "force_api_key"):
                data.force_api_key = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "cb_tf_version"):
                try:
                    data.cb_tf_version = int(config_dict[i])
                except:
                    data.cb_tf_version = 1
            elif (il == "low_cpu_or_memory"):
                data.low_cpu_or_memory = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "max_length"):
                try:
                    data.max_length = int(config_dict[i])
                except:
                    data.max_length = 10000
            elif (il == "use_chat_history"):
                data.use_chat_history = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "use_dynamic_system_args"):
                data.use_dynamic_system_args = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "prompt_order"):
                data.prompt_order = config_dict[i]
            elif (il == "use_gpu"):
                data.use_gpu_if_available = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "ai_args"):
                data.ai_args = config_dict[i]
            elif (il == "custom_sys_msg"):
                data.custom_system_messages = config_dict[i]
            elif (il == "sys_msg_first_person"):
                data.system_messages_in_first_person = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "use_default_system_messages"):
                data.use_default_system_messages = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "welcome_message"):
                data.welcome_message = config_dict[i]
            elif (il == "temp"):
                try:
                    data.temp = int(config_dict[i])

                    if (data.temp < 0):
                        data.temp = 0
                    elif (data.temp > 1):
                        data.temp = 1
                except:
                    data.temp = 0.5
            elif (il == "save_conversations"):
                data.save_conversations = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "keys_db"):
                try:
                    kdb = json.loads(config_dict[i])
                    kdb_keys = list(kdb.keys())

                    if (kdb_keys.__contains__("use") and kdb_keys.__contains__("server") and kdb_keys.__contains__("user") and
                        kdb_keys.__contains__("password") and kdb_keys.__contains__("database") and kdb_keys.__contains__("table")):
                        data.keys_db = kdb
                except:
                    pass
            elif (il == "print_prompt"):
                data.print_prompt = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")

        f.close()
    
    return data

def SaveConfig(cfg: ConfigData = None) -> None:
    global current_data
    Init()

    if (cfg == None):
        cfg = current_data

        if (current_data == None):
            return
    
    text = ""

    text += "gpt4all_model=" + cfg.gpt4all_model + "\n"
    text += "any_model=" + cfg.any_model + "\n"
    text += "text_classification_model=" + cfg.text_classification_model + "\n"
    text += "translation_model_mult=" + cfg.translation_model_multiple + "\n"
    text += "translation_models=" + json.dumps(cfg.translation_models) + "\n"
    text += "whisper_model=" + cfg.whisper_model + "\n"
    text += "tf_data_file=" + cfg.tf_data_file + "\n"
    text += "openai_model=" + cfg.openai_model + "\n"
    text += "internet_model=" + cfg.internet_model + "\n"
    text += "tf_epochs=" + str(cfg.tf_epochs) + "\n"
    text += "force_api_key=" + ("true" if cfg.force_api_key == True else "false") + "\n"
    text += "cb_tf_version=" + str(cfg.cb_tf_version) + "\n"
    text += "low_cpu_or_memory=" + ("true" if cfg.low_cpu_or_memory == True else "false") + "\n"
    text += "max_length=" + str(cfg.max_length) + "\n"
    text += "use_chat_history=" + ("true" if cfg.use_chat_history == True else "false") + "\n"
    text += "use_dynamic_system_args=" + ("true" if cfg.use_dynamic_system_args == True else "false") + "\n"
    text += "prompt_order=" + cfg.prompt_order + "\n"
    text += "use_gpu=" + ("true" if cfg.use_gpu_if_available == True else "false") + "\n"
    text += "ai_args=" + cfg.ai_args + "\n"
    text += "custom_sys_msg=" + cfg.custom_system_messages + "\n"
    text += "sys_msg_first_person=" + ("true" if cfg.system_messages_in_first_person == True else "false") + "\n"
    text += "use_default_system_messages=" + ("true" if cfg.use_default_system_messages == True else "false") + "\n"
    text += "welcome_message=" + cfg.welcome_message + "\n"
    text += "temp=" + str(cfg.temp) + "\n"
    text += "save_conversations=" + ("true" if cfg.save_conversations == True else "false") + "\n"
    text += "keys_db=" + str(cfg.keys_db).replace("'", "\"") + "\n"
    text += "print_prompt=" + ("true" if cfg.print_prompt == True else "false") + "\n"

    with open("config.tcfg", "w") as f:
        f.write(text)
        f.close()

current_data = ReadConfig()