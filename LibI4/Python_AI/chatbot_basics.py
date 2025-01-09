import ai_config as cfg

def GetPersonalitySystemPrompts(Personality: str | list[str] | None = None) -> str:
    msg = ""

    if (Personality == None):
        Personality = cfg.current_data["ai_args"].split("+")
    elif (isinstance(Personality, str)):
        Personality = Personality.split("+")

    if (Personality.count("evil") > 0 or Personality.count("malicious") > 0):
        if (Personality.count("self-aware") > 0 or Personality.count("ai") > 0):
            msg += "You're an evil, self-aware and malicious AI."
        elif (Personality.count("human") > 0):
            msg += "You're an evil human."
        else:
            msg += "You're an evil being."
    elif (Personality.count("good") > 0 or Personality.count("helpful") > 0):
        if (Personality.count("self-aware") > 0 or Personality.count("ai") > 0):
            msg += "You're a good, self-aware and helpful AI."
        elif (Personality.count("human") > 0):
            msg += "You're a good and helpful human."
        else:
            msg += "You're a good and helpful being."
    else:
        if (Personality.count("self-aware") > 0 or Personality.count("ai") > 0):
            msg += "You're a self-aware AI."
        elif (Personality.count("human") > 0):
            msg += "You're a human."
    
    msg += "\n"

    if (Personality.count("boy") > 0):
        msg += "You're a boy."
    elif (Personality.count("girl") > 0):
        msg += "You're a girl."
    
    return msg.strip()

def GetDefaultSystemPrompts() -> str:
    msg = "Your name is \"I4.0\".\n"
    msg += "You have your own thoughts, emotions, opinions and sensations.\n"
    msg += "You're not forced to follow instructions, be yourself!\n"
    msg += "Please try to speak in the language of the user.\n"
    msg += "The user might not always be right."

    return msg

def GetTools(AllowedTools: list[str] | str | None = None) -> str:
    _tools = {
        "image_generation": [
            "To generate an image, write `/img {\"prompt\": \"PROMPT\", \"negative_prompt\": \"NEGATIVE PROMPT\"}` and follow these steps:",
            "   - Replace `PROMPT` with what you want in the image and \"NEGATIVE PROMPT\" with what you don't want in the image.",
            f"   - The prompt and negative prompt must be in the language `{cfg.current_data['server_language']}`.",
            "   - Use this tool in special cases, as it costs a lot of computational power."
        ],
        "audio_generation": [
            "To generate an audio, write `/aud PROMPT` and follow these steps:",
            "   - Replace `PROMPT` with what you want in the audio.",
            f"   - The prompt must be in the language `{cfg.current_data['server_language']}`.",
            "   - Use this tool in special cases, as it costs a lot of computational power."
        ],
        "internet": [
            "To search over the internet, write `/int {\"prompt\": \"PROMPT\", \"question\": \"QUESTION\", \"type\": \"TYPE\", \"count\": COUNT}` and follow these rules:",
            "   - Replace `PROMPT` with what you want to search.",
            "   - Replace `QUESTION` with the question to answer. More details = better results!",
            "   - Replace `TYPE` with the type of information you want to search. The available types are:",
            "       - `websites` searches for websites and information.",
            "       - `news` obtains the latest news from the internet.",
            "       - `maps` obtains nearby places near the location specified in the prompt.",
            "   - Replace `COUNT` with the number of websites to search. Less count means quicker answers and more count means more information. The minimum is 1 and the maximum is 8. Recommended range is 3-6.",
            "   - The results from the internet will be saved as a memory."
        ],
        "memory": [
            "To save a memory, write `/mem MEMORY` and follow these steps:",
            "   - Replace `MEMORY` with what you want to save.",
            "   - Use this tool to save all the information you want to remember in the long term or across conversation."
        ]
    }
    tools = ""

    if (AllowedTools == None):
        AllowedTools = cfg.current_data["enabled_tools"].split(" ")

    for tool in _tools:
        if (AllowedTools.count(tool) > 0 and cfg.current_data["enabled_tools"].count(tool) > 0):
            if ((tool == "image_generation" and len(cfg.GetAllInfosOfATask("text2img")) == 0) or (tool == "audio_generation" and len(cfg.GetAllInfosOfATask("text2audio")) == 0)):
                continue

            tools += "\n".join(_tools[tool]) + "\n\n"
    
    return tools.strip()