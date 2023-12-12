import asyncio
import discord
from gtts import gTTS
import logging
import os
import re
import time


GTTS_LANGUAGE = 'zh-TW'
TEXT_ENTER_VOICE_CHANNEL = '進入頻道'
TEXT_LEAVE_VOICE_CHANNEL = '離開頻道'


class VoiceClient:

  def __init__(self, discord_client: discord.Client):
    self._discord_client = discord_client

  async def MemberEnterVoiceChannel(self, member: discord.Member):
    await self.Speech(
        f'{member.display_name}{TEXT_ENTER_VOICE_CHANNEL}', member.guild)

  async def MemberLeaveVoiceChannel(self, member: discord.Member):
    await self.Speech(
        f'{member.display_name}{TEXT_LEAVE_VOICE_CHANNEL}', member.guild)

  async def Speech(self, text: str, guild: discord.Guild):
    voice_client = self.GetVoiceClient(guild)
    if voice_client:
      audio_filename = self._GenerateAudioFile(
          self._ProcessCustomizedEmojis(text))
      # Wait until the previous one is played.
      while voice_client.is_playing():
        await asyncio.sleep(1)
      voice_client.play(discord.FFmpegPCMAudio(audio_filename))
      while voice_client.is_playing():
        await asyncio.sleep(1)
      os.remove(audio_filename)

  def GetVoiceClient(self, guild: discord.Guild):
    return discord.utils.get(self._discord_client.voice_clients, guild=guild)

  def _ProcessCustomizedEmojis(self, text: str) -> str:
    matches = re.finditer(r'<:(.*?):[0-9]+>', text)
    for match in matches:
      text = text.replace(match.group(0), f' {match.group(1)} ')
    logging.info(f'Processed text without the dicord emoji format: {text}')
    return text

  def _GenerateAudioFile(self, text: str) -> str:
    audio_filename = os.path.join('sounds', f'{int(time.time() * 1000000)}.mp3')
    gTTS(text, lang=GTTS_LANGUAGE).save(audio_filename)
    return audio_filename
