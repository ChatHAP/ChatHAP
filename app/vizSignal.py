import matplotlib.pyplot as plt
import io
import sys
import logging
from .globalVariable import *

logger = logging.getLogger("ChatHAP")

def visSignal(data, t):
    if len(data) > 0 and len(t) > 0:
        line_width = 1
        plt.rc('font', size=20)
        plt.figure(figsize=(15, 10))
        plt.plot(t, data[0] / GAIN, linewidth=line_width)
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.ylim(-1.1, 1.1)
        plt.show()
    else:
        logger.warning("Data is empty. Cannot display plot.")

def visSignal_st(data, t):
    if len(data) > 0 and len(t) > 0:
        line_width = 1
        plt.rc('font', size=20)
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.plot(t, data[0] / GAIN, linewidth=line_width)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
        ax.set_ylim(-1.1, 1.1)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        return buf.getvalue()
    else:
        logger.warning("Data is empty. Cannot display plot.")
        return None