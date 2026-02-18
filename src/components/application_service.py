from motor.motor_asyncio import AsyncIOMotorClient
import discord
from src.helpers.env import MONGO_DATABASE, TEAM_APPLICATIONS_CHANNEL_ID


class ApplicationService:
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db = db_client.get_database(MONGO_DATABASE)
        self.collection = self.db.get_collection("applications")

    async def has_application(self, user_id: int) -> bool:
        return await self.collection.count_documents({"user_id": user_id}) > 0

    async def save_application(self, user_id: int, user_tag: str, data: dict):
        document = {
            "user_id": user_id,
            "user_tag": user_tag,
            "data": data,
            "status": "pending",
            "created_at": discord.utils.utcnow()
        }

        await self.collection.insert_one(document)

    async def notify_team(self, guild: discord.Guild, user: discord.User, data: dict):
        channel = guild.get_channel(TEAM_APPLICATIONS_CHANNEL_ID)

        if not channel:
            return

        embed = discord.Embed(
            title="Neue Bewerbung",
            description=f"Eine neue Bewerbung von {user.mention} ({user.name}; {user.id}) ist eingegangen.",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

        for label, value in data.items():
            embed.add_field(name=label, value=value, inline=False)

        await channel.send(embed=embed)
