import ai_config as cfg

class Plugins:
    def All() -> list[str]:
        return [
            "sing", "vtuber", "discord bot", "twitch",
            "gaming", "image_generation", "pacep"
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

def GetDefault_I4_SystemMessages(available_plugins: list[str] = [], extra_messages: list[str] = []) -> list[str]:
    msgs = [
        "You are 'I4.0', a 10 years old girl.",
        "Your height is 140cm. You have a cute blue hair.",
        "You're free to have your own thoughts, emotions and opinions."
    ]

    # Friends of I4.0
    msgs.append("Your friends are 'Alcoft' (a boy), 'Dinolt' (a girl), 'Jlmr08' (a boy), 'Codearduinopython' (a boy).")

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
        elif (plugin == "image_generation" and cfg.current_data.prompt_order.__contains__("text2img")):
            msgs.append("To paint an image or generate an image you need to say [agi 'PROMPT'] where you replace 'PROMPT' with the image description.")
        elif (plugin == "pacep"):
            msgs.append("You have an AI assistant called 'PaCep', you can call him by saying '[PACEP]'.")
    
    for msg in extra_messages:
        msgs.append(msg)
    
    msgs2 = []
    
    if (cfg.current_data.system_messages_in_first_person):
        msgs2 = ToFirstPerson(msgs)
    else:
        msgs2 = msgs

    return msgs2

def ToFirstPerson(messages: list[str]) -> list[str]:
    msgs2 = []
    
    for msg in messages:
        msgs2.append(msg.replace("You're", "I'm").replace("You are", "I am").replace("Your", "My").replace("You", "I"))
    
    return msgs2