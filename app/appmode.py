from .utilities import strtobool
from enum import Enum
import os


class AppMode(Enum):
    DEBUG = 0 # NO PLAYBACK, KEEP PARAMETERS IN GPT RESPONSE
    TEST = 1

CH_APP_MODE: AppMode = AppMode.DEBUG # set via CH_APP_MODE environment variable (or in .env file)
match os.getenv("CH_APP_MODE", "DEBUG").upper():
    case "DEBUG":
        CH_APP_MODE = AppMode.DEBUG
    case "TEST":
        CH_APP_MODE = AppMode.TEST
    case _:
        raise ValueError("Invalid value for CH_APP_MODE. Please set it to 'DEBUG' or 'TEST'.")
    
# CH_APP_MODE: AppMode = AppMode.TEST # set via CH_APP_MODE environment variable (or in .env file)

CH_DISABLE_OPENAI = strtobool(os.getenv("CH_DISABLE_OPENAI", "false")) # set via CH_DISABLE_OPENAI environment variable (or in .env file)

CH_DISABLE_FIREBASE = strtobool(os.getenv("CH_DISABLE_FIREBASE", "false")) # set via CH_DISABLE_FIREBASE environment variable (or in .env file)