from typing import Union, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import discord
from src.helpers.env import MONGO_DATABASE, TEAM_APPLICATIONS_CHANNEL_ID


class ApplicationService:
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db = db_client.get_database(MONGO_DATABASE)
        self.collection = self.db.get_collection("applications")

    async def has_application(self, user_id: int) -> bool:
        return await self.collection.count_documents({"user_id": user_id}) > 0

    async def save_application(self, user_id: int, user_tag: str, data: dict, team_message_id: int = None) -> str:
        document = {
            "user_id": user_id,
            "user_tag": user_tag,
            "data": data,
            "team_message_id": team_message_id,
            "status": "pending",
            "created_at": discord.utils.utcnow()
        }

        result = await self.collection.insert_one(document)
        return str(result.inserted_id)


    async def notify_team(self, guild: discord.Guild, user: discord.User, data: dict) -> Optional[discord.Message]:
        channel = guild.get_channel(TEAM_APPLICATIONS_CHANNEL_ID)

        if not channel:
            return None

        embed = discord.Embed(
            title="Neue Bewerbung",
            description=f"Eine neue Bewerbung von {user.mention} ({user.name}; {user.id}) ist eingegangen.",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

        for label, value in data.items():
            embed.add_field(name=label, value=value, inline=False)

        return await channel.send(embed=embed)

    async def get_application(self, user_id: int) -> dict:
        return await self.collection.find_one({"user_id": user_id})

    async def delete_application(self, user_id: int):
        await self.collection.delete_one({"user_id": user_id})

    async def revoke_application(self, guild: discord.Guild, user: Union[discord.User, discord.Member], reason: str = None) -> bool:
        application = await self.get_application(user.id)

        if not application:
            return False

        if application.get("status", None) != "pending":
            return False

        # Attempt to delete the message in the team channel
        team_message_id = application.get('team_message_id')

        if team_message_id:
            team_channel = guild.get_channel(TEAM_APPLICATIONS_CHANNEL_ID)

            if team_channel:
                try:
                    message = await team_channel.fetch_message(team_message_id)
                    await message.delete()

                    description = f"Die Bewerbung von {user.mention} ({user.name}; {user.id}) wurde zurückgezogen."

                    if reason:
                        description += f" Grund: {reason}"

                    embed = discord.Embed(
                        title="Bewerbung zurückgezogen",
                        description=description,
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow()
                    )

                    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

                    await team_channel.send(embed=embed, reference=message)
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    pass
                except Exception:
                    pass

        await self.delete_application(user.id)
        return True
