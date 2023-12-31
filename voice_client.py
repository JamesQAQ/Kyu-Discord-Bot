import asyncio
import discord
import enum
from gtts import gTTS
import logging
import os
import re
import requests
import subprocess
import time

from settings import VITS_SETTING


GTTS_LANGUAGE = 'zh-TW'
GTTS_LANGUAGE_JP = 'ja'
GTTS_LANGUAGE_EN = 'en-US'
VITS_LANGUAGE = '简体中文'
VITS_LANGUAGE_JP = '日本語'
VITS_LANGUAGE_EN = 'English'
TEXT_ENTER_VOICE_CHANNEL = '進入頻道'
TEXT_LEAVE_VOICE_CHANNEL = '離開頻道'
TEXT_ENTER_VOICE_CHANNEL_JP = 'がチャンネルに入る'
TEXT_LEAVE_VOICE_CHANNEL_JP = 'がチャンネルを退出する'
VITS_SET_UP_TEXT = 'テスト'


class Language(enum.Enum):
  DEFAULT = 1
  JAPANESE = 2
  ENGLISH = 3


class VoiceClient:

  def __init__(
      self, discord_client: discord.Client, web_inference_port: int = 8080):
    self._discord_client = discord_client
    self._voice_name = 'gtts'
    self._length_scale = 1
    self._web_inference_url = f'http://localhost:{web_inference_port}/'

  async def MemberEnterVoiceChannel(self, member: discord.Member):
    text = TEXT_ENTER_VOICE_CHANNEL
    lang = Language.DEFAULT
    if self._voice_name != 'gtts':
      text = TEXT_ENTER_VOICE_CHANNEL_JP
      lang = Language.JAPANESE
    await self.Speech(f'{member.display_name}{text}', member.guild, lang)

  async def MemberLeaveVoiceChannel(self, member: discord.Member):
    text = TEXT_LEAVE_VOICE_CHANNEL
    lang = Language.DEFAULT
    if self._voice_name != 'gtts':
      text = TEXT_LEAVE_VOICE_CHANNEL_JP
      lang = Language.JAPANESE
    await self.Speech(f'{member.display_name}{text}', member.guild, lang)

  async def SetVoice(
      self, voice_name: str,
      guild: discord.Guild,
      channel: discord.TextChannel):
    if voice_name == 'gtts' or voice_name in VITS_SETTING:
      self._voice_name = voice_name
      if voice_name == 'gtts':
        await channel.send('Set voice with `Google Text-to-Speech`')
      else:
        config_path = VITS_SETTING[voice_name]['config_path']
        model_path = VITS_SETTING[voice_name]['model_path']
        speaker = VITS_SETTING[voice_name]['speaker']
        self._CallWebInference(f'set{config_path},{model_path},{speaker}')

        discord_file = None
        if 'image_path' in VITS_SETTING[voice_name]:
          with open(VITS_SETTING[voice_name]['image_path'], 'rb') as f:
            discord_file = discord.File(f)
        await channel.send(
          f'Set voice with `{voice_name}`.\n'
              + VITS_SETTING[voice_name].get('description', ''),
          file=discord_file)
        await self.Speech(VITS_SET_UP_TEXT, guild, Language.JAPANESE)
    else:
      await channel.send(f'Unrecognized voice name: `{voice_name}`.')

  async def SetSpeed(self, length_scale_str: str, channel: discord.TextChannel):
    try:
      self._length_scale = float(length_scale_str)
      await channel.send(f'Set speed(length_scale) with `{self._length_scale}`.')
    except ValueError as e:
      await channel.send(f'ValueError: {str(e)}')

  async def Speech(
      self,
      text: str,
      guild: discord.Guild,
      lang: Language = Language.DEFAULT,
      channel: discord.TextChannel = None):
    if self._voice_name != 'gtts':
      if (lang == Language.ENGLISH
          and 'E' not in VITS_SETTING[self._voice_name]['pretrained_model']):
        await channel.send(
            'Warning: English is not supported for current voice name '
                + f'`{self._voice_name}`.')
    voice_client = self.GetVoiceClient(guild)
    if voice_client:
      audio_filename = self._GenerateAudioFile(
          self._ProcessCustomizedEmojis(text), lang)
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

  def _GenerateAudioFile(self, text: str, lang: Language) -> str:
    if self._voice_name == 'gtts':
      return self._GenerateAudioFileByGtts(text, lang)
    return self._GenerateAudioFileByVits(self._voice_name, text, lang)

  def _GenerateAudioFileByGtts(self, text: str, lang: Language) -> str:
    audio_filename = os.path.join('output', f'{int(time.time() * 1000000)}.mp3')
    lang_value = GTTS_LANGUAGE
    if lang == Language.JAPANESE:
      lang_value = GTTS_LANGUAGE_JP
    if lang == Language.ENGLISH:
      lang_value = GTTS_LANGUAGE_EN
    gTTS(text, lang=lang_value).save(audio_filename)
    return audio_filename

  def _GenerateAudioFileByVits(
      self, voice_name: str, text: str, lang: Language) -> str:
    audio_filename = f'{int(time.time() * 1000000)}'
    lang_value = VITS_LANGUAGE
    if lang == Language.JAPANESE:
      lang_value = VITS_LANGUAGE_JP
    if lang == Language.ENGLISH:
      lang_value = VITS_LANGUAGE_EN
    audio_path = os.path.join('output', 'vits', f'{audio_filename}.wav')
    self._CallWebInference(
        f'generate{lang_value},{audio_filename},{self._length_scale},{text}')
    return audio_path

  def _CallWebInference(self, input_data: str):
    requests.post(self._web_inference_url, data=input_data.encode())
