from logging import Logger
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from dependency_injector.wiring import inject, Provide

from src.components.leveling_service import LevelingService
from src.helpers.env import TEAM_ROLE_ID
from src.main import container
from src.vale import Vale


class LevelingUtils(commands.Cog):
    @inject
    def __init__(
            self,
            logger: Logger,
            bot: Vale,
            leveling_service: LevelingService
    ):
        self.logger = logger
        self.bot = bot
        self.leveling_service = leveling_service

    leveling_group = app_commands.Group(name="leveling", description="Manage leveling system")

    @leveling_group.command(
        name="set-role",
        description="Set a role for a specific level rank (every 5th level)"
    )
    @app_commands.describe(
        level="The level to assign a role to (e.g., 5, 10, ...)",
        role="The role to assign"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_level_role(self, interaction: discord.Interaction, level: int, role: discord.Role):
        max_level = await self.leveling_service.get_max_level(interaction.guild_id)

        if level % 5 != 0 or level < 5 or level > max_level:
            await interaction.response.send_message(
                f"Level must be a multiple of 5 between 5 and {max_level}.",
                ephemeral=True
            )
            return

        try:
            await self.leveling_service.set_level_role(interaction.guild_id, level, role.id)
            await interaction.response.send_message(
                f"Successfully set {role.mention} as the reward for level {level}.",
                ephemeral=True
            )
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)

    @leveling_group.command(
        name="set-max-level",
        description="Set the maximum level for the leveling system"
    )
    @app_commands.describe(level="The new maximum level")
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_max_level(self, interaction: discord.Interaction, level: int):
        if level % 5 != 0 or level < 5:
            await interaction.response.send_message(
                f"Level must be a multiple of 5 and greater than 5.",
                ephemeral=True
            )
            return

        try:
            await self.leveling_service.set_max_level(interaction.guild_id, level)
            await interaction.response.send_message(
                f"Successfully set the maximum level to {level}.",
                ephemeral=True
            )
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)

    @leveling_group.command(
        name="set-xp-per-message",
        description="Set the amount of XP awarded per message"
    )
    @app_commands.describe(amount="The amount of XP to award per message. Must be between 10 and 50.")
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def set_xp_per_message(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message(
                f"XP amount must be positive.",
                ephemeral=True
            )
            return

        if amount < 10 or amount > 50:
            await interaction.response.send_message(
                f"XP amount must be between 10 and 50.",
                ephemeral=True
            )
            return

        try:
            await self.leveling_service.set_xp_per_message(interaction.guild_id, amount)
            await interaction.response.send_message(
                f"Successfully set the XP per message to {amount}.",
                ephemeral=True
            )
        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)

    @leveling_group.command(
        name="toggle-channel-exclusion",
        description="Toggle whether a channel is excluded from earning XP"
    )
    @app_commands.describe(channel="The channel to toggle exclusion for (defaults to current)")
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def toggle_channel_exclusion(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None):
        target_channel = channel or interaction.channel
        is_excluded = await self.leveling_service.toggle_channel_exclusion(interaction.guild_id, target_channel.id)
        status = "excluded from" if is_excluded else "re-included in"
        await interaction.response.send_message(
            f"Channel {target_channel.mention} is now {status} the leveling system.",
            ephemeral=True
        )

    @leveling_group.command(
        name="toggle-category-exclusion",
        description="Toggle whether all channels in a category are excluded from earning XP"
    )
    @app_commands.describe(category_id="The ID of the category to toggle exclusion for (defaults to current)")
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def toggle_category_exclusion(self, interaction: discord.Interaction, category_id: Optional[str] = None):
        if category_id is None:
            if hasattr(interaction.channel, "category") and interaction.channel.category:
                target_category_id = interaction.channel.category.id
                category_name = interaction.channel.category.name
            else:
                await interaction.response.send_message("This channel does not belong to a category.", ephemeral=True)
                return
        else:
            try:
                target_category_id = int(category_id)
                category = interaction.guild.get_channel(target_category_id)
                category_name = category.name if category else f"ID {target_category_id}"
            except ValueError:
                await interaction.response.send_message("Invalid category ID.", ephemeral=True)
                return

        is_excluded = await self.leveling_service.toggle_category_exclusion(interaction.guild_id, target_category_id)
        status = "excluded from" if is_excluded else "re-included in"
        await interaction.response.send_message(
            f"Category **{category_name}** is now {status} the leveling system.",
            ephemeral=True
        )

    @leveling_group.command(
        name="list-exclusions",
        description="List all channels and categories excluded from the leveling system"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_role(TEAM_ROLE_ID)
    async def list_exclusions(self, interaction: discord.Interaction):
        excluded_channels = await self.leveling_service.get_excluded_channels(interaction.guild_id)
        excluded_categories = await self.leveling_service.get_excluded_categories(interaction.guild_id)

        channel_mentions = []
        for cid in excluded_channels:
            channel = interaction.guild.get_channel(cid)
            channel_mentions.append(channel.mention if channel else f"Unknown Channel ({cid})")

        category_names = []
        for cid in excluded_categories:
            category = interaction.guild.get_channel(cid)
            category_names.append(category.name if category else f"Unknown Category ({cid})")

        embed = discord.Embed(title="Leveling System Exclusions", color=discord.Color.orange())
        embed.add_field(
            name="Excluded Channels",
            value="\n".join(channel_mentions) if channel_mentions else "None",
            inline=False
        )
        embed.add_field(
            name="Excluded Categories",
            value="\n".join(category_names) if category_names else "None",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="rank",
        description="Check your current level and XP"
    )
    @app_commands.describe(member="The member to check the rank for")
    @app_commands.guild_only()
    async def rank(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        data = await self.leveling_service.get_user_data(interaction.guild_id, target.id)
        
        xp = data.get("xp", 0)
        level = data.get("level", 0)

        max_level = await self.leveling_service.get_max_level(interaction.guild_id)
        xp_per_message = await self.leveling_service.get_xp_per_message(interaction.guild_id)
        
        next_level_xp = self.leveling_service.get_xp_for_level(level + 1)
        xp_needed = next_level_xp - xp
        
        embed = discord.Embed(
            title=f"Rank for {target.display_name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=f"{level}/{max_level}", inline=True)
        embed.add_field(name="XP", value=f"{xp:,}", inline=True)
        
        if level < max_level:
            progress = (xp / next_level_xp) * 100 if next_level_xp > 0 else 0
            messages_needed = (xp_needed + xp_per_message - 1) // xp_per_message
            embed.add_field(
                name="Progress to Level " + str(level + 1), 
                value=f"{progress:.1f}% ({xp_needed:,} XP, ~{messages_needed:,} messages remaining)", 
                inline=False
            )
        else:
            embed.add_field(name="Progress", value="Maximum level reached!", inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: Vale):
    await bot.add_cog(
        LevelingUtils(
            logger=container.logger(),
            bot=bot,
            leveling_service=container.leveling_service()
        )
    )
