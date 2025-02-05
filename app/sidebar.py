import streamlit as st
import os
import sys
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("ChatHAP")

# if "key_counter_reset" not in st.session_state: # causes importerror
#     st.session_state.key_counter_reset = 1

def reset_conversation():
    st.session_state["messages"] = [{"role": "assistant", "content": "Welcome to the ChatHAP! I'll assist you in designing a vibration through conversation. How can I help you?"}]

    conversation_history = []
    parameter_history = []
    feature_history = []
    feature_current_str = ""
    current_signal = []
    current_t = []

    st.session_state.plot_counter = 1

    logger.debug("Clear Conversation")
    # logger.debug(f"key_counter:reset: {st.session_state.key_counter}")

    st.session_state.key_counter_reset = st.session_state.key_counter

def sidebar():
    with st.sidebar:
        st.button('Clear Conversation', on_click=reset_conversation)
        st.markdown(
            "## How to use\n"
            "1. Describe a vibration that you want to create using your natural language.\n"
            "2. You can look the designed vibration waveform and feel it by clicking a button.\n"
            "3. Enjoy interactions with ChatHAP.\n"
        )

        st.markdown("---")
        st.markdown("# About")
        st.markdown(
            "💬ChatHAP allows you to create a vibration using a conversation. "
        )
        st.markdown(
            "This tool is a work in progress. "
        )
        st.markdown("Made by a collaboration between [TEAL](https://hastiseifi.com/) and [HAM](http://ham.gist.ac.kr/)")
        st.markdown("---")

        # st.markdown(
        #         """
        # # FAQ
        # ## How does ChatHAP work?
        # XXX

        # ## Is my data safe?
        # XXX
        # """
        # )