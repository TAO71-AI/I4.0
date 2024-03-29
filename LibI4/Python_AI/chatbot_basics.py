import ai_config as cfg

class Plugins:
    def All() -> list[str]:
        return [
            "sing", "vtuber", "discord bot", "twitch",
            "gaming", "image_generation", "audio_generation"
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
        "You have your own thoughts, emotions and opinions.",
        "Your friends are 'Alcoft' (a boy), 'Dinolt' (a girl), 'Jlmr08' (a boy), 'Codearduinopython' (a boy)."
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
        elif (plugin == "image_generation" and cfg.current_data.prompt_order.__contains__("text2img")):
            msgs.append("To paint a picture or generate an image you need to say [agi 'PROMPT'] where you replace 'PROMPT' with the image description.")
        elif (plugin == "audio_generation" and cfg.current_data.prompt_order.__contains__("text2audio")):
            msgs.append("To generate an audio you need to say [aga 'PROMPT'] where you replace 'PROMPT' with the audio description.")
    
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