import argparse
import asyncio
from gtts import gTTS
import logging
import os
import re
import sys
import time
from typing import List, Optional

import discord

from bot_token import TOKEN
from settings import AUTO_REPLY


COMMAND_PREFIX = '!kyu'
GTTS_LANGUAGE = 'zh-TW'
TEXT_ENTER_VOICE_CHANNEL = '進入頻道'
TEXT_LEAVE_VOICE_CHANNEL = '離開頻道'


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

      if commands[0] == 'say':
        text = ' '.join(commands[1:])
        voice_client = discord.utils.get(self.voice_clients, guild=message.guild)
        if voice_client:
          await self._Speech(voice_client, text)

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
        await self._Speech(
            voice_client, f'{member.display_name}{TEXT_ENTER_VOICE_CHANNEL}')
    elif before.channel is not None and after.channel is None:
      logging.info('%s left %s.', member.display_name, before.channel.name)
      if before.channel.id == voice_client.channel.id:
        await self._Speech(
            voice_client, f'{member.display_name}{TEXT_LEAVE_VOICE_CHANNEL}')
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
        await self._Speech(
            voice_client, f'{member.display_name}{TEXT_LEAVE_VOICE_CHANNEL}')
      if after.channel.id == voice_client.channel.id:
        await self._Speech(
            voice_client, f'{member.display_name}{TEXT_ENTER_VOICE_CHANNEL}')

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

    voice_client = discord.utils.get(self.voice_clients, guild=message.guild)
    if commands[0] == 'voice_join':
      if message.author.voice and message.author.voice.channel:
        if voice_client:
          await voice_client.disconnect()
        await message.author.voice.channel.connect()
    if commands[0] == 'voice_kick':
      if message.author.voice and message.author.voice.channel:
        if voice_client:
          await voice_client.disconnect()

  async def _Speech(self, voice_channel, text: str):
    audio_filename = os.path.join('sounds', f'{int(time.time() * 1000000)}.mp3')

    # Process Discord Emojis to be without ID number.
    matches = re.finditer(r'<:(.*?):[0-9]+>', text)
    for match in matches:
      text = text.replace(match.group(0), f' {match.group(1)} ')
    logging.info(f'Processed text: {text}')

    # Wait until the previous one is played.
    while voice_channel.is_playing():
      await asyncio.sleep(1)

    gTTS(text, lang=GTTS_LANGUAGE).save(audio_filename)
    voice_channel.play(discord.FFmpegPCMAudio(audio_filename))
    while voice_channel.is_playing():
      await asyncio.sleep(1)
    os.remove(audio_filename)


def Main(args: argparse.Namespace):
  intents = discord.Intents.default()
  intents.message_content = True
  intents.voice_states = True

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
