import os

class ConfigData:
    gpt4all_model: str = "ggml-gpt4all-j-v1.3-groovy"
    any_model: str = "microsoft/DialoGPT-small"
    tf_data_file: str = "tf_train_data_es.txt"
    tf_epochs: int = 100
    force_api_key: bool = True
    use_tf_v2: bool = False
    low_cpu_or_memory: bool = False
    max_length: int = 1000
    use_chat_history: bool = True
    unrecognized_data: list[str] = []
    prompt_order: str = "0312"

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
            elif (il == "tf_data_file"):
                data.tf_data_file = config_dict[i]
            elif (il == "tf_epochs"):
                try:
                    data.tf_epochs = int(config_dict[i])
                except:
                    data.tf_epochs = 100
            elif (il == "force_api_key"):
                data.force_api_key = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "use_tf_v2"):
                data.use_tf_v2 = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "low_cpu_or_memory"):
                data.low_cpu_or_memory = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "max_length"):
                try:
                    data.max_length = int(config_dict[i])
                except:
                    data.max_length = 1000
            elif (il == "use_chat_history"):
                data.use_chat_history = (config_dict[i].lower() == "true" or config_dict[i].lower() == "yes")
            elif (il == "prompt_order"):
                data.prompt_order = config_dict[i]
            elif (il == "unrecognized_data"):
                try:
                    data.unrecognized_data = list[config_dict[i]]
                except:
                    pass
            else:
                if (not data.unrecognized_data.__contains__(config_dict[i])):
                    data.unrecognized_data.append(config_dict[i])

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
    text += "tf_data_file=" + cfg.tf_data_file + "\n"
    text += "tf_epochs=" + str(cfg.tf_epochs) + "\n"
    text += "force_api_key=" + ("true" if cfg.force_api_key == True else "false") + "\n"
    text += "use_tf_v2=" + ("true" if cfg.use_tf_v2 == True else "false") + "\n"
    text += "low_cpu_or_memory=" + ("true" if cfg.low_cpu_or_memory == True else "false") + "\n"
    text += "max_length=" + str(cfg.max_length) + "\n"
    text += "use_chat_history=" + ("true" if cfg.use_chat_history == True else "false") + "\n"
    text += "prompt_order=" + cfg.prompt_order + "\n"
    text += "unrecognized_data=" + str(cfg.unrecognized_data) + "\n"

    with open("config.tcfg", "w") as f:
        f.write(text)
        f.close()

current_data = ReadConfig()