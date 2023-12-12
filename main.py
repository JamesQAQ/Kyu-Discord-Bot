import argparse
import discord
import logging
import os
import sys
from typing import List, Optional

from bot_token import DEV_TOKEN, PROD_TOKEN
from settings import AUTO_REPLY
from voice_client import VoiceClient


COMMAND_PREFIX = '!kyu'


class KyuDiscordBot(discord.Client):

  async def on_ready(self):
    logging.info(f'Logged on as {self.user}!')
    self._voice_client = VoiceClient(self)

  async def on_message(self, message: discord.Message):
    if self.user == message.author:
      return
    logging.info(f'Message from {message.author}: {message.content}')

    commands = [part for part in ' '.join(message.content.split()).split(' ')]
    if commands[0] == COMMAND_PREFIX:
      commands = commands[1:]
      await self._HandleCommand(message, commands)

  async def on_voice_state_update(
      self, member: discord.Member,
      before: discord.VoiceState,
      after: discord.VoiceState):
    voice_client = discord.utils.get(
        self.voice_clients, guild=member.guild)
    if not voice_client or member.id == self.user.id:
      return

    if before.channel is None and after.channel is not None:
      logging.info('%s entered %s.', member.display_name, after.channel.name)
      if after.channel.id == voice_client.channel.id:
        await self._voice_client.MemberEnterVoiceChannel(member)

    elif before.channel is not None and after.channel is None:
      logging.info('%s left %s.', member.display_name, before.channel.name)
      if before.channel.id == voice_client.channel.id:
        await self._voice_client.MemberLeaveVoiceChannel(member)

    elif (
        before.channel is not None
        and after.channel is not None
        and before.channel.id != after.channel.id):
      logging.info(
          '%s moved from %s to %s.',
          member.display_name,
          before.channel.name,
          after.channel.name)
      if before.channel.id == voice_client.channel.id:
        await self._voice_client.MemberLeaveVoiceChannel(member)
      if after.channel.id == voice_client.channel.id:
        await self._voice_client.MemberEnterVoiceChannel(member)

  async def _HandleCommand(self, message: discord.Message, commands: List[str]):
    logging.info('Received commands: %s', commands)
    if commands[0] == 'post':
      reply = AUTO_REPLY[commands[1]]
      content = reply.get('content', '')
      if 'file' in reply:
        with open(reply['file'], 'rb') as f:
          discord_file = discord.File(f)
        await message.channel.send(content, file=discord_file)
      else:
        await message.channel.send(content)

    discord_voice_client = self._voice_client.GetVoiceClient(message.guild)
    if commands[0] == 'voice_join':
      if message.author.voice and message.author.voice.channel:
        if discord_voice_client:
          await discord_voice_client.disconnect()
        await message.author.voice.channel.connect()

    if commands[0] == 'voice_kick':
      if discord_voice_client:
        await discord_voice_client.disconnect()

    if commands[0] == 'say':
      await self._voice_client.Speech(' '.join(commands[1:]), message.guild)


def Main(args: argparse.Namespace):
  intents = discord.Intents.default()
  intents.message_content = True
  intents.voice_states = True

  bot = KyuDiscordBot(intents=intents)
  bot.run(PROD_TOKEN if args.prod else DEV_TOKEN)


if __name__ == '__main__':
  logging.basicConfig(
      stream=sys.stdout,
      level=logging.INFO,
      format='[%(levelname)s] %(asctime)s - %(message)s',
      datefmt='%H:%M:%S')

  parser = argparse.ArgumentParser()
  parser.add_argument('--prod', action='store_true')
  Main(parser.parse_args())
