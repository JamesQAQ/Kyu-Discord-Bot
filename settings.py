import os


AUTO_REPLY = {
    'test_1': {
        'content': 'Hello world!',
    },
    'test_2': {
        'file': '/path/to',
    },
}

VITS_DATA_DIR = os.path.join('.', 'path', 'to')

def _GenerateDefaultConfigPath(speaker: str):
  return os.path.join(VITS_DATA_DIR, speaker, 'finetune_speaker.json')

def _GenerateDefaultModelPath(speaker: str):
  return os.path.join(VITS_DATA_DIR, speaker, 'G_latest.pth')

def _GenerateDefaultImagePath(speaker: str):
  return os.path.join(VITS_DATA_DIR, speaker, 'avatar.jpg')

VITS_SETTING = {
    '語音名稱': {
        'speaker': 'character',
        'config_path': _GenerateDefaultConfigPath('character'),
        'model_path': _GenerateDefaultModelPath('character'),
        'description': 'A simple description for this model.',
        'image_path': _GenerateDefaultImagePath('character'),
    },
}
