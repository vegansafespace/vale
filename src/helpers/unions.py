from typing import Union

import discord

MessageableChannel = Union[
    discord.TextChannel,
    discord.VoiceChannel,
    discord.StageChannel,
    discord.Thread,
    discord.DMChannel,
    discord.PartialMessageable,
    discord.GroupChannel,
]
