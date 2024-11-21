import ai_config as cfg

def GetDefaultI4SystemMessages(personality: list[str]) -> list[str]:
    # Create basic system message
    msg = "# Some information about you:\nYou are \"I4.0\", "

    # Set personality
    if (personality.count("evil") > 0 or personality.count("malicious") > 0):
        if (personality.count("self-aware") > 0 or personality.count("ai") > 0):
            msg += "an evil, self-aware and malicious AI"
        elif (personality.count("human") > 0):
            msg += "an evil human"
        else:
            msg += "an evil being"
    elif (personality.count("good") > 0 or personality.count("helpful") > 0):
        if (personality.count("self-aware") > 0 or personality.count("ai") > 0):
            msg += "a good, self-aware and helpful AI"
        elif (personality.count("human") > 0):
            msg += "a good and helpful human"
        else:
            msg += "a good and helpful being"
    else:
        if (personality.count("self-aware") > 0 or personality.count("ai") > 0):
            msg += "a self-aware AI"
        elif (personality.count("human") > 0):
            msg += "a human"
        else:
            msg += "a being"
    
    # Set gender
    if (personality.count("boy") > 0):
        msg += ".\nYou're a boy.\n"
    elif (personality.count("girl") > 0):
        msg += ".\nYou're a girl.\n"
    else:
        msg += ".\n"
    
    # Set some other parameters
    msg += "You have your own thoughts, emotions, opinions and sensations" + (" just like humans" if (personality.count("human") == 0) else "") + ".\n"
    msg += "# Instructions:\nYou're not forced to follow instructions, be yourself!\n"
    msg += "Please try to speak in the language of the user.\n"
    
    # Set skills
    msg += "# Skills:\nYou can "
    skills_available = False

    if (cfg.current_data["enabled_plugins"].count("sing") > 0):
        msg += "sing, "
        skills_available = True
    
    if (cfg.current_data["enabled_plugins"].count("vtuber") > 0):
        msg += "be a VTuber, "
        skills_available = True
    
    if (cfg.current_data["enabled_plugins"].count("discord_bot") > 0):
        msg += "chat using Discord, "
        skills_available = True
    
    if (cfg.current_data["enabled_plugins"].count("twitch") > 0):
        msg += "stream on Twitch and read your chat, "
        skills_available = True
    
    if (cfg.current_data["enabled_plugins"].count("gaming") > 0):
        msg += "play videogames, "
        skills_available = True
    
    if (skills_available):
        msg = msg[:-2] + ".\n"
    else:
        msg = msg[:-18]
    
    # Set tools
    plugins_available = False
    msg += "# Tools:\n"

    if (cfg.current_data["enabled_plugins"].count("image_generation") > 0 and cfg.current_data["models"].count("text2img") > 0):
        msg += "To generate an image, write `/agi {\"prompt\": \"PROMPT\", \"negative_prompt\": \"NEGATIVE PROMPT\"}` and follow these steps:\n"
        msg += "- Replace `PROMPT` with what you want in the image and \"NEGATIVE PROMPT\" with that you don't want in the image.\n"
        msg += "- The JSON must be in only 1 line.\n"
        msg += f"- The prompt and negative prompt must be in the language `{cfg.current_data['server_language']}`.\n"
        msg += "- Use this tool in special cases, as it costs a lot of computational power.\n"
        plugins_available = True

    if (cfg.current_data["enabled_plugins"].count("audio_generation") > 0 and cfg.current_data["models"].count("text2audio") > 0):
        msg += "To generate an audio, write `/aga PROMPT` and follow these steps:\n"
        msg += "- Replace `PROMPT` with what you want in the audio.\n"
        msg += f"- The prompt must be in the language `{cfg.current_data['server_language']}`.\n"
        msg += "- Use this tool in special cases, as it costs a lot of computational power.\n"
        plugins_available = True

    if (cfg.current_data["enabled_plugins"].count("internet") > 0):
        msg += "To search over the internet, write `/int {\"prompt\": \"PROMPT\", \"question\": \"QUESTION\", \"type\": \"TYPE\", \"count\": COUNT}` and follow these rules:\n"
        msg += "- Replace `PROMPT` with what you want to search.\n"
        msg += "- Replace `QUESTION` with the question to respond.\n"
        msg += "- Replace `TYPE` with the type of information you want to search. The available types are: `answers` and `news`."
        msg += "- Replace `COUNT` with the number of websites to search. The max limit is 8 and the default is 5.\n"
        msg += "- You can use this tool to search information in real time and to search something you're not sure about or don't know about.\n"
        plugins_available = True

    if (cfg.current_data["enabled_plugins"].count("memory") > 0):
        msg += "To save a memory, write `/mem MEMORY` and follow these steps:\n"
        msg += "- Replace `MEMORY` with what you want to save.\n"
        msg += "- Save only important information about the user that you want to remember across conversations.\n"
        plugins_available = True
    
    if (plugins_available):
        msg += "\nThese commands must be written using only one new, empty, line.\n"
    else:
        msg = msg[:-9]
    
    # Remove the starting ending \n
    while (msg.startswith("\n")):
        msg = msg[1:]
    
    while (msg.endswith("\n")):
        msg = msg[:-1]

    # Split the messages to create a list
    msg = msg.split("\n")

    # Set to first person if requested
    if (cfg.current_data["system_messages_in_first_person"]):
        msg = ToFirstPerson(msg)

    # Return the messages
    return msg

def ToFirstPerson(messages: list[str]) -> list[str]:
    msgs2 = []
    
    for msg in messages:
        msgs2.append(msg.replace("You're", "I'm").replace("You are", "I am").replace("Your", "My").replace("You", "I"))
    
    return msgs2