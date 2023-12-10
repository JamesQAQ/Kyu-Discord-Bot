import argparse
import logging
import sys
from typing import List

import discord

from bot_token import TOKEN
from settings import AUTO_REPLY


COMMAND_PREFIX = '!kyu'


class KyuDiscordBot(discord.Client):

  async def on_ready(self):
    logging.info(f'Logged on as {self.user}!')

  async def on_message(self, message: discord.Message):
    if self.user == message.author:
      return
    logging.info(f'Message from {message.author}: {message.content}')

    commands = [part for part in ' '.join(message.content.split()).split(' ')]
    if commands[0] == COMMAND_PREFIX:
      commands = commands[1:]
      await self._HandleCommand(message, commands)

  async def _HandleCommand(self, message: discord.Message, commands: List[str]):
    logging.info('Received commands: %s', commands)
    if commands[0] in AUTO_REPLY:
      reply = AUTO_REPLY[commands[0]]
      content = reply.get('content', '')
      if 'file' in reply:
        with open(reply['file'], 'rb') as f:
          discord_file = discord.File(f)
        await message.channel.send(content, file=discord_file)
      else:
        await message.channel.send(content)


def Main(args: argparse.Namespace):
  intents = discord.Intents.default()
  intents.message_content = True

  bot = KyuDiscordBot(intents=intents)
  bot.run(TOKEN)


if __name__ == '__main__':
  logging.basicConfig(
      stream=sys.stdout,
      level=logging.INFO,
      format='[%(levelname)s] %(asctime)s - %(message)s',
      datefmt='%H:%M:%S')

  parser = argparse.ArgumentParser()
  Main(parser.parse_args())
