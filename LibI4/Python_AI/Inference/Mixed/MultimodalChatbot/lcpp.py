# Import other libraries
from llama_cpp import Llama
from collections.abc import Iterator
from io import BytesIO
from PIL import Image as PILImage
import json
import base64

def __inference__(
        Model: Llama,
        Config: dict[str, any],
        ContentForModel: list[dict[str, str]],
        Seed: int | None,
        Tools: list[dict[str, str | dict[str, any]]],
        MaxLength: int,
        Temperature: float,
        TopP: float,
        TopK: int,
        MinP: float,
        TypicalP: float
    ) -> Iterator[str]:
    # Convert the all the images to a valid format
    for msg in ContentForModel:
        if (msg["role"] == "system"):
            continue

        for content in msg["content"]:
            if (content["type"] == "image"):
                imgInputBuffer = BytesIO(base64.b64decode(content["image"][18:]))
                img = PILImage.open(imgInputBuffer)

                imgOutputBuffer = BytesIO()
                img.save(imgOutputBuffer, format = "PNG")

                img.close()
                imgInputBuffer.close()

                img = imgOutputBuffer.getvalue()
                imgOutputBuffer.close()

                img = base64.b64encode(img).decode("utf-8")

                content["type"] = "image_url"
                content["image_url"] = {"url": f"data:image/png;base64,{img}"}
                del content["image"]

    # Get a response from the model
    response = Model.create_chat_completion(
        messages = ContentForModel,
        temperature = Temperature,
        max_tokens = MaxLength,
        top_p = TopP,
        top_k = TopK,
        min_p = MinP,
        typical_p = TypicalP,
        seed = Seed,
        tools = Tools,
        tool_choice = None,
        stream = True
    )

    # For every token
    for token in response:
        # Check if it's valid (contains a response)
        if (not "content" in token["choices"][0]["delta"]):
            continue

        # Get the tools
        tools = token["choices"][0]["delta"].get("tool_calls")

        if (tools is not None):
            for tool in token["choices"][0]["delta"]["tool_calls"]:
                yield json.dumps(tool["function"])

        # Yield the token
        yield token["choices"][0]["delta"]["content"]