import gpt4all
import ai_config as cfg

model_name: str = cfg.ReadConfig().gpt4all_model
system_messages: list[str] = []

model: gpt4all.GPT4All = None
messages = []
chat_history = []
print_data = False

def LoadModel() -> None:
    global model

    if (len(model_name) <= 0 or model != None):
        return

    try:
        model = gpt4all.GPT4All(model_name = model_name)
    except:
        pass

def ApplySystemMessagesToModel() -> None:
    messages.clear()

    for message in system_messages:
        messages.append({"role": "system", "content": message})

def MakePrompt(prompt: str, use_chat_history: bool = True) -> str:
    LoadModel()
    ApplySystemMessagesToModel()

    if (use_chat_history):
        for i in chat_history:
            messages.append(i)

    content = [
        "### Prompt:" + prompt + "\n### Response:"
    ]
    content_str = ""

    for i in content:
        content_str += i

    messages.append({"role": "user", "content": content_str})
    response = model.chat_completion(messages, verbose = print_data)["choices"][0]["message"]["content"]

    chat_history.append({"role": "assistant", "content": response})

    return "ERROR" if (len(response.strip()) < 1) else response