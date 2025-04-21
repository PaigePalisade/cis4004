import discord
import os # default module
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

load_dotenv() # load all the variables from the env file
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.event
async def on_message(message):
    # webhooks do not have a display name
    if message.author.global_name:
        print(message.content)
        print(f"username: @{message.author.name}")
        print(f"display name: {message.author.global_name}")
        print(f"avatar: {message.author.avatar}")

async def send_discord_message(display_name, pfp, body, channel):
    webhook = await bot.fetch_channel(int(channel)).channel.create_webhook(name="temp webhook")
    await webhook.send(content=body, username=display_name, avatar_url=pfp)
    await webhook.delete()

@bot.slash_command(name="bindchannel", description="bind channel to webhook")
async def bindchannel(ctx: discord.ApplicationContext):
    webhook = await ctx.channel.create_webhook(name="test webhook")
    await webhook.send(content="Hello this is a test", username="Paige West", avatar_url="https://docs.pycord.dev/en/stable/_static/pycord_logo.png")
    await webhook.delete()

bot.run(os.getenv('DISCORD_TOKEN')) # run the bot with the token