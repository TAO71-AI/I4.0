"""
This is still under creaton.
It will not work for now.
"""

# Import some things
from discord.ext import commands
import discord
import os
import ai_config as cfg

# Create message intents
Intents = discord.Intents.default()

Intents.dm_messages = True
Intents.message_content = True
Intents.moderation = True

# Create bot
Bot = commands.Bot(command_prefix = cfg.current_data["discord_bot"]["prefix"] + " ", intents = Intents)

# On ready
@Bot.event
async def on_ready() -> None:
    print(f"Connected to Discord as '{Bot.user}'.")

@Bot.event
async def on_message(Message: discord.Message) -> None:
    if (Message.author == Bot.user):
        return
    
    pass # TODO