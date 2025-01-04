import asyncio
import os
import disnake
from disnake.ext import commands
from disnake.ext.commands import has_permissions
from dotenv import load_dotenv
import database
import datetime
import json
load_dotenv()

collection = database.Database(os.getenv('MONGODB_URI'), 'samplebot').get_collection("users")
bot = commands.Bot(command_prefix=commands.bot.when_mentioned, intents=disnake.Intents.all())

def load_channels():
    try:
        with open("guild_channels.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        with open("guild_channels.json", 'w') as f:
            json.dump({}, f)
        return {}
    
def save_channels(channels):
    with open("guild_channels.json", 'w') as f:
        json.dump(channels, f)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    bot.loop.create_task(check_birthday())

@has_permissions(administrator=True)
@bot.slash_command()
async def set_birthday_channel(ctx: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
    guild_id = ctx.guild.id


    channels = load_channels()
    if str(guild_id) in channels and channels[str(guild_id)] != channel.id:
        channels.pop(str(guild_id))
    channels[str(guild_id)] = channel.id
    save_channels(channels)

    await ctx.response.send_message(f"Birthday channel set to {channel.mention}")


@bot.slash_command()
async def add_birthday(ctx: disnake.ApplicationCommandInteraction, birthday: str):
    user = {
        "_id": ctx.author.id,
        "birthday": birthday,
        "guild_id": ctx.guild.id
    }
    if collection.find_one({"_id": ctx.author.id}) is None:
        collection.insert_one(user)
    else:
        query = {"_id": ctx.author.id, "guild_id": ctx.guild.id}
        update = {"$set": {"birthday": birthday}}
        collection.update_one(query, update)
    await ctx.response.send_message("Birthday added successfully!")

@bot.slash_command()
async def remove_birthday(ctx: disnake.ApplicationCommandInteraction):
    query = {"_id": ctx.author.id}
    collection.delete_one(query)
    await ctx.response.send_message("Birthday removed successfully!")

async def check_birthday():
    while True:
        today = datetime.datetime.now().strftime("%d/%m")
        users = collection.find({"birthday": today})
        for user in users:
            channel = bot.get_channel(load_channels().get(str(user["guild_id"])))
            member = await bot.fetch_user(user["_id"])
            if load_channels().get(str(user["guild_id"])) is not None:
                await channel.send(f"Happy Birthday to {member.mention}!")
            else:
                guild = await bot.fetch_guild(user["guild_id"])
                guild_name = guild.name
                print(f"Channel not found for guild {guild_name}")
        await asyncio.sleep(3600)


def main():
    bot.run(os.getenv('DISCORD_TOKEN'))
    

if __name__ == "__main__":
    main()