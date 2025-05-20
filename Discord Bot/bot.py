import ssl
import certifi
import discord
import aiohttp
import json
import requests

def get_meme():
   response = requests.get('https://meme-api.com/gimme')
   json_data = json.loads(response.text)
   return json_data['url']
   
ssl_context = ssl.create_default_context(cafile=certifi.where())

class MyClient(discord.Client):
  async def on_ready(self):
    print('Logged on as {0}!'.format(self.user))

  async def on_message(self, message):
    if message.author == self.user:
      return

    if message.content.startswith('meme'):
      await message.channel.send(get_meme())

intents = discord.Intents.default()
intents.message_content = True

async def main():
    async with aiohttp.ClientSession() as session:
        client = MyClient(intents=intents)
        await client.start('MTM1MTYwNjQyMzg0NjUyMjk1MA.GFQQA2.nqJU2z1IXJd5j7iV0ACQsM3kCRc_exYTGDu89w', reconnect=True)

import asyncio
asyncio.run(main())