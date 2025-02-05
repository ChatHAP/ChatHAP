from typing import NoReturn
from datetime import datetime

def strtobool(val) -> bool:
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError("invalid truth value %r" % (val,))

# Get the current time
def get_time():
    timestamp_str = datetime.now().isoformat()
    timestamp = datetime.fromisoformat(timestamp_str)
    formattedTime = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return formattedTime

def assert_exhaustiveness(x: NoReturn) -> NoReturn:
  """Provide an assertion at type-check time that this function is never called."""
  raise AssertionError(f"Invalid value: {x!r}")