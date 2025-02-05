from enum import Enum
import numpy as np
import logging
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

from .globalVariable import *


logger = logging.getLogger("ChatHAP")


class AmplitudeEnvelopeType(Enum):
    """Options for the whole amplitude envelope."""
    CONTINUOUS = "CONTINUOUS"
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    INCREASE_DECREASE = "INCREASE_DECREASE"

class GenSignalInput(BaseModel):
    """Input data for generating vibration signal."""
    A: float = Field(0.5, title="Amplitude", description="Amplitude of the signal", ge=0, le=1)
    A_W_option: AmplitudeEnvelopeType = Field(AmplitudeEnvelopeType.CONTINUOUS, title="Whole Amplitude Envelope", description="Option for the overall amplitude envelope")
    A_E_option: AmplitudeEnvelopeType = Field(AmplitudeEnvelopeType.CONTINUOUS, title="Each Amplitude Envelope", description="Option for each amplitude envelope")
    freq_c: float = Field(200, title="Carrier Frequency", description="Carrier Frequency of the signal, ranging from 50Hz to 500Hz, default 200Hz", ge=MIN_FREQ_C, le=MAX_FREQ_C)
    freq_e: float = Field(0, title="Envelope Frequency", description="Envelope Frequency of the signal, ranging from 0Hz to Carrier Frequency", ge=0)
    dur: float = Field(2, title="Duration", description="Duration of the signal", ge=0, le=MAX_DURATION)
    rhythm: int = Field(1, title="Rhythm", description="Rhythm of the signal (number of pulses)", ge=1, le=MAX_RHYTHM)



# @tool("genSignal", args_schema=GenSignalInput, return_direct=True)
def genSignal_direct(
        gsi: GenSignalInput
        # A: float = 0.5,
        # A_W_option: AmplitudeEnvelopeType = AmplitudeEnvelopeType.CONTINUOUS,
        # A_E_option: AmplitudeEnvelopeType = AmplitudeEnvelopeType.CONTINUOUS,
        # freq = 0.5,
        # dur = 2,
        # rhythm = 1
    ):
    """Generate a vibration signal with the given parameters."""
    A = gsi.A
    A_W_option = gsi.A_W_option
    A_E_option = gsi.A_E_option
    freq_c = gsi.freq_c
    freq_e = gsi.freq_e
    dur = gsi.dur
    rhythm = gsi.rhythm
    if A != None and A_W_option != None and A_E_option != None and freq_c != None and freq_e != None and dur != None and rhythm != None:
        rhythm = int(rhythm)
        A_env = 1
        entire_length = int(dur*SAMPLE_RATE)
        t = np.linspace(0, dur, entire_length, endpoint=False)
        R_env = np.array([])
        pulse_length = 0

        # Entire Envelope
        match A_W_option:
            case AmplitudeEnvelopeType.CONTINUOUS:
                A_env = 1
            case AmplitudeEnvelopeType.INCREASE:
                A_env = t / dur
            case AmplitudeEnvelopeType.DECREASE:
                A_env = 1 - (t / dur)
            case AmplitudeEnvelopeType.INCREASE_DECREASE:
                A_env = np.concatenate((t[:int(entire_length/2)] / (dur / 2), 1 - t[:int(entire_length/2)] / (dur / 2)))
                if len(A_env) != entire_length:
                    A_env = np.concatenate((A_env, np.zeros(entire_length - len(A_env))))
            case _:
                A_env = 1
                # raise ValueError(f"Unhandled AmplitudeEnvelopeType: {A_W_option}")

        # Entire Frequency (Carrier Frequency)
        if freq_c < MIN_FREQ_C or freq_c > MAX_FREQ_C:
            logger.warning("frequency parameter out of range")
            freq_c = min(MAX_FREQ_C, max(MIN_FREQ_C, freq_c))

        # The number of pulses
        if rhythm == 1:
            pulse_list = np.ones(entire_length)
            R_env = np.concatenate((R_env, pulse_list))
        elif rhythm != 1:
            pulse_length = int(entire_length/(rhythm*2))
            rest_length = int(entire_length/(rhythm*2))

            # Each Envelope
            match A_E_option:
                case AmplitudeEnvelopeType.CONTINUOUS:
                    A_E_env = np.ones(pulse_length)
                case AmplitudeEnvelopeType.INCREASE:
                    A_E_env = np.arange(0, 1, 1/pulse_length)
                    if len(A_E_env) != pulse_length:
                        A_E_env = np.concatenate((A_E_env, np.ones(pulse_length - len(A_E_env))))
                case AmplitudeEnvelopeType.DECREASE:
                    A_E_env = np.arange(1, 0, -1/pulse_length)
                    if len(A_E_env) <= pulse_length:
                        A_E_env = np.concatenate((A_E_env, np.zeros(pulse_length - len(A_E_env))))
                    else:
                        A_E_env = A_E_env[:pulse_length]
                case AmplitudeEnvelopeType.INCREASE_DECREASE:
                    increasing_seq = np.arange(0, 1, 1/(pulse_length/2))
                    decreasing_seq = np.arange(1, 0, -1/(pulse_length/2))
                    A_E_env = np.concatenate((increasing_seq, decreasing_seq))
                    if len(A_E_env) <= pulse_length:
                        A_E_env = np.concatenate((A_E_env, np.zeros(pulse_length - len(A_E_env))))
                    else:
                        A_E_env = A_E_env[:pulse_length]
                case _:
                    A_E_env = np.ones(pulse_length)

            pulse_list = A_E_env
            rest_list = np.zeros(rest_length)

            for i in range(rhythm):
                R_env = np.concatenate((R_env, pulse_list, rest_list))

            if len(R_env) != entire_length:
                R_env = np.concatenate((R_env, np.zeros(entire_length-len(R_env))))

        if freq_e == 0:
            Signal = GAIN * A * A_env * R_env * np.sin(2* np.pi * freq_c * t)
        else:
            freq_e = min(freq_c, max(0, freq_e))
            Signal = GAIN * A * A_env * R_env * np.sin(2* np.pi * freq_c * t) * np.sin(2* np.pi * freq_e * t) 

        data = []
        data.append(Signal)
        data = np.array(data)

        return data, t, dur

    else:
        logger.warning("No list. Cannot create vibration.")
        return np.array([[]]), np.array([]), 0