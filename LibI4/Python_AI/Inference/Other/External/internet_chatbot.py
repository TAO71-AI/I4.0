# Import I4.0 utilities
import ai_config as cfg

# Import other libraries
import requests
import json
import copy

# Create global variables
"""
Models example template:
{
    "ModelName": {
        "PrivacyLevel": "`unknown`, `low`, `medium`, `high`...",           <-- Optional
        "Censorship": "`unknown`, `none`, `low`, `medium`, `high`...",     <-- Optional
        "UsualSpeed": "`unknown`, `slow`, `medium`, `fast`...",            <-- Optional
        "Description": "...",                                              <-- Optional
        "API": "`pollinations=MODEL_NAME`",
        "OpenSource": `True` or `False`,                                   <-- Optional
        "Supports": [
            "tools",
            "reasoning",
            "image",        <-- Not supported yet
            "audio",        <-- Not supported yet
            "video"         <-- Not supported yet
        ],
        "SpecializedFor": [                                                <-- Optional
            "General conversations",
            "Programming",
            ...
        ]
    }
}

Some parameters may be optional, but they help I4.0 to choose a better model for each task.
"""

__models_list__: dict[str, dict[str, any]] = {}

def UpdateModelsList() -> None:
    # Define globals
    global __models_list__

    # Clear the dictionary
    __models_list__.clear()

    # Set variables
    updatedFromInternet = False

    if (len(cfg.current_data["internet"]["models"]["update_from_url"]) > 0):
        # Update the models from the URL
        response = requests.get(cfg.current_data["internet"]["models"]["update_from_url"])

        # Make sure the response is fine
        if (response.status_code == 200):
            # Parse the JSON
            __models_list__ = json.loads(response.content.decode("utf-8"))
            updatedFromInternet = True
    
    if (not updatedFromInternet):
        # Set a fixed dictionary
        __models_list__ = {}

def GetModelsList(ExcludeSpecialParameters: bool) -> dict[str, dict[str, any]]:
    # Define globals
    global __models_list__

    if (ExcludeSpecialParameters):
        # Copy to a new dictionary
        newModelsList = copy.deepcopy(__models_list__)

        # For each value
        for modelInfo in newModelsList.values():
            # Delete all the special parameters if the dictionary contains them
            if ("Supports" in modelInfo):
                del modelInfo["Supports"]
            
            if ("API" in modelInfo):
                del modelInfo["API"]
        
        # Return the new models list
        return newModelsList
    
    # Return a copy of the models list
    return __models_list__.copy()

def InferenceModel(
        ModelName: str,
        Config: dict[str, any],
        Prompt: str,
        SystemPrompts: list[str],
        Tools: list[dict[str, str | dict[str, any]]],
        Temperature: float | None = None
    ) -> str:
    # Define globals
    global __models_list__

    # Make sure the model exists
    if (ModelName not in __models_list__):
        raise ValueError(f"Model {ModelName} not found in the available models list ({json.dumps(list(__models_list__.keys()))}).")
    
    # Strip the prompt and set the system prompts
    Prompt = Prompt.strip()
    SystemPrompts = "\n".join(SystemPrompts).strip()
    
    # Set the temperature
    if (Temperature is None):
        temp = Config["temp"] if ("temp" in Config) else 0.5
    else:
        temp = Temperature
    
    # Check the API to use
    if (__models_list__[ModelName]["API"].startswith("pollinations=")):
        # Use pollinations.ai
        # Get the model name in the API
        modelNameInAPI = __models_list__[ModelName]["API"][13:]

        # Send a POST request
        response = requests.post(
            "https://text.pollinations.ai/openai",
            headers = {
                "Content-Type": "application/json"
            },
            json = {
                "messages": [
                    {"role": "system", "content": SystemPrompts},
                    {"role": "user", "content": Prompt}
                ],
                "temperature": temp,
                "tools": Tools,
                "model": modelNameInAPI,
                "private": True
            }
        )
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
    else:
        # Invalid API
        raise ValueError("Invalid model API.")
    
    """
    Note: The model will give the whole response at once, streamming is not supported.
    """
    
    # Return the content
    return content