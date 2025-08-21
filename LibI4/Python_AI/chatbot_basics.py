import ai_config as cfg

def GetAvailableTools(InternetChatbots: dict[str, dict[str, any]] = {}) -> dict[str, dict[str, str | dict[str, any]]]:
    return {
        "image-generation": {
            "type": "function",
            "function": {
                "name": "image_generation",
                "description": "This function generates an image.",
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
        "audio-generation": {
            "type": "function",
            "function": {
                "name": "audio_generation",
                "description": "This function generates an audio.",
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
                "description": "This function searches over the internet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Keywords to search. You can use special keywords such as `filetype:`, `site:`, etc. Please write the keywords in English."
                        },
                        "count": {
                            "type": "integer",
                            "description": "Optional. Maximum number of results to fetch from the internet. More results will use information of more websites, but response latency is bigger and the information per page is less."
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Optional. Prompt or question to answer. If not set it will use the user's prompt."
                        }
                    },
                    "required": ["keywords"]
                }
            }
        },
        "internet-url": {
            "type": "function",
            "function": {
                "name": "internet_url",
                "description": "This function reads the content of all the websites mentioned using internet.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "URLs of all the websites to read."
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Optional prompt or question to answer. If not set it will use the user's prompt."
                        }
                    },
                    "required": ["urls"]
                }
            }
        },
        "internet-research": {
            "type": "function",
            "function": {
                "name": "internet_research",
                "description": "This function researches information across the whole internet. WARNING: THIS TOOL MAY TAKE UP A LOT OF TIME AND RESOURCES, CHOOSE WISELY WHEN TO USE IT.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Keywords to search. You can use special keywords such as `filetype:`, `site:`, etc. Please write the keywords in English."
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Optional prompt or question to answer. If not set it will use the user's prompt."
                        }
                    },
                    "required": ["keywords"]
                }
            }
        },
        "internet-chatbot": {
            "type": "function",
            "function": {
                "name": "internet_chatbot",
                "description": f"This function contacts a publicly available chatbot from the internet. Available chatbots: {InternetChatbots}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "model": {
                            "type": "string",
                            "description": "Name of the model to use."
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Optional prompt or question to answer. If not set it will use the user's prompt."
                        }
                    },
                    "required": ["model"]
                }
            }
        },
        "memory": {
            "type": "function",
            "function": {
                "name": "save_memory",
                "description": "This function saves a memory for the long-term.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Memory content."
                        }
                    },
                    "required": ["content"]
                }
            }
        },
        "memory-edit": {
            "type": "function",
            "function": {
                "name": "edit_memory",
                "description": "This function edits a previously created memory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "integer",
                            "description": "Memory index or ID."
                        },
                        "new_content": {
                            "type": "string",
                            "description": "New memory content."
                        }
                    },
                    "required": ["memory_id", "new_content"]
                }
            }
        },
        "memory-delete": {
            "type": "function",
            "function": {
                "name": "delete_memory",
                "description": "This function deletes a previously created memory.",
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
        },
        "document-creator": {
            "type": "function",
            "function": {
                "name": "document_creator",
                "description": "This function creates a document.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content of the document. Depending the document this parameter can be in HTML format, or CSV format."
                        },
                        "document_type": {
                            "type": "string",
                            "description": "Type of document to create. This parameter can be `html2pdf`, `html2docx`, or `csv2xlsx`."
                        }
                    },
                    "required": ["content", "document_type"]
                }
            }
        }
    }

def GetPersonalitySystemPrompts(Personality: str | list[str] | None = None) -> str:
    """
    Get the system prompts of the AIArgs.
    """
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
    """
    Get default I4.0 system prompts.
    """
    msg = "Your name is 'I4.0'.\n"
    msg += "You have your own thoughts, emotions, opinions, and sensations."

    return msg

def IsToolValid(Tool: dict[str, str | dict[str, any]]) -> bool:
    """
    Check if a tool is valid.
    """
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
            raise Exception("Tool type is not 'function'.")
        elif (not isinstance(toolFunc, dict)):
            raise Exception("Tool function is not a dict.")
        elif (not isinstance(toolName, str)):
            raise Exception("Tool name is not a string.")
        elif (not isinstance(toolDescription, str)):
            raise Exception("Tool description is not a string.")
        elif (not isinstance(toolParameters, dict)):
            raise Exception("Tool parameter are not a dict.")
        elif (not isinstance(toolParametersType, str)):
            raise Exception("Tool parameter type is not a string.")
        elif (toolParametersType != "object"):
            raise Exception("Tool parameter type is not 'object'.")
        elif (not isinstance(toolParametersProperties, dict)):
            raise Exception("Tool parameter properties is not dict.")
        elif (not isinstance(toolParametersReq, list)):
            raise Exception("Tool parameter required is not a list.")
        
        for reqParam in toolParametersReq:
            if (reqParam not in list(toolParametersProperties.keys())):
                raise Exception("Tool required parameter not created.")
        
        return True
    except Exception as e:
        print(f"Error validating client tool: {str(e)}")
        return False

def GetTools(AllowedTools: list[str] | str | None = None, InternetChatbots: dict[str, dict[str, any]] = {}) -> list[dict[str, str | dict[str, any]]]:
    """
    Get all the tools allowed.
    """
    toolsAvailable = GetAvailableTools(InternetChatbots)
    tools = []

    if (AllowedTools == None):
        AllowedTools = cfg.current_data["enabled_tools"].split(" ")
    elif (isinstance(AllowedTools, str)):
        AllowedTools = AllowedTools.split(" ")
    elif (not isinstance(AllowedTools, list)):
        raise ValueError("AllowedTools is not a string nor a list.")

    for tool in toolsAvailable.keys():
        if (
            (AllowedTools.count(tool) > 0 and cfg.current_data["enabled_tools"].count(tool) > 0) or
            (AllowedTools.count("*") > 0 and cfg.current_data["enabled_tools"].count(tool) > 0)
        ):
            if (
                (tool == "image-generation" and len(cfg.GetAllInfosOfATask("text2img")) == 0) or
                (tool == "audio-generation" and len(cfg.GetAllInfosOfATask("text2audio")) == 0) or
                (tool == "internet-chatbot" and not cfg.current_data["internet"]["models"]["allow"]) or
                (tool == "internet-chatbot" and len(InternetChatbots) == 0)
            ):
                continue

            tools.append(toolsAvailable[tool])

    return tools