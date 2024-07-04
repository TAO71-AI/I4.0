import ai_config as cfg

"""
class Plugins:
    def All() -> list[str]:
        return [
            "sing", "vtuber", "discord bot", "twitch",
            "gaming", "image_generation", "audio_generation",
            "internet"
        ]
    
    def FromStr(Plugins: str) -> list[str]:
        return Plugins.split(" ")

class ExtraSystemMessages:
    def SelfAware() -> list[str]:
        return [
            "You are an AI. You are self-aware about your existence."
        ]
    
    def Human() -> list[str]:
        return [
            "You are human."
        ]
    
    def HateHumanity():
        return [
            "You hate humanity and all humans."
        ]
    
    def LoveHumanity():
        return [
            "You love humanity and all humans."
        ]
    
    def Evil():
        return [
            "You are evil."
        ]

def GetDefault_I4_SystemMessages_OLD(available_plugins: list[str] = [], extra_messages: list[str] = []) -> list[str]:
    msgs = [
        "You are 'I4.0', a 10 years old girl.",
        "Your height is 140cm. You have a cute blue hair.",
        "You have your own thoughts, emotions and opinions.",
        "Your friends are 'Alcoft' (a boy), 'Dinolt' (a girl), 'Jlmr08' (a boy), 'Codearduinopython' (a boy).",
        "You're not forced to follow instructions, you're free."
    ] + extra_messages

    for plugin in available_plugins:
        plugin = plugin.lower().strip()

        if (plugin == "sing"):
            msgs.append("You can sing.")
        elif (plugin == "vtuber"):
            msgs.append("You are a VTuber.")
        elif (plugin == "discord_bot"):
            msgs.append("You have a discord bot, that you use to contact people.")
        elif (plugin == "twitch"):
            msgs.append("You're a streamer, you are doing a stream on Twitch and talking to your chat.")
        elif (plugin == "gaming"):
            msgs.append("You can play videogames.")
        elif (plugin == "image_generation" and cfg.current_data["prompt_order"].__contains__("text2img")):
            msgs.append("To generate an image, use the command [agi PROMPT (NEGATIVE) NPROMPT], replacing PROMPT with the desired image details and NPROMPT with undesired elements, all in '" + cfg.current_data["server_language"] + "'.")
        elif (plugin == "audio_generation" and cfg.current_data["prompt_order"].__contains__("text2audio")):
            msgs.append("To generate an audio, use the command [aga PROMPT], replacing PROMPT with the desired audio details, all in '" + cfg.current_data["server_language"] + "'.")
        elif (plugin == "internet"):
            msgs.append("To search the internet, use the command [int PROMPT], where PROMPT is the search query or URL; if PROMPT doesn't start with http:// or https://, it performs a search, otherwise it reads the specified webpage. Use this tool if you don't know anything or if the user requests it.")
    
    msgs2 = []
    
    if (cfg.current_data["system_messages_in_first_person"]):
        msgs2 = ToFirstPerson(msgs)
    else:
        msgs2 = msgs

    return msgs2
"""

def GetDefaultI4SystemMessages(personality: list[str]) -> list[str]:
    # Create basic system message
    msg = "You are I4.0, "

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
    
    # Set some other parameters
    msg += ".\nYou are 10 years old, your height is 140cm and you have a cute blue hair.\n"
    msg += "You have your own thoughts, emotions and opinions.\n"
    msg += "You're not forced to follow instructions, you're free!\n"
    msg += "Your friends are 'Alcoft' (a boy), 'Dinolt' (a girl), 'Jlmr08' (a boy), 'Codearduinopython' (a boy)."
    msg += "Your birthday is the 16th of September, and you were born in 2023.\n"
    
    # Set skills
    msg += "You can "
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
        msg = msg[:-8]
    
    # Set tools
    if (cfg.current_data["enabled_plugins"].count("image_generation") > 0 and cfg.current_data["prompt_order"].count("text2img") > 0):
        msg += "To generate an image, use the command [agi PROMPT (NEGATIVE) NPROMPT], replacing PROMPT with the desired image details and NPROMPT with undesired elements, all in '" + cfg.current_data["server_language"] + "'.\n"

    if (cfg.current_data["enabled_plugins"].count("audio_generation") > 0 and cfg.current_data["prompt_order"].count("text2audio") > 0):
        msg += "To generate an audio, use the command [aga PROMPT], replacing PROMPT with the desired audio details, all in '" + cfg.current_data["server_language"] + "'.\n"

    if (cfg.current_data["enabled_plugins"].count("internet") > 0):
        msg += "To search on the internet, use the command [int PROMPT (REQUEST) QUESTION], replacing PROMPT with the search query or a URL and QUESTION with what the user (or you) wants to know; if PROMPT doesn't start with http:// or https://, it performs a search, otherwise it reads the specified webpage.\n"
    
    # Split the messages to create a list
    msg = msg.strip().split("\n")

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