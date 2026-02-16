from typing import Optional, Literal

import discord
from discord.ext import commands

from src.containers import Container
from src.helpers.env import DISCORD_TOKEN
from src.vale import Vale

container = Container()
container.wire(modules=[__name__])


def main() -> None:
    bot: Vale = container.bot()

    @bot.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object],
                   spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        """
        Synchronize commands between bot and guild(s).

        :param ctx: The context in which the command is being invoked.
        :type ctx: commands.Context
        :param guilds: A list of guild objects or ids, if provided.
        :type guilds: commands.Greedy[discord.Object]
        :param spec: An optional string specifying the sync behavior. Possible values are "~" (sync all guild commands for the current context's guild), "*" (copy all global commands to the
        * current guild and sync), and "^" (remove all guild commands from the CommandTree and sync, effectively removing all commands from the guild). Default is None.
        :type spec: Optional[Literal["~", "*", "^"]]
        :return: None
        :rtype: None

        """
        if not guilds:
            if spec == "~":
                # sync all guild commands for the current context’s guild
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                # copy all global commands to the current guild (within the CommandTree) and sync
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                # remove all guild commands from the CommandTree and syncs,
                # which effectively removes all commands from the guild
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                # takes all global commands within the CommandTree and sends them to Discord
                synced = await ctx.bot.tree.sync()

            await ctx.message.reply(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}",
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.message.reply(
            f"Synced the tree to {ret}/{len(guilds)}.",
        )

    bot.run(token=DISCORD_TOKEN)


if __name__ == '__main__':
    main()
