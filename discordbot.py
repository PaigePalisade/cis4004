import discord
import os
from dotenv import load_dotenv

import json
from time import time
import socketio

import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

load_dotenv() # load all the variables from the env file
bot = discord.Bot(intents=intents)

sio = socketio.AsyncClient()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")
    await sio.connect('http://localhost:5000')
    await sio.emit('discord-init', '')

# receives a message from Discord and sends it to the web app
@bot.event
async def on_message(message):
    # webhooks do not have a display name
    if message.author.global_name:
        pfp = '/static/default_pfp.png'
        if message.author.avatar:
            pfp = message.author.avatar.url
        await sio.emit('discord-message', json.dumps({'username': message.author.name, 'display_name': message.author.display_name, 'pfp': pfp, 'body': message.content, 'channel': str(message.channel.id)}))

# tells the web app to register a bridge between a room and a Discord channel
@bot.slash_command(name="bindchannel", description="bind channel to webhook")
async def bindchannel(ctx: discord.ApplicationContext, room: str):
    future = asyncio.get_event_loop().create_future()
    def ack_callback(response):
        future.set_result(response)
    webhook = (await ctx.channel.create_webhook(name='flask chat')).id
    await sio.emit('create-bridge', json.dumps({'internal_channel': room, 'external_channel': ctx.channel_id, 'webhook': webhook}), callback=ack_callback)
    await ctx.respond(await future)

# tells the web app to remove all bridges with a discord channel id
@bot.slash_command(name='unbind', description='unbind all bridges to this channel')
async def unbind(ctx: discord.ApplicationContext):
    future = asyncio.get_event_loop().create_future()
    def ack_callback(response):
        future.set_result(response)
    await sio.emit('remove-bridge', str(ctx.channel_id), callback=ack_callback)
    await ctx.respond(await future)

# receives a message from the web app and sends it to Discord
@sio.on('new-discord-message')
async def echoMessage(data):
    obj = json.loads(data)
    webhook = await bot.fetch_webhook(int(obj['webhook']))
    if not webhook:
        channel = await bot.fetch_channel(int(obj['channel']))
        if not channel:
            await sio.emit('remove-bridge', obj['channel'])
        webhook = channel.create_webhook(name='flask chat')
    await webhook.send(content=obj['body'], username=obj['display_name'], avatar_url=obj['pfp'])


bot.run(os.getenv('DISCORD_TOKEN'))