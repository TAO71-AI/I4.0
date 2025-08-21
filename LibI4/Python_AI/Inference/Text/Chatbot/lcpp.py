# Import other libraries
from llama_cpp import Llama
from collections.abc import Iterator
import json

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
        TypicalP: float,
        ExtraKWargs: dict[str, any]
    ) -> Iterator[str]:
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
        tool_choice = "auto",
        stream = True,
        **ExtraKWargs
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