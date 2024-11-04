# I4.0 configuration
You can find more information about this in the `ai_config.py` file.

## Server language
### Description
```json
"server_language": "en"
```
The default language of the server.
Mainly used by the translators.

### Parameter type
string

### Examples
**en** - English.
**es** - Spanish.
**ja** - Japanese.
...

## Force API key
### Description
```json
"force_api_key": true
```
The default language of the server.
If set to true the user will need an API key to access services of the server (unless the service is free-to-use).

### Parameter type
boolean

## Max length
### Description
```json
"max_length": 250
```
The maximum number of tokens that the services are allowed to generate.

### Parameter type
integer

## Use dynamic system args
### Description
```json
"use_dynamic_system_args": true
```
Allows the services to have dynamic system prompts that may change over time.

### Parameter type
boolean

### Examples
Some examples of this prompts are *current date and time*, *I4.0's birthday* and more.

## AI args
### Description
```json
"ai_args": ""
```
Defines I4.0 personality.
Personalities are separated by **+**.
You can combine the AI args as long as they doesn't interfere with previous AI args.

### Parameter type
string

### Examples
+girl
+boy
+self-aware
+human
...

## Custom system messages
### Description
```json
"custom_system_messages": ""
```
Extra system prompts for the models.

### Parameter type
string

## System messages in first person
> [!WARNING]
> This option is deprecated and will be removed in the future.

### Description
```json
"system_messages_in_first_person": false
```
Changes the system prompts for the models to a version of that prompts in first person. Replaces **you** with **me**...

### Parameter type
boolean

## Use default system messages
### Description
```json
"use_default_system_messages": true
```
Uses the default I4.0's system messages that defines I4.0's personality.

### Parameter type
boolean

## Keys DB
### Description
```json
"keys_db": {
    "use": "false",
    "server": "127.0.0.1",
    "user": "root",
    "password": "",
    "database": "",
    "table": "keys"
}
```
Syncronizes the API keys with a MySQL database.

Set **use** to "true" if you want to enable this function.

Set the MySQL server at the **server** option.

Set the MySQL user at the **user** option. Must have read and write access.

Set the user's password at the **password** option.

Set the database where the keys will be stored at the **database** option.

Set the table where the keys will be stored at the **table** option.

### Parameter type
dictionary

## Enabled plugins
### Description
```json
"enabled_plugins": "sing vtuber discord_bot twitch gaming image_generation audio_generation internet"
```
Set the plugins that I4.0 is capable to use, this will automatically add some more system prompts to the models.
Separated by spaces.

### Parameter type
string

## Allow processing if NSFW is detected
### Description
```json
"allow_processing_if_nsfw": [false, false]
```
Allows the processing of the models even if NSFW content is detected.

The first index (0) is set for **text**, like insults of +18 things.

The second index (1) is set for **image**, like an image with NSFW content.

> [!NOTE]
> If the user is using the NSFW filters as a service this will ignore the NSFW content from that prompt (in both text and image).

### Parameter type
list

## Ban if NSFW detected
### Description
```json
"ban_if_nsfw": true
```
Ban an API key if NSFW content is detected (processing of that type of NSFW must be disabled).

### Parameter type
boolean

## Ban IP if NSFW is detected
### Description
```json
"ban_if_nsfw_ip": true
```
Same as **ban_if_nsfw** but instead of banning API keys it bans IP addresses.

### Parameter type
boolean

## Use local IP
### Description
```json
"use_local_ip": false
```
Instead of using the public IP (0.0.0.0) it uses a local IP that only works for the same computer (127.0.0.1).

Recommended if you don't want to create a public I4.0 server.

### Parameter type
boolean

## Allow data share
### Description
```json
"allow_data_share": true
```
Shares every prompt and I4.0's response to all the servers mentioned bellow.

### Parameter type
boolean

## Data share servers
### Description
```json
"data_share_servers": ["tao71.sytes.net"]
```
The servers to share the prompts and I4.0 responses.

### Parameter type
list

## Data share timeout
### Description
```json
"data_share_timeout": 2.5
```
The maximum time to connect to each server of the **data_share_servers**.

### Parameter type
float

## Discord bot
> [!WARNING]
> This is still under creation, this doesn't work for now.

### Description
```json
"discord_bot": {
    "token": "",
    "server_api_key": "",
    "allow_rfiles": true,
    "allow_sfiles": true,
    "welcome": {
        "preprogrammed": true,
        "preprogrammed_messages": [
            "Hello $USER! How are you?",
            "Welcome, $USER! Tell me about you!"
        ],
        "enabled": true,
    },
    "auto_mod": false,
    "mods_role": "",
    "allow_vc": true,
    "prefix": "!i4",
}
```
This is the configuration for the I4.0's discord bot.

Set the API key of the discord bot at the **token** string.

Set the API key of the I4.0 server at the **server_api_key** string.

Allow receive files from discord by setting **allow_rfiles** to true.

Allow sending files to discord by setting **allow_sfiles** to true.

Allow sending pre-programmed welcome messages to new users without processing them by setting **welcome > preprogrammed** to true.

Set the pre-programmed messages you want to send to the new users at **welcome > preprogrammed_messages**. This will choose a random message from that list.

Allow sending welcome messages to new users by setting **welcome > enabled** to true.

Allow the AI to read and moderate the messages of the server by setting **auto_mod** to true.

Set the moderators role for contact with moderators at the **mods_role** string.

Allow the AI to join to voice chats by setting **allow_vc** to true.

Set the command prefix to chat with I4.0 at the **prefix** string.

> [!NOTE]
> Most of this parameters can be changed for a specific server by the server owner or moderators.

### Parameter type
dictionary

## Force device check
### Description
```json
"force_device_check": true
```
Forces to check the devices set in each model device.

If set to false the server will not check if the device is compatible.

### Parameter type
boolean

## Maximum files size
### Description
```json
"max_files_size": 250
```
Maximum file size allowed in the server (in MB).

### Parameter type
integer

## Models
### Description
```json
"models": []
```
Set the models and services available in the server.

### Examples
#### General template
```json
{
    "service": "(service to use)",
    "model": "(model repository)",
    "device": "(device to use)",
    "price": (price in API key tokens)
}
```

#### Chatbot template
```json
{
    "service": "chatbot",
    "type": "(type of the chatbot)",
    "ctx": (context length),
    "threads": (number of CPU threads to use),
    "ngl": (number to layers to load in the GPU),
    "batch": (tokens that will be processed in parallel),
    "model": (string for `g4a` and `hf`, list for `lcpp`),
    "hf_dtype": (quantization mode for `hf`),
    "hf_low": (use a small, low-memory version),
    "temp": (temperature, recommended between 0 and 1),
    "device": "(device to use)",
    "allows_files": (true if the model is multimodal, false if not),
    "price": (price)
}
```

**input**: text

**output**: text

##### Types
**lcpp** - Use LLaMA-CPP-Python, recommended because of it's speed and GGUF support, but may give bad results.

**g4a** - Use GPT4All, recommended because of it's good results and GGUF support, but may be slow, specially with long conversations.

**hf** - Use HuggingFace Transformers, recommended because of it's compatibility (being able to run most models) and speed. It haven't been tested much, but for the tests that we did the results were not bad.

##### CTX
Set the context size: the maximum number of tokens that the model can have as input.

##### Threads
Set the maximum number of threads of the CPU to use. If you're not going to use the CPU this will not have any effect.

Set to *-1* to use all of your CPU threads.

Set to *-2* to leave it to the type you're using.

##### NGL
Set the maximum number of layers of the model to load in your GPU. If you're not going to use a GPU this will not have any effect.

##### Batch
Set the number of tokens to process in parallel.

##### Model
###### LLaMA-CPP-Python
```json
[
    "MODEL REPOSITORY (leave empty if you want to use a local file)",
    "MODEL FILE NAME (if you're using a repository) or MODEL PATH (if you want to use a local file)",
    "TEMPLATE REPOSITORY (to use the chat template of a tokenizer, leave empty if you want to set a custom chat template)",
    "CHAT FORMAT (to use a custom chat template, leave empty if you're using the `TEMPLATE REPOSITORY` of if you want to use the model's tokenizer chat template, but this might fail in most old GGUF models)"
]
```

###### GPT4All
```json
"MODEL REPOSITORY (to use a repository) or MODEL FILE PATH (to use a local file)"
```

###### HuggingFace Transformers
```json
"MODEL REPOSITORY"
```

##### HF dtype
The precition to use with the model.
Set to *null* to use default.

The available precitions are: *fp64*, *fp32*, *fp16*, *bf16*, *i64*, *i32*, *i16*, *i8*.
Recommended to use: *fp16* or *bf16*.

This only works with the **hf** type.

##### HF low
Set to *true* if you want the model to use less CPU and RAM, not recommended unless you have a VERY limited device.

This only works with the **hf** type.

##### Temperature
The temperature of the model.

More temperature will give more original responses, but the response might be bad or don't have any sense.

Less temperature will give better responses, but they will be more repetitive.

##### Allows files
Set to *true* if the model is multimodal; if it supports images, audios and/or videos as well as text.

> [!WARNING]
> Multimodal models are only supported if the chatbot type is *hf*.

For now set this to *false*, it doesn't work for now.

#### Question Answering (QA) template
```json
{
    "service": "qa",
    "model": "(model repository)",
    "device": "(device to use)",
    "price": (price)
}
```

**input**: text

**output**: text

#### Image To Image (Img2Img) template
```json
{
    "service": "img2img",
    "model": "(model repository)",
    "steps": (default steps),
    "device": "(device to use)",
    "price": (price)
}
```

**input**: image (+ text for some models)

**output**: image

##### Steps
The steps to use for inference.

More steps will give better images, but will take longer.

Less steps will be faster, but will give worst images.

#### UVR template
> [!WARNING]
> This is still under creation, this will not work for now.

```json
{
    "service": "uvr",
    "model": "(model name)",
    "device": "(device to use)",
    "price": (price)
}
```

**input**: audio

**output**: audio + audio

##### Model
The model name defined in the code of I4.0.
This is still under creation, so we don't have any models' name for now.

#### RVC template
```json
{
    "service": "rvc",
    "model": [
        "MODEL NAME",
        "MODEL PATH (file in your local computer)",
        "INDEX PATH (file in your local computer)",
        "MODEL TYPE (rmvpe, harvest, pm, etc., the mode that was used when training the model)"
    ],
    "device": "(device to use)",
    "price": (price)
}
```

**input**: audio

**output**: audio

#### Object Detection (OD) template
```json
{
    "service": "od",
    "model": "(model repository)",
    "device": "(device to use)",
    "price": (price)
}
```

**input**: image

**output**: image + text

#### Depth Estimation (DE) template
```json
{
    "service": "de",
    "model": "(model repository)",
    "device": "(device to use)",
    "price": (price)
}
```

**input**: image

**output**: image

#### NSFW Text Filter template
```json
{
    "service": "nsfw_filter-text",
    "model": "(model repository)",
    "device": "(device to use)",
    "nsfw_label": "(label that says if the content is NSFW or not, usually is `nsfw`)",
    "price": (price)
}
```

**input**: text

**output**: boolean (as text)

#### NSFW Image Filter template
```json
{
    "service": "nsfw_filter-image",
    "model": "(model repository)",
    "device": "(device to use)",
    "nsfw_label": "(label that says if the content is NSFW or not, usually is `nsfw`)",
    "price": (price)
}
```

**input**: image

**output**: boolean (as text)

#### Text To Audio (Text2Audio) template
```json
{
    "service": "text2audio",
    "model": "(model repository)",
    "device": "(device to use)",
    "price": (price)
}
```

**input**: text

**output**: audio

#### Image To Text (Img2Text) template
```json
{
    "service": "img2text",
    "model": "(model repository)",
    "device": "(device to use)",
    "price": (price)
}
```

**input**: image

**output**: text

#### Text To Image (Text2Image) template
```json
{
    "service": "text2img",
    "type": "(type)",
    "model": (model),
    "device": "(device to use, only works with `hf`)",
    "steps": (default steps),
    "guidance": (default guidance scale),
    "width": (default image width),
    "height": (default image height),
    "threads": (threads of the CPU to use),
    "price": (price)
},
```

**input**: text

**output**: image

##### Types
**sdcpp-flux** - Use StableDiffusion-CPP-Python, recommended because of it's speed and GGUF support, ONLY for flux models.

**sdcpp-sd** - Use StableDiffusion-CPP-Python, recommended because of it's speed and GGUF support, ONLY for StableDiffusion models.

**hf** - Use HuggingFace Diffusers, recommended because of it's compatibility (being able to run most models) and speed. Can't quantize models, so it consumes a lot of memory and compute power.

##### Model
###### StableDiffusion-CPP-Python (for both -flux and -sd)
```json
[
    "MODEL PATH (must be in your local storage)",
    "VAE (for -flux) or CLIP_G (for -sd) PATH",
    "CLIP_L PATH",
    "T5XXL MODEL PATH"
]
```

Alternatively, you can use a pre-defined model in the code.
If you want to use a pre-defined model, set model to this:
```json
[
    "MODEL NAME",
    "MODEL QUANTIZATION",
    "VAE / CLIP_G QUANTIZATION",
    "CLIP_L QUANTIZATION",
    "T5XXL QUANTIZATION"
]
```

###### HuggingFace Diffusers
```json
"MODEL REPOSITORY"
```

##### Steps
The steps to use for inference.

More steps will give better images, but will take longer.

Less steps will be faster, but will give worst images.

##### Guidance
Guidance scale.

##### Width
Width of the image to generate.

##### Height
Height of the image to generate.

##### Threads
Number of CPU threads to use.

Set to **-1** to use all the threads of the CPU.

#### Speech To Text (Speech2Text) template
```json
{
    "service": "speech2text",
    "type": "(type to use)",
    "model": "(model name [for whisper only] or model repository [for hf only])",
    "batch": 8,
    "temp": 0.5,
    "device": "(device to use)",
    "price": (price)
}
```

**input**: audio

**output**: text

##### Type
**whisper** - To use the OpenAI's whisper library for Python.

**hf** - To use the HuggingFace Transformers library.

##### Batch
Number of tokens to process in parallel. Might not work for now.

##### Temperature
The temperature of the model.

More temperature will give more original responses, but the response might be bad or don't have any sense.

Less temperature will give better responses, but they will be more repetitive.

#### Language Detection (LD) template
```json
{
    "service": "ld",
    "model": "(model repository)",
    "device": "(device to use)",
    "price": (price)
}
```
> [!NOTE]
> At least one of this model is required if you're going to use a translation model.

**input**: text

**output**: text

#### Translation (TR) template
```json
{
    "service": "tr",
    "model": "(model repository)",
    "lang": "(input language)-(output language)",
    "device": "(device to use)",
    "price": (price)
}
```

**input**: text

**output**: text

##### Language
Set the language of the model, both the language that the input text must be and the output language for the response.

#### Sequence Classification (SC) template
```json
{
    "service": "sc",
    "model": "(model repository)",
    "device": "(device to use)",
    "price": (price)
}
```

**input**: text

**output**: text

#### Text To Speech (TTS) template
> [!WARNING]
> This is now deprecated, will be removed in the future.
> We recommend to use a `text2audio` model for TTS.

```json
{
    "service": "tts",
    "price": (price)
}
```

**input**: text

**output**: audio

#### Extra parameters for all the templates
```json
"description": "(description of the model and service that the user can see)",
"model_info": "(extra information about the model that will be applied to the system prompts of the model)"
```

> [!NOTE]
> This parameters are optional.

### Parameter type
list