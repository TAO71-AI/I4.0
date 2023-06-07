import chatbot_gpt4all as cbg4a
import chatbot_any as cba
import chatbot_basics as basics
import ai_config as cfg
import openai

if (cfg.ReadConfig().use_tf_v2):
    import chatbot_tf_v2 as cbtf
else:
    import chatbot_tf as cbtf

def DefaultOrder() -> str:
    return "0312"

openai_model: str = "gpt-3.5-turbo"
openai_max_tokens: int = 25
system_messages: list[str] = []
apply_system_messages_to_tensorflow: bool = False
use_chat_history_if_available: bool = True
order: str = DefaultOrder()

def SystemMessagesToStr(extra_system_messages: list[str] = None) -> str:
    sm_str = "("

    for i in system_messages:
        sm_str += i

    if (extra_system_messages != None):
        for i in extra_system_messages:
            sm_str += i
    
    sm_str += ") "
    return sm_str

def LoadAllModels() -> None:
    for i in order:
        if (i == "0"):
            cbg4a.LoadModel()
        elif (i == "3"):
            cba.LoadModel()

def MakePrompt(prompt: str, order_prompt: str = "") -> dict:
    LoadAllModels()

    cbg4a.system_messages = system_messages

    if (not prompt.endswith(".") and not prompt.endswith("!") and not prompt.endswith("?")):
        prompt += "."

    if (len(order_prompt) <= 0):
        order_prompt = order

        if (len(order) <= 0):
            order_prompt = DefaultOrder()
            order = order_prompt
    
    tested_models: list[str] = []
    errors: list[str] = []

    for i in order_prompt:
        response = "ERROR"

        try:
            if (i == "0"):
                response = cbg4a.MakePrompt(prompt, use_chat_history_if_available)
            elif (i == "1"):
                response = cbtf.get_ai_response((SystemMessagesToStr() if apply_system_messages_to_tensorflow else "") + prompt)
            elif (i == "2"):
                response = openai.Completion.create(model = openai_model, prompt = SystemMessagesToStr() + prompt,
                    temperature = 0.5, max_tokens = openai_max_tokens)
            elif (i == "3"):
                response = cba.MakePrompt(prompt)
            
            tested_models += i
        except Exception as ex:
            errors.append("Error on model '" + i + "': '" + str(ex) + "'")
            continue

        response = response.strip()

        try:
            response = response.split("\n")[0]
            response = response.split("### Explanation")[0]
            response = response.split("### Prompt")[0]
            response = response.split("### Task")[0]
        except:
            pass
            
        if (len(response.strip()) > 0 and response.lower() != "error" and response.lower() != "error."):
            return {
                "response": response,
                "model": i,
                "tested_models": tested_models,
                "errors": errors
            }

    return {
        "response": "ERROR",
        "model": "-1",
        "tested_models": tested_models,
        "errors": ["Error on response from all models."]
    }