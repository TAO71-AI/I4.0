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
    msg += "The user might not always be right.\n"
    msg += "Do not start a message with a JSON unless you're using a tool. Tools must be on top of the message."

    return msg

def IsToolValid(Tool: dict[str, str | dict[str, any]]) -> bool:
    try:
        toolType = Tool["type"]
        toolFunc = Tool["function"]
        toolName = toolFunc["name"]
        toolDescription = toolFunc["description"]
        toolParameters = toolFunc["parameters"]
        toolParametersType = toolParameters["type"]
        toolParametersProperties = toolParameters["properties"]

        for propName in list(toolParametersProperties.keys()):
            _ = {
                "type": str(toolParametersProperties[str(propName)]["type"]),
                "description": str(toolParametersProperties[str(propName)]["description"])
            }
        
        toolParametersReq = toolParameters["required"]

        if (not isinstance(toolType, str)):
            raise Exception("Tool type is not a string.")
        elif (toolType != "function"):
            raise Exception("Tool is not function.")
        elif (not isinstance(toolFunc, dict)):
            raise Exception("Tool function is not a dict.")
        elif (not isinstance(toolName, str)):
            raise Exception("Tool name is not a string.")
        elif (not isinstance(toolDescription, str)):
            raise Exception("Tool description is not a string.")
        elif (not isinstance(toolParameters, dict)):
            raise Exception("Tool parameters are not a dict.")
        elif (not isinstance(toolParametersType, str)):
            raise Exception("Tool parameters type is not a string.")
        elif (toolParametersType != "object"):
            raise Exception("Tool parameters type is not object.")
        elif (not isinstance(toolParametersProperties, dict)):
            raise Exception("Tool parameters properties is not dict.")
        elif (not isinstance(toolParametersReq, list)):
            raise Exception("Tool parameters required is not a list.")
        
        return True
    except Exception as e:
        print(f"Error validating client tool: {str(e)}")
        return False

def GetTools(AllowedTools: list[str] | str | None = None) -> list[dict[str, str | dict[str, any]]]:
    TOOLS_AVAILABLE = {
        "image_generation": {
            "type": "function",
            "function": {
                "name": "image_generation",
                "description": "Generates an image.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Prompt for the image generator. Give as many details as you can."
                        },
                        "negative_prompt": {
                            "type": "string",
                            "description": "Prompt for the image generator. Include only things you don't want in the image."
                        }
                    },
                    "required": ["prompt", "negative_prompt"]
                }
            }
        },
        "audio_generation": {
            "type": "function",
            "function": {
                "name": "audio_generation",
                "description": "Generates an audio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Prompt for the audio generator. Give as many details as you can."
                        }
                    },
                    "required": ["prompt"]
                }
            }
        },
        "internet": {
            "type": "function",
            "function": {
                "name": "internet_search",
                "description": "Search over the internet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Keywords to search. You can use special keywords such as `filetype:`, `site:`, etc."
                        },
                        "question": {
                            "type": "string",
                            "description": "Question or prompt to answer."
                        },
                        "type": {
                            "type": "string",
                            "description": "Type of search. Can be `websites`, `news` or `maps`."
                        },
                        "count": {
                            "type": "integer",
                            "description": "Max number of results to search."
                        }
                    },
                    "required": ["keywords", "question", "type"]
                }
            }
        },
        "memory": {
            "type": "function",
            "function": {
                "name": "save_memory",
                "description": "Saves a memory for the long-term.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "memory": {
                            "type": "string",
                            "description": "Memory to save. Add as many details as possible."
                        }
                    },
                    "required": ["memory"]
                }
            }
        },
        "memory-edit": {
            "type": "function",
            "function": {
                "name": "edit_memory",
                "description": "Edits a previously created memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "integer",
                            "description": "Memory index or ID."
                        },
                        "new_memory": {
                            "type": "string",
                            "description": "New memory text. Add as many details as possible."
                        }
                    },
                    "required": ["memory_id", "new_memory"]
                }
            }
        },
        "memory-delete": {
            "type": "function",
            "function": {
                "name": "delete_memory",
                "description": "Deletes a previously created memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "integer",
                            "description": "Memory index or ID."
                        }
                    },
                    "required": ["memory_id"]
                }
            }
        }
    }
    tools = []

    if (AllowedTools == None):
        AllowedTools = cfg.current_data["enabled_tools"].split(" ")
    elif (isinstance(AllowedTools, str)):
        AllowedTools = AllowedTools.split(" ")

    for tool in list(TOOLS_AVAILABLE.keys()):
        if (AllowedTools.count(tool) > 0 and cfg.current_data["enabled_tools"].count(tool) > 0):
            if (
                (tool == "image_generation" and len(cfg.GetAllInfosOfATask("text2img")) == 0) or
                (tool == "audio_generation" and len(cfg.GetAllInfosOfATask("text2audio")) == 0)
            ):
                continue

            tools.append(TOOLS_AVAILABLE[tool])
    
    return tools