import json
import logging
import random
import math

import numpy as np
import numpy.typing as npt
from scipy.signal import resample

from .langinterface import NavigationApproach, ModifyApproach, nav_chatgpt, BaseMessage
from .genSignal import GAIN, GenSignalInput
from .firebase_users import *
from .globalVariable import *

logger = logging.getLogger("ChatHAP")

with open("./data/VibViz_tags.json", "r") as json_file:
    tag_examples = json.load(json_file)
tag_examples = json.dumps(tag_examples)

with open("./data/VibLib-VibViz-processed.json", "r") as json_file:
    tag_files = json.load(json_file)
    random.shuffle(tag_files)

with open("./data/VibViz_files.json", "r") as json_file:
    signal_files = json.load(json_file)

def navSignal(nav_approach: NavigationApproach) -> tuple[list[npt.NDArray[np.float64]], list[npt.NDArray[np.float64]], list[float], list[str], list[str], list[float], str]:
    random.shuffle(tag_files)
    tag_lists = tag_files
    response = nav_chatgpt(nav_approach.natural_language_search_query, tag_lists)

    logging.debug(f"Response: {response}")

    if not response.resources or not response.features:
        logger.error("No resources or features available in the response.")
        return None # type: ignore

    resourceLists = [r.resource for r in response.resources]
    reasonLists = [r.reason for r in response.resources]
    featureLists = [f.feature for f in response.features]
    importanceLists = [f.importance for f in response.features]

    # Select a single navigation
    selected_resource = read_nav_rating(resourceLists, featureLists, importanceLists, UserPreference, CLIP, MIN_CLIP)

    if not selected_resource:
        logger.error("No resources or probabilities available for selection.")
        return None # type: ignore

    resource_index = resourceLists.index(selected_resource) # type: ignore
    logger.debug(f"resource_index: {resource_index}")
    corresponding_reason = reasonLists[resource_index]

    signal_list = 0.5 * GAIN * np.array(signal_files[selected_resource]["data"])
    t_list = np.linspace(0, signal_files[selected_resource]["duration"], int(signal_files[selected_resource]["num_frames"]), endpoint=False)
    duration_list = signal_files[selected_resource]["duration"]

    logging.debug(f"Signal length: {len(signal_list)}, t length: {len(t_list)}, duration: {duration_list}")

    return [signal_list], [t_list], [duration_list], resourceLists, featureLists, importanceLists, corresponding_reason

def modifySignal(msg_modify: ModifyApproach, signal: npt.NDArray[np.float64], t: npt.NDArray[np.float64]) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], float]:
    logger.debug(f"msg_modify: {msg_modify}")

    new_signal: np.ndarray = np.array([])
    new_t: np.ndarray = np.array([])

    new_signal = signal
    new_t = t

    if msg_modify.change_amplitude_factor:
        new_signal = np.array(new_signal) * msg_modify.change_amplitude_factor
    if msg_modify.time_stretch_factor:
        new_length = int(len(new_signal) * msg_modify.time_stretch_factor)
        new_duration = new_t[-1] * msg_modify.time_stretch_factor
        new_signal = resample(new_signal, new_length) # type: ignore
        new_t = np.linspace(0, new_duration, new_length, endpoint=False)
    if msg_modify.truncate_or_extend_signal_factor:
        if msg_modify.truncate_or_extend_signal_factor > 1.0: # Extend by looping
            new_length = int(len(new_t) * msg_modify.truncate_or_extend_signal_factor)
            new_signal = np.tile(new_signal, int(math.ceil(msg_modify.truncate_or_extend_signal_factor)))[0:new_length]
            new_duration = new_t[-1] * msg_modify.truncate_or_extend_signal_factor
            new_t = np.linspace(0, new_duration, new_length, endpoint=False) # type: ignore
        else: # Truncate
            new_length = int(len(new_t) * msg_modify.truncate_or_extend_signal_factor)
            new_signal = new_signal[:new_length]
            new_t = new_t[:new_length]
    if msg_modify.reverse_signal:
        new_signal = np.flip(new_signal)

    if np.abs(np.max(new_signal)) > GAIN:
        new_signal = new_signal * GAIN / np.abs(np.max(new_signal))

    return new_signal, new_t, new_t[-1]