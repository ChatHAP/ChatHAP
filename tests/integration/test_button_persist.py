import io
import sys
import os
from streamlit.testing.v1 import AppTest
# from contextlib import redirect_stdout

import logging

class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_records = []

    def emit(self, record):
        self.log_records.append(record)

def test_button_persist():
	# set CH_APP_MODE=0
	os.environ['CH_APP_MODE'] = 'DEBUG'
	os.environ['CH_DISABLE_OPENAI'] = 'yes'

	at = AppTest.from_file('../../app/main.py')
	at.run()
	assert not at.exception

	at.chat_input[0].set_value('hello').run()
	# check if last chat_message is from the "assistant"
	assert at.chat_message[-1].name == 'assistant'

	assert len(at.button) == 1
	assert at.button[-1].key == 'Button1_play'

	assert all(md.value != "Vibration activated." for md in at.markdown) # asset no "Vibration activated."

	at.button[-1].click().run()

	assert any(md.value == "Vibration activated." for md in at.markdown) # asset has "Vibration activated."

	# check if button is still there with same key
	assert len(at.button) == 1
	assert at.button[-1].key == 'Button1_play'
