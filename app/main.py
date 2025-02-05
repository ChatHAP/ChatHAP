from enum import Enum
import io
from pathlib import Path
import sys
import zipfile
import nidaqmx.constants
import nidaqmx.stream_writers
import numpy as np
from numpy.typing import NDArray
import threading
import time
import pandas as pd
import os
import re
import streamlit as st
import base64
from PIL import Image
from datetime import datetime
from dotenv import load_dotenv
import logging
import json
import wave
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
import tiktoken

load_dotenv()

if __name__ == '__main__' and __package__ is None:
    file = Path(__file__).resolve()
    parent, top = file.parent, file.parents[3]

    sys.path.append(str(top))
    try:
        sys.path.remove(str(parent))
    except ValueError: # Already removed
        pass

    __package__ = 'app'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


from .appmode import AppMode, CH_APP_MODE, CH_DISABLE_OPENAI
from .genSignal import GenSignalInput, genSignal_direct, SAMPLE_RATE, GAIN
from .vizSignal import visSignal_st
from .langinterface import GenerationApproach, NavigationApproach, ModifyApproach, chat_chatgpt
from .navsignal import navSignal, modifySignal
from .globalVariable import *
from .firebase_users import *
from .sidebar import sidebar


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("ChatHAP")
match CH_APP_MODE:
    case AppMode.DEBUG:
        logger.setLevel(logging.DEBUG)
    case AppMode.TEST:
        logger.setLevel(logging.INFO)

# logger.info(CH_APP_MODE)

if CH_DISABLE_OPENAI is False:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY is None:
        raise ValueError("Please set the `OPENAI_API_KEY` environment variable or create a .env file with the API key.")

st.set_page_config(
    page_title="ChatHAP",
    page_icon="👋",
)



def activateDAQ(data, dur):
    if len(data) > 0 and dur > 0:
        if CH_APP_MODE == AppMode.DEBUG:
            logger.debug("skipping vibration playback (CH_APP_MODE==AppMode.DEBUG).")
        else:
            ###################################
            ### Code for playing vibrations.###
            with nidaqmx.Task() as task:
                ch = task.ao_channels.add_ao_voltage_chan("Dev2/ao0")
                task.timing.cfg_samp_clk_timing(SAMPLE_RATE, sample_mode=nidaqmx.constants.AcquisitionType.FINITE, samps_per_chan=int(SAMPLE_RATE*dur))
                test_writer = nidaqmx.stream_writers.AnalogMultiChannelWriter(
                    task.out_stream,
                    auto_start=True # type: ignore
                )
                test_writer.write_many_sample(data)
                task.wait_until_done(timeout=1000)
            ###################################
            logger.debug("Vibration was successfully played.")
    else:
        logger.warning("Data is empty. Cannot play vibration.")



initialize_firebase_users()
# backup_data()
st.title("💬 ChatHAP")
st.caption("🚀 A chatbot developed by researchers at Arizona State University in the United States and the Gwangju Institute of Science and Technology in South Korea.")

# Ensure user_id is created and stored in session state
if "user_id" not in st.session_state:
    user_id = add_data()
    st.session_state["user_id"] = user_id
    logger.debug(f'user_id: {user_id}')

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Welcome to the ChatHAP! I'll assist you in designing a vibration through conversation. How can I help you?"}]

if "plot_counter" not in st.session_state:
    st.session_state["plot_counter"] = 1

if "key_counter" not in st.session_state:
    st.session_state["key_counter"] = 1
    # logger.debug(f"key_counter:initialization: {st.session_state.key_counter}")

if "key_counter_reset" not in st.session_state:
    st.session_state.key_counter_reset = 1

if "vote_clicked" not in st.session_state:
    st.session_state["vote_clicked"] = 0

if "processing" not in st.session_state:
    st.session_state["processing"] = False

sidebar()

class Vote(Enum):
    THUMBS_UP = "👍"
    THUMBS_DOWN = "👎"

handleMessage = "Please explain more details of vibrations in different ways."
conversation_history = []
parameter_history = []
feature_history = []
current_signal: list[np.ndarray] = []
current_t: list[np.ndarray] = []
current_resource = []

# delete_data("4ab79e56-33cf-485e-ba4a-eae836ccd6fa")

for i, msg in enumerate(st.session_state["messages"]):

    if i == 0:
        st.session_state["plot_counter"] = 1
        st.session_state.key_counter = st.session_state.key_counter_reset

    if msg["role"] != "image" and msg["role"] != "parameter" and msg["role"] != "feature" and msg["role"] != "modify":
        st.chat_message(msg["role"]).write(msg["content"])
        conversation_history.append({"role": msg["role"], "content": msg["content"]})

    if msg["role"] == "image":
        caption = f"Plot{st.session_state.plot_counter}"
        st.image(msg["content"], caption=caption, use_column_width=True)

        st.session_state.plot_counter += 1

    if msg["role"] == "parameter" or msg["role"] == "feature" or msg["role"] == "modify":
        # Approach: PARAMETER
        if msg["role"] == "parameter":
            generation_parameters: GenSignalInput = msg["content"]
            parameter_history.append({"role": "parameter", "content": generation_parameters, "time": str(datetime.now())})
            signal, t, duration = genSignal_direct(generation_parameters) # type: ignore

            t = np.array([t])

            # csv_signal_params = pd.DataFrame({"Amplitude": [parameter_list[0]], "Amplitude Variation1": [parameter_list[1]], "Amplitude Variation2": [parameter_list[2]], "Frequency": [parameter_list[3]], "Duration": [parameter_list[4]], "The number of pulses": [parameter_list[5]]})
            csv_signal_params = pd.DataFrame({
                "A": [generation_parameters.A],
                "A_W_option": [generation_parameters.A_W_option],
                "A_E_option": [generation_parameters.A_E_option],
                "freq_c": [generation_parameters.freq_c],
                "freq_e": [generation_parameters.freq_e],
                "dur": [generation_parameters.dur],
                "rhythm": [generation_parameters.rhythm],
            }).to_csv(index=False)

            generation_parameters_list = [generation_parameters.A, generation_parameters.A_W_option, generation_parameters.A_E_option, generation_parameters.freq_c, generation_parameters.freq_e, generation_parameters.dur, generation_parameters.rhythm]
            generation_parameters_list_string = '-'.join(map(lambda x: str(x).replace('.', '_'), generation_parameters_list))
            current_resource.append(generation_parameters_list_string)

        # Approach: NAVIAGATION
        if msg["role"] == "feature":
            signal = np.array([np.array(msg["signal"])])
            t = np.array([np.array(msg["t"])])

            duration = msg["duration"]

            csv_signal_params = pd.DataFrame({
                "feature": [msg["featureList"]]
            }).to_csv(index=False)

            current_resource.append(msg["resource"])

        # Approach: MODIFY
        if msg["role"] == "modify":
            signal = np.array([np.array(msg["signal"])])
            t = np.array([np.array(msg["t"])])

            duration = msg["duration"]

            csv_signal_params = pd.DataFrame({
                "modified": [msg["approach"]]
            }).to_csv(index=False)

        current_signal.append(signal)
        current_t.append(t)

        # bc1, bc2, bc3, bc4, bc5 = st.columns([1,1,1,1,1])
        bc1, bc2, bc3, bc4, bc5 = st.columns([1,1,1,1,1])

        with bc1:
            key_button = f"Button{st.session_state.key_counter}"
            if st.button("  Play   Vibration", key = key_button+"_play", use_container_width=True):
                activateDAQ(signal, duration)

                st.write("Vibration activated.")


        # with bc2:
        #     if st.download_button("Download Parameters", csv_signal_params, f"vibration_{st.session_state.key_counter}.csv", use_container_width=True):
        #         st.write("Downloaded vibration data.")

        # with bc2:
        #     # streamlit does not allow downloading multiple files, and also does not yet support dialog box modals, so im just gonna zip both together for now
        #     zbuf = io.BytesIO()
        #     with zipfile.ZipFile(zbuf, "x") as z:
        #         # create wav file
        #         buffer = io.BytesIO()
        #         signali16 = np.int16((signal / GAIN) * 32767).tobytes() # idk if this is correct (i tried to make it match the vis plot) CM pls check
        #         with wave.open(buffer, "wb") as wav_file:
        #             wav_file.setnchannels(1)
        #             wav_file.setsampwidth(2)
        #             wav_file.setframerate(SAMPLE_RATE)
        #             wav_file.writeframes(signali16)
        #         signal_wav = buffer.getvalue()
        #         z.writestr(f"vibration_signal_{st.session_state.key_counter}.wav", signal_wav)

        #         # create json file
        #         z.writestr(f"vibration_signal_{st.session_state.key_counter}.json", json.dumps({
        #             "sample_rate": SAMPLE_RATE,
        #             "duration": duration,
        #             "data": signal.squeeze().tolist() # idk if we want to adjust this for GAIN or not
        #         }))

        #     if st.download_button("Download Signal", zbuf, f"vibration_signal_{st.session_state.key_counter}.zip", use_container_width=True):
        #         st.write("Downloaded signal wav.")

        with bc3:
            # msg["vote"] = st.select_slider("Rate this vibration", options=["👍", "", "👎"], key=key_button+"_rate", value=msg.get("vote", ""))

            options = [Vote.THUMBS_UP.value, Vote.THUMBS_DOWN.value]
            vote_index_map = {Vote.THUMBS_UP.value: 0, Vote.THUMBS_DOWN.value: 1}

            curr_vote = msg.get("vote", "")
            radio_index = vote_index_map.get(curr_vote, None)

            def on_change_vote(msg: dict, key_button: str, key_counter: int, vote_clicked: int): # needed to use on_change to avoid some glitches with the radio widget state
                msg["vote"] = st.session_state[key_button+"_rate"]
                logger.debug(f"Vote for Signal{st.session_state.key_counter}: {msg['vote']}")
                st.session_state.vote_clicked += 1
                logger.debug(f"Clicked: {st.session_state.vote_clicked}")
                st.session_state.processing = True

            st.radio("Rate this vibration", options, key=key_button+"_rate", horizontal=True, index=radio_index, on_change=on_change_vote, args=(msg, key_button, st.session_state.key_counter, st.session_state.vote_clicked))

            temp_rating = 0
            if curr_vote == "👍":
                temp_rating = 1
            elif curr_vote == "👎":
                temp_rating = -1
            else:
                temp_rating = 0

            content_rating = {"rating": temp_rating}
            update_rating(st.session_state["user_id"], f'vibration_{st.session_state.key_counter}', content_rating)

            if i == len(st.session_state["messages"]) - 1 and st.session_state["processing"] == True:
                with st.spinner("Updating Rating..."):
                    update_vibration_rating(st.session_state["user_id"], msg["role"], f'vibration_{st.session_state.key_counter}', st.session_state.vote_clicked, temp_rating)
                    st.session_state["processing"] = False

        with bc5:
            submit_button = f"Button{st.session_state.key_counter}"
            if st.button("  Submit   Vibration", key = submit_button+"_submit", use_container_width=True):
                current_time = get_time()
                user_id = st.session_state.get("user_id")
                if msg["role"] == "parameter":
                    content = {"approach": "parameter", "resource": current_resource[-1], "time": current_time}
                if msg["role"] == "feature":
                    content = {"approach": "navigation", "resource": msg["resource"], "time": current_time}
                if msg["role"] == "modify":
                    content = {"approach": "modify", "resource": current_resource[-1], "time": current_time}

                with st.spinner("Submitting Vibration..."):
                    submit_signal_data(user_id, content, signal, t, st.session_state.key_counter)
                    st.write("Vibration submitted.")

        st.session_state.key_counter += 1



if prompt := st.chat_input():
    current_time = get_time()
    user_id = st.session_state.get("user_id")

    if "vote_clicked" in st.session_state:
        st.session_state["vote_clicked"] = 0

    st.session_state.messages.append({"role": "user", "content": prompt})
    conversation_history.append({"role": "user", "content": prompt, "time": str(datetime.now())})
    # prompt_added = "\n\n".join([message["content"] for message in conversation_history])
    # map role: user to ("human", prompt) and role: assistant to ("ai", msg)
    conversation_history_langchain: list[BaseMessage] = []
    for message in conversation_history:
        if message["role"] == "user":
            conversation_history_langchain.append(HumanMessage(content=message["content"]))
        elif message["role"] == "assistant":
            conversation_history_langchain.append(AIMessage(content=message["content"]))
        else:
            conversation_history_langchain.append(SystemMessage(content=message["content"]))

    with st.spinner("Thinking..."):
        msg = chat_chatgpt(conversation_history_langchain)

        msg_content = msg.response_msg

        if msg_content is not None:
            st.session_state.messages.append({"role": "assistant", "content": msg_content })
            conversation_history.append({"role": "assistant", "content": msg_content, "time": str(datetime.now())})
            conversation_history_langchain.append(AIMessage(content=msg_content))

        if user_id:
            update_conversation(user_id, {"role": "user", "content": prompt, "vibration": f'vibration_{st.session_state.key_counter}', "time": str(datetime.now())})
            if msg_content is not None:
                update_conversation(user_id, {"role": "assistant", "content": msg_content, "vibration": f'vibration_{st.session_state.key_counter}', "time": str(datetime.now())})
        else:
            logger.error("user_id is not defined in session state")


        if isinstance(msg.approach, GenerationApproach):
            logger.debug("Approach: PARAMETER_LIST")

            gen_params = msg.approach.generation_parameters
            gen_change = msg.approach.generation_change

            logger.debug(f"generation_parameters: {gen_params}")
            logger.debug(f"generation_change: {gen_change}")

            if gen_change is not None:
                changes_list = [gen_change.target_feature, gen_change.selected_parameter, gen_change.changed_parameter_direction]
                change_list_string = [change.value for change in changes_list]

                # Need to refine code and prompt later
                if gen_change.target_feature.value == "Pleasant or Positive":
                    if gen_change.selected_parameter.value == "Amplitude":
                        if gen_change.changed_parameter_direction.value == "POSITIVE":
                            gen_params.A = min(gen_params.A*1.5, 1.0)
                        elif gen_change.changed_parameter_direction.value == "NEGATIVE":
                            gen_params.A = max(gen_params.A*0.5, 0)
                    elif gen_change.selected_parameter.value == "Rhythm":
                        if gen_change.changed_parameter_direction.value == "POSITIVE":
                             gen_params.rhythm = max(int(gen_params.rhythm * 0.5), 0)
                        elif gen_change.changed_parameter_direction.value == "NEGATIVE":
                            gen_params.rhythm = min(int(gen_params.rhythm * 2), MAX_RHYTHM)

                elif gen_change.target_feature.value == "Exciting or Urgent" or gen_change.target_feature.value == "Roughness":
                    if gen_change.selected_parameter.value == "Amplitude":
                        if gen_change.changed_parameter_direction.value == "POSITIVE":
                            gen_params.A = min(gen_params.A*1.5, 1.0)
                        elif gen_change.changed_parameter_direction.value == "NEGATIVE":
                            gen_params.A = max(gen_params.A*0.5, 0)
                    elif gen_change.selected_parameter.value == "Duration":
                        if gen_change.changed_parameter_direction.value == "POSITIVE":
                            gen_params.dur = min(gen_params.dur*1.5, MAX_DURATION)
                        elif gen_change.changed_parameter_direction.value == "NEGATIVE":
                            gen_params.dur = max(gen_params.dur*0.5, 0)
                logger.debug(f"Generated signal with updated parameters: {gen_params}")
            else:
                changes_list = []
                change_list_string = []

            # Create vibrations
            signal, t, duration = genSignal_direct(gen_params)
            parameter_history.append({"role": "parameter", "content": gen_params, "time": str(datetime.now())})

            parameter_list = [gen_params.A, gen_params.A_W_option, gen_params.A_E_option, gen_params.freq_c, gen_params.freq_e, gen_params.dur, gen_params.rhythm]
            parameter_list_string = '-'.join(map(lambda x: str(x).replace('.', '_'), parameter_list))
            content = {"approach": "parameter", "change": f"{change_list_string}", "resource": parameter_list_string, "time": current_time}

            update_signal_data(user_id, content, signal, t, st.session_state.key_counter)

            # Visualization
            plot = visSignal_st(signal, t)
            if plot:
                caption = f"Plot{st.session_state.plot_counter}"
                st.session_state.messages.append({"role": "image", "content": plot, "caption": caption})
                st.session_state.messages.append({"role": "parameter", "content": gen_params})
            else:
                logger.warning("No parameter list found in response")

        elif isinstance(msg.approach, NavigationApproach):
            logger.debug("Approach: NAVIGATION")

            signal_list: list[np.ndarray] = []
            t_list: list[np.ndarray] = []
            duration_list: list[float] = []
            resourceLists: list[str] = []
            featureLists: list[str] = []
            importanceLists: list[float] = []
            nav_reason: str = ""


            with st.spinner("Querying signal database..."):
                # signal_list, t_list, duration_list, resourceLists, featureLists, nav_reason = navSignal(msg.approach)
                try:
                    result = navSignal(msg.approach)
                    if result is None:
                        logger.error("navSignal returned None, no resources were found.")
                        st.session_state.messages.append({"role": "assistant", "content": handleMessage})
                        if user_id:
                            update_conversation(user_id, {"role": "assistant", "content": handleMessage, "vibration": f'vibration_{st.session_state.key_counter}', "time": current_time})

                            content_noResponse = {"role": "user", "approach": "navigation", "content": prompt, "vibration": f'vibration_{st.session_state.key_counter}', "time": current_time}
                            update_noResponse_data(user_id, content_noResponse, st.session_state.key_counter) # type: ignore
                        else:
                            logger.error("user_id is not defined in session state")
                    else:
                        signal_list, t_list, duration_list, resourceLists, featureLists, importanceLists, nav_reason = result
                except Exception as e:
                    logger.exception("An error occurred while processing navSignal")
                    st.session_state.messages.append({"role": "assistant", "content": handleMessage})
                    if user_id:
                        update_conversation(user_id, {"role": "assistant", "content": handleMessage, "vibration": f'vibration_{st.session_state.key_counter}', "time": current_time})

                        content_noResponse = {"role": "user", "approach": "navigation", "content": prompt, "vibration": f'vibration_{st.session_state.key_counter}', "time": current_time}
                        update_noResponse_data(user_id, content_noResponse, st.session_state.key_counter) # type: ignore
                    else:
                        logger.error("user_id is not defined in session state")

            if CH_APP_MODE == AppMode.DEBUG:
                st.session_state.messages.append({"role": "assistant", "content": "NAVIGATED RESOURCES: " + json.dumps([{"resource": resourceLists[x_r], "feature": featureLists} for x_r in range(len(resourceLists))])})

            for i in range(len(signal_list)):
                # feature_history.append({"role": "feature", "content": featureLists, "resource": resourceLists[i], "signal": signal_list[i], "t": t_list[i], "duration": duration_list[i]}) # this does not persist because of streamlit? must add to st.session_state if we need to keep this?

                feature_importance_pairs = [{"feature": feature, "importance": importance} for feature, importance in zip(featureLists, importanceLists)]
                content = {"approach": "navigation", "feature": featureLists, "feature_importance": feature_importance_pairs, "resource": resourceLists[i], "duration": duration_list[i], "time": current_time}
                update_signal_data(user_id, content, signal_list[i], t_list[i], st.session_state.key_counter)

                # Visualization
                plot = visSignal_st(np.array([signal_list[i]]), t_list[i])
                if plot:
                    caption = f"Plot{st.session_state.plot_counter}"
                    st.session_state.messages.append({"role": "assistant", "content": nav_reason})
                    st.session_state.messages.append({"role": "image", "content": plot, "resource": caption})
                    st.session_state.messages.append({"role": "feature", "featureList": featureLists, "resource": resourceLists[i], "signal": signal_list[i], "t": t_list[i], "duration": duration_list[i]})

                    if user_id:
                        update_conversation(user_id, {"role": "assistant", "content": nav_reason, "vibration": f'vibration_{st.session_state.key_counter}', "time": current_time})
                    else:
                        logger.error("user_id is not defined in session state")
        elif isinstance(msg.approach, ModifyApproach):
            if len(current_signal) > 0:
                signal, t, duration = modifySignal(msg.approach, current_signal[-1][0], current_t[-1][0])

                content = {**msg.approach.dict(), "approach": "modify", "time": current_time}
                update_signal_data(user_id, content, signal, t, st.session_state.key_counter)

                # Visualization
                plot = visSignal_st(np.array([signal]), t)
                if plot:
                    caption = f"Plot{st.session_state.plot_counter}"
                    st.session_state.messages.append({"role": "image", "content": plot, "caption": caption})
                    st.session_state.messages.append({"role": "modify", "signal": signal, "t": t, "duration": duration, "approach": msg.approach})
                else:
                    logger.warning("Failed to modify signal.")

            else:
                logger.warning("No previous signal found to modify.")
        elif msg.approach is None:
            logger.debug("Approach: NONE")
            st.session_state.messages.append({"role": "assistant", "content": handleMessage})
            if user_id:
                update_conversation(user_id, {"role": "assistant", "content": handleMessage, "vibration": f'vibration_{st.session_state.key_counter}', "time": current_time})

                content_noResponse = {"role": "user", "approach": "NONE", "content": prompt, "vibration": f'vibration_{st.session_state.key_counter}', "time": current_time}
                update_noResponse_data(user_id, content_noResponse, st.session_state.key_counter) # type: ignore
            else:
                logger.error("user_id is not defined in session state")
            # st.session_state.messages.append({"role": "assistant", "content": msg.msg}) # this is already added above
        else:
            logger.debug("Approach: ERROR")
            assert_exhaustiveness(msg.approach)


    # logger.debug("conversation_history:")
    # logger.debug(conversation_history)
    # logger.debug("parameter_history:")
    # logger.debug(parameter_history)
    # logger.debug("feature_history:")
    # logger.debug(feature_history)

    st.rerun() # update session state and rerun to keep code DRY





## Test buttons
# signal, time_value, duration = genSignal_direct(0.5, 0, 0, 0.5, 2, 1, MODE)

# button_clicked = st.button("PLAY VIBRATION")
# if button_clicked:
#     activateDAQ(signal, duration, MODE)
#     st.write("Vibration activated.")



## Test vibrations
# parameter_list = [0.5, 0, 0, 1, 0.5, 2, 5]

# signal, time_value, duration = genSignal_direct(parameter_list[0], parameter_list[1], parameter_list[2], parameter_list[3], parameter_list[4], parameter_list[5], MODE)
# visSignal(signal, time_value, MODE)
# activateDAQ(signal, duration, MODE)