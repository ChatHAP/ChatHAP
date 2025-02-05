# type: ignore
import os
import wave
import numpy as np
import json
from scipy.signal import resample

def load_wave_files(directory):
    wave_files = {}
    for filename in os.listdir(directory):
        if filename.endswith(".wav"):
            file_path = os.path.join(directory, filename)
            try:
                with wave.open(file_path, 'rb') as wf:
                    file_name = os.path.splitext(filename)[0]
                    wave_files[file_name] = {
                        'frame_rate': wf.getframerate(),
                        'num_frames': wf.getnframes(),
                        'duration': wf.getnframes() / wf.getframerate(),
                        'data': wf.readframes(wf.getnframes())
                    }
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return wave_files

def downsample_data(data, original_frame_rate, target_frame_rate):
    ratio = target_frame_rate / original_frame_rate
    return resample(data, int(len(data) * ratio))

sample_rate = 10000 # 10kHz
directory = r"Z:\Shared Materials\Utility\VibViz\viblib\viblib"
wave_files = load_wave_files(directory)
print("Loaded wave files:")
for filename, data in wave_files.items():
    print(f"Filename: {filename}, Frame Rate: {data['frame_rate']}, Num Frames: {data['num_frames']}, Duration: {data['duration']}, Length: {len(data['data'])}")


for filename, data in wave_files.items():
    data['data'] = np.frombuffer(data['data'], dtype=np.int16).tolist()
    data['data'] = [x / 2**15 for x in data['data']]
    data['data'] = downsample_data(data['data'], data['frame_rate'], sample_rate).tolist()
    data['num_frames'] = len(data['data'])
    data['frame_rate'] = sample_rate
    data['duration'] = data['num_frames'] / data['frame_rate']

print()
print("Output wave files:")
for filename, data in wave_files.items():
    print(f"Filename: {filename}, Frame Rate: {data['frame_rate']}, Num Frames: {data['num_frames']}, Duration: {data['duration']}, Length: {len(data['data'])}")

output_file = "data\VibViz_files.json"
with open(output_file, "w") as json_file:
    json.dump(wave_files, json_file, indent=4)

print(f"Wave file information saved to {output_file}")


# Loaded wave files:
# Filename: v-09-09-8-11, Frame Rate: 44100, Num Frames: 22852, Duration: 0.5181859410430839, Length: 45704
# Filename: v-09-09-8-20, Frame Rate: 44100, Num Frames: 342016, Duration: 7.75546485260771, Length: 684032
# Filename: v-09-09-8-24, Frame Rate: 44100, Num Frames: 604160, Duration: 13.699773242630386, Length: 1208320
# Filename: v-09-10-11-55, Frame Rate: 44100, Num Frames: 260096, Duration: 5.897868480725624, Length: 520192
# Filename: v-09-10-11-58, Frame Rate: 44100, Num Frames: 414720, Duration: 9.404081632653062, Length: 829440
# Filename: v-09-10-12-11, Frame Rate: 44100, Num Frames: 285696, Duration: 6.478367346938776, Length: 571392
# Filename: v-09-10-12-13, Frame Rate: 44100, Num Frames: 175805, Duration: 3.9865079365079366, Length: 351610
# Filename: v-09-10-12-16, Frame Rate: 44100, Num Frames: 162166, Duration: 3.677233560090703, Length: 324332
# Filename: v-09-10-12-2, Frame Rate: 44100, Num Frames: 143360, Duration: 3.250793650793651, Length: 286720
# Filename: v-09-10-12-6, Frame Rate: 44100, Num Frames: 418816, Duration: 9.496961451247165, Length: 837632
# Filename: v-09-10-12-9, Frame Rate: 44100, Num Frames: 216005, Duration: 4.898072562358276, Length: 432010
# Filename: v-09-10-3-52, Frame Rate: 22050, Num Frames: 16411, Duration: 0.7442630385487529, Length: 32822
# Filename: v-09-10-3-56, Frame Rate: 44100, Num Frames: 44928, Duration: 1.0187755102040816, Length: 89856
# Filename: v-09-10-4-2, Frame Rate: 44100, Num Frames: 40689, Duration: 0.9226530612244898, Length: 81378
# Filename: v-09-10-4-20, Frame Rate: 48000, Num Frames: 184304, Duration: 3.8396666666666666, Length: 737216
# Filename: v-09-10-4-23, Frame Rate: 48000, Num Frames: 157567, Duration: 3.2826458333333335, Length: 630268
# Filename: v-09-10-4-25, Frame Rate: 48000, Num Frames: 260105, Duration: 5.418854166666667, Length: 1040420
# Filename: v-09-10-4-6, Frame Rate: 22050, Num Frames: 25920, Duration: 1.1755102040816328, Length: 51840
# Filename: v-09-10-6-16, Frame Rate: 22050, Num Frames: 32800, Duration: 1.4875283446712018, Length: 65600
# Filename: v-09-10-6-22, Frame Rate: 44100, Num Frames: 44928, Duration: 1.0187755102040816, Length: 89856
# Filename: v-09-10-6-27, Frame Rate: 44100, Num Frames: 49200, Duration: 1.1156462585034013, Length: 98400
# Filename: v-09-10-6-38, Frame Rate: 44100, Num Frames: 44100, Duration: 1.0, Length: 88200
# Filename: v-09-10-6-43, Frame Rate: 44100, Num Frames: 48022, Duration: 1.0889342403628117, Length: 192088
# Filename: v-09-10-6-46, Frame Rate: 8000, Num Frames: 9167, Duration: 1.145875, Length: 18334
# Filename: v-09-10-6-5, Frame Rate: 22050, Num Frames: 43899, Duration: 1.9908843537414966, Length: 87798
# Filename: v-09-10-6-59, Frame Rate: 44100, Num Frames: 51275, Duration: 1.1626984126984128, Length: 205100
# Filename: v-09-10-7-34, Frame Rate: 48000, Num Frames: 49536, Duration: 1.032, Length: 198144
# Filename: v-09-10-7-36, Frame Rate: 44100, Num Frames: 28149, Duration: 0.6382993197278911, Length: 56298
# Filename: v-09-10-7-9, Frame Rate: 48000, Num Frames: 49536, Duration: 1.032, Length: 198144
# Filename: v-09-10-8-5, Frame Rate: 44100, Num Frames: 55296, Duration: 1.253877551020408, Length: 110592
# Filename: v-09-10-8-7, Frame Rate: 44100, Num Frames: 37746, Duration: 0.8559183673469388, Length: 75492
# Filename: v-09-11-3-12, Frame Rate: 44100, Num Frames: 88200, Duration: 2.0, Length: 176400
# Filename: v-09-11-3-16, Frame Rate: 44100, Num Frames: 88200, Duration: 2.0, Length: 176400
# Filename: v-09-11-3-19, Frame Rate: 44100, Num Frames: 88204, Duration: 2.000090702947846, Length: 176408
# Filename: v-09-11-3-21, Frame Rate: 44100, Num Frames: 88204, Duration: 2.000090702947846, Length: 176408
# Filename: v-09-11-3-24, Frame Rate: 44100, Num Frames: 88200, Duration: 2.0, Length: 176400
# Filename: v-09-11-3-4, Frame Rate: 44100, Num Frames: 66150, Duration: 1.5, Length: 132300
# Filename: v-09-11-3-43, Frame Rate: 44100, Num Frames: 88200, Duration: 2.0, Length: 176400
# Filename: v-09-11-3-50, Frame Rate: 44100, Num Frames: 88200, Duration: 2.0, Length: 176400
# Filename: v-09-11-3-54, Frame Rate: 44100, Num Frames: 88204, Duration: 2.000090702947846, Length: 176408
# Filename: v-09-11-3-56, Frame Rate: 44100, Num Frames: 88112, Duration: 1.9980045351473923, Length: 176224
# Filename: v-09-11-3-8, Frame Rate: 44100, Num Frames: 46988, Duration: 1.0654875283446712, Length: 93976
# Filename: v-09-11-4-1, Frame Rate: 44100, Num Frames: 88200, Duration: 2.0, Length: 176400
# Filename: v-09-11-4-12, Frame Rate: 44100, Num Frames: 44100, Duration: 1.0, Length: 88200
# Filename: v-09-11-4-22, Frame Rate: 44100, Num Frames: 44100, Duration: 1.0, Length: 88200
# Filename: v-09-11-4-3, Frame Rate: 44100, Num Frames: 88204, Duration: 2.000090702947846, Length: 176408
# Filename: v-09-11-4-41, Frame Rate: 22050, Num Frames: 119488, Duration: 5.4189569160997735, Length: 477952
# Filename: v-09-11-4-54, Frame Rate: 44100, Num Frames: 54144, Duration: 1.2277551020408164, Length: 108288
# Filename: v-09-11-4-8, Frame Rate: 44100, Num Frames: 88200, Duration: 2.0, Length: 176400
# Filename: v-09-12-1-0, Frame Rate: 22050, Num Frames: 23616, Duration: 1.0710204081632653, Length: 47232
# Filename: v-09-12-1-19, Frame Rate: 48000, Num Frames: 40525, Duration: 0.8442708333333333, Length: 162100
# Filename: v-09-12-1-21, Frame Rate: 48000, Num Frames: 38346, Duration: 0.798875, Length: 153384
# Filename: v-09-12-1-23, Frame Rate: 44100, Num Frames: 21737, Duration: 0.49290249433106575, Length: 43474
# Filename: v-09-12-1-29, Frame Rate: 44100, Num Frames: 19354, Duration: 0.4388662131519274, Length: 38708
# Filename: v-09-12-1-39, Frame Rate: 44100, Num Frames: 89856, Duration: 2.0375510204081633, Length: 179712
# Filename: v-09-12-1-48, Frame Rate: 44100, Num Frames: 55296, Duration: 1.253877551020408, Length: 110592
# Filename: v-09-12-1-53, Frame Rate: 44100, Num Frames: 54144, Duration: 1.2277551020408164, Length: 108288
# Filename: v-09-12-2-17, Frame Rate: 44100, Num Frames: 46080, Duration: 1.0448979591836736, Length: 92160
# Filename: v-09-12-2-20, Frame Rate: 44100, Num Frames: 46080, Duration: 1.0448979591836736, Length: 92160
# Filename: v-09-12-2-23, Frame Rate: 44100, Num Frames: 89856, Duration: 2.0375510204081633, Length: 179712
# Filename: v-09-12-2-40, Frame Rate: 44100, Num Frames: 166912, Duration: 3.7848526077097504, Length: 333824
# Filename: v-09-12-8-10, Frame Rate: 44100, Num Frames: 228693, Duration: 5.18578231292517, Length: 457386
# Filename: v-09-12-8-13, Frame Rate: 44100, Num Frames: 92375, Duration: 2.0946712018140587, Length: 184750
# Filename: v-09-12-8-21, Frame Rate: 44100, Num Frames: 5031, Duration: 0.11408163265306122, Length: 10062
# Filename: v-09-12-8-27, Frame Rate: 44100, Num Frames: 8820, Duration: 0.2, Length: 17640
# Filename: v-09-12-8-30, Frame Rate: 22050, Num Frames: 3329, Duration: 0.1509750566893424, Length: 6658
# Filename: v-09-12-8-32, Frame Rate: 44100, Num Frames: 33075, Duration: 0.75, Length: 66150
# Filename: v-09-16-1-43, Frame Rate: 48000, Num Frames: 18909, Duration: 0.3939375, Length: 75636
# Filename: v-09-16-1-56, Frame Rate: 44100, Num Frames: 62926, Duration: 1.4268934240362812, Length: 125852
# Filename: v-09-18-1-55, Frame Rate: 44100, Num Frames: 139221, Duration: 3.1569387755102043, Length: 278442
# Filename: v-09-18-2-7, Frame Rate: 44100, Num Frames: 55597, Duration: 1.260702947845805, Length: 111194
# Filename: v-09-18-4-12, Frame Rate: 44100, Num Frames: 116722, Duration: 2.6467573696145124, Length: 233444
# Filename: v-09-18-4-15, Frame Rate: 44100, Num Frames: 32256, Duration: 0.7314285714285714, Length: 64512
# Filename: v-09-18-4-16, Frame Rate: 44100, Num Frames: 11264, Duration: 0.25541950113378686, Length: 22528
# Filename: v-09-18-4-18, Frame Rate: 44100, Num Frames: 104960, Duration: 2.380045351473923, Length: 209920
# Filename: v-09-18-4-22, Frame Rate: 44100, Num Frames: 642519, Duration: 14.569591836734693, Length: 1285038
# Filename: v-09-18-4-56, Frame Rate: 44100, Num Frames: 271104, Duration: 6.147482993197279, Length: 542208
# Filename: v-09-23-6-24, Frame Rate: 44100, Num Frames: 89153, Duration: 2.021609977324263, Length: 178306
# Filename: v-09-26-1-39, Frame Rate: 44100, Num Frames: 148810, Duration: 3.37437641723356, Length: 297620
# Filename: v-10-09-1-1, Frame Rate: 44100, Num Frames: 49446, Duration: 1.1212244897959183, Length: 98892
# Filename: v-10-09-1-11, Frame Rate: 44100, Num Frames: 85940, Duration: 1.94875283446712, Length: 171880
# Filename: v-10-09-1-12, Frame Rate: 44100, Num Frames: 63745, Duration: 1.4454648526077098, Length: 127490
# Filename: v-10-09-1-14, Frame Rate: 44100, Num Frames: 150008, Duration: 3.4015419501133786, Length: 300016
# Filename: v-10-09-1-16, Frame Rate: 44100, Num Frames: 147692, Duration: 3.3490249433106576, Length: 295384
# Filename: v-10-09-1-20, Frame Rate: 44100, Num Frames: 265347, Duration: 6.016938775510204, Length: 530694
# Filename: v-10-09-1-8, Frame Rate: 44100, Num Frames: 188234, Duration: 4.268344671201814, Length: 376468
# Filename: v-10-09-5-0, Frame Rate: 22050, Num Frames: 23040, Duration: 1.0448979591836736, Length: 46080
# Filename: v-10-09-5-2, Frame Rate: 22050, Num Frames: 23040, Duration: 1.0448979591836736, Length: 46080
# Filename: v-10-09-5-4, Frame Rate: 22050, Num Frames: 23040, Duration: 1.0448979591836736, Length: 46080
# Filename: v-10-09-5-7, Frame Rate: 44100, Num Frames: 46080, Duration: 1.0448979591836736, Length: 92160
# Filename: v-10-10-1-10, Frame Rate: 44100, Num Frames: 176448, Duration: 4.001088435374149, Length: 352896
# Filename: v-10-10-1-18, Frame Rate: 44100, Num Frames: 63236, Duration: 1.433922902494331, Length: 126472
# Filename: v-10-10-1-21, Frame Rate: 44100, Num Frames: 46138, Duration: 1.0462131519274376, Length: 92276
# Filename: v-10-10-1-5, Frame Rate: 44100, Num Frames: 121218, Duration: 2.7487074829931974, Length: 242436
# Filename: v-10-18-11-11, Frame Rate: 44100, Num Frames: 46138, Duration: 1.0462131519274376, Length: 92276
# Filename: v-10-21-2-48, Frame Rate: 44100, Num Frames: 54822, Duration: 1.2431292517006802, Length: 109644
# Filename: v-10-21-3-11, Frame Rate: 44100, Num Frames: 27648, Duration: 0.626938775510204, Length: 55296
# Filename: v-10-21-3-17, Frame Rate: 44100, Num Frames: 46080, Duration: 1.0448979591836736, Length: 92160
# Filename: v-10-21-3-2, Frame Rate: 44100, Num Frames: 21457, Duration: 0.48655328798185943, Length: 42914
# Filename: v-10-21-3-21, Frame Rate: 44100, Num Frames: 23542, Duration: 0.5338321995464853, Length: 47084
# Filename: v-10-21-3-30, Frame Rate: 44100, Num Frames: 21888, Duration: 0.4963265306122449, Length: 43776
# Filename: v-10-21-3-33, Frame Rate: 44100, Num Frames: 8064, Duration: 0.18285714285714286, Length: 16128
# Filename: v-10-21-3-39, Frame Rate: 44100, Num Frames: 11520, Duration: 0.2612244897959184, Length: 23040
# Filename: v-10-21-3-4, Frame Rate: 44100, Num Frames: 23158, Duration: 0.525124716553288, Length: 46316
# Filename: v-10-21-3-45, Frame Rate: 44100, Num Frames: 69842, Duration: 1.583718820861678, Length: 139684
# Filename: v-10-21-3-7, Frame Rate: 44100, Num Frames: 23040, Duration: 0.5224489795918368, Length: 46080
# Filename: v-10-23-1-10, Frame Rate: 44100, Num Frames: 104719, Duration: 2.374580498866213, Length: 209438
# Filename: v-10-23-1-16, Frame Rate: 44100, Num Frames: 45306, Duration: 1.0273469387755103, Length: 90612
# Filename: v-10-23-1-21, Frame Rate: 44100, Num Frames: 54822, Duration: 1.2431292517006802, Length: 109644
# Filename: v-10-23-1-23, Frame Rate: 44100, Num Frames: 54822, Duration: 1.2431292517006802, Length: 109644
# Filename: v-10-23-1-24, Frame Rate: 44100, Num Frames: 54822, Duration: 1.2431292517006802, Length: 109644
# Filename: v-10-28-7-22, Frame Rate: 44100, Num Frames: 144805, Duration: 3.283560090702948, Length: 289610
# Filename: v-10-28-7-23, Frame Rate: 44100, Num Frames: 136805, Duration: 3.102154195011338, Length: 273610
# Filename: v-10-28-7-26, Frame Rate: 44100, Num Frames: 202090, Duration: 4.582539682539682, Length: 404180
# Filename: v-10-28-7-29, Frame Rate: 44100, Num Frames: 175429, Duration: 3.977981859410431, Length: 350858
# Filename: v-10-28-7-31, Frame Rate: 44100, Num Frames: 237338, Duration: 5.381814058956916, Length: 474676
# Filename: v-10-28-7-33, Frame Rate: 44100, Num Frames: 113425, Duration: 2.5719954648526078, Length: 226850
# Filename: v-10-28-7-35, Frame Rate: 44100, Num Frames: 103473, Duration: 2.3463265306122447, Length: 206946
# Filename: v-10-28-7-36, Frame Rate: 44100, Num Frames: 105028, Duration: 2.3815873015873015, Length: 210056
# Filename: v-10-29-4-20, Frame Rate: 44100, Num Frames: 695186, Duration: 15.763854875283446, Length: 1390372
# Filename: v-10-29-4-22, Frame Rate: 44100, Num Frames: 91685, Duration: 2.0790249433106576, Length: 183370

# Output wave files:
# Filename: v-09-09-8-11, Frame Rate: 10000, Num Frames: 5181, Duration: 0.5181, Length: 5181
# Filename: v-09-09-8-20, Frame Rate: 10000, Num Frames: 77554, Duration: 7.7554, Length: 77554
# Filename: v-09-09-8-24, Frame Rate: 10000, Num Frames: 136997, Duration: 13.6997, Length: 136997
# Filename: v-09-10-11-55, Frame Rate: 10000, Num Frames: 58978, Duration: 5.8978, Length: 58978
# Filename: v-09-10-11-58, Frame Rate: 10000, Num Frames: 94040, Duration: 9.404, Length: 94040
# Filename: v-09-10-12-11, Frame Rate: 10000, Num Frames: 64783, Duration: 6.4783, Length: 64783
# Filename: v-09-10-12-13, Frame Rate: 10000, Num Frames: 39865, Duration: 3.9865, Length: 39865
# Filename: v-09-10-12-16, Frame Rate: 10000, Num Frames: 36772, Duration: 3.6772, Length: 36772
# Filename: v-09-10-12-2, Frame Rate: 10000, Num Frames: 32507, Duration: 3.2507, Length: 32507
# Filename: v-09-10-12-6, Frame Rate: 10000, Num Frames: 94969, Duration: 9.4969, Length: 94969
# Filename: v-09-10-12-9, Frame Rate: 10000, Num Frames: 48980, Duration: 4.898, Length: 48980
# Filename: v-09-10-3-52, Frame Rate: 10000, Num Frames: 7442, Duration: 0.7442, Length: 7442
# Filename: v-09-10-3-56, Frame Rate: 10000, Num Frames: 10187, Duration: 1.0187, Length: 10187
# Filename: v-09-10-4-2, Frame Rate: 10000, Num Frames: 9226, Duration: 0.9226, Length: 9226
# Filename: v-09-10-4-20, Frame Rate: 10000, Num Frames: 76793, Duration: 7.6793, Length: 76793
# Filename: v-09-10-4-23, Frame Rate: 10000, Num Frames: 65652, Duration: 6.5652, Length: 65652
# Filename: v-09-10-4-25, Frame Rate: 10000, Num Frames: 108377, Duration: 10.8377, Length: 108377
# Filename: v-09-10-4-6, Frame Rate: 10000, Num Frames: 11755, Duration: 1.1755, Length: 11755
# Filename: v-09-10-6-16, Frame Rate: 10000, Num Frames: 14875, Duration: 1.4875, Length: 14875
# Filename: v-09-10-6-22, Frame Rate: 10000, Num Frames: 10187, Duration: 1.0187, Length: 10187
# Filename: v-09-10-6-27, Frame Rate: 10000, Num Frames: 11156, Duration: 1.1156, Length: 11156
# Filename: v-09-10-6-38, Frame Rate: 10000, Num Frames: 10000, Duration: 1.0, Length: 10000
# Filename: v-09-10-6-43, Frame Rate: 10000, Num Frames: 21778, Duration: 2.1778, Length: 21778
# Filename: v-09-10-6-46, Frame Rate: 10000, Num Frames: 11458, Duration: 1.1458, Length: 11458
# Filename: v-09-10-6-5, Frame Rate: 10000, Num Frames: 19908, Duration: 1.9908, Length: 19908
# Filename: v-09-10-6-59, Frame Rate: 10000, Num Frames: 23253, Duration: 2.3253, Length: 23253
# Filename: v-09-10-7-34, Frame Rate: 10000, Num Frames: 20640, Duration: 2.064, Length: 20640
# Filename: v-09-10-7-36, Frame Rate: 10000, Num Frames: 6382, Duration: 0.6382, Length: 6382
# Filename: v-09-10-7-9, Frame Rate: 10000, Num Frames: 20640, Duration: 2.064, Length: 20640
# Filename: v-09-10-8-5, Frame Rate: 10000, Num Frames: 12538, Duration: 1.2538, Length: 12538
# Filename: v-09-10-8-7, Frame Rate: 10000, Num Frames: 8559, Duration: 0.8559, Length: 8559
# Filename: v-09-11-3-12, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-11-3-16, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-11-3-19, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-11-3-21, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-11-3-24, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-11-3-4, Frame Rate: 10000, Num Frames: 15000, Duration: 1.5, Length: 15000
# Filename: v-09-11-3-43, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-11-3-50, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-11-3-54, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-11-3-56, Frame Rate: 10000, Num Frames: 19980, Duration: 1.998, Length: 19980
# Filename: v-09-11-3-8, Frame Rate: 10000, Num Frames: 10654, Duration: 1.0654, Length: 10654
# Filename: v-09-11-4-1, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-11-4-12, Frame Rate: 10000, Num Frames: 10000, Duration: 1.0, Length: 10000
# Filename: v-09-11-4-22, Frame Rate: 10000, Num Frames: 10000, Duration: 1.0, Length: 10000
# Filename: v-09-11-4-3, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-11-4-41, Frame Rate: 10000, Num Frames: 108379, Duration: 10.8379, Length: 108379
# Filename: v-09-11-4-54, Frame Rate: 10000, Num Frames: 12277, Duration: 1.2277, Length: 12277
# Filename: v-09-11-4-8, Frame Rate: 10000, Num Frames: 20000, Duration: 2.0, Length: 20000
# Filename: v-09-12-1-0, Frame Rate: 10000, Num Frames: 10710, Duration: 1.071, Length: 10710
# Filename: v-09-12-1-19, Frame Rate: 10000, Num Frames: 16885, Duration: 1.6885, Length: 16885
# Filename: v-09-12-1-21, Frame Rate: 10000, Num Frames: 15977, Duration: 1.5977, Length: 15977
# Filename: v-09-12-1-23, Frame Rate: 10000, Num Frames: 4929, Duration: 0.4929, Length: 4929
# Filename: v-09-12-1-29, Frame Rate: 10000, Num Frames: 4388, Duration: 0.4388, Length: 4388
# Filename: v-09-12-1-39, Frame Rate: 10000, Num Frames: 20375, Duration: 2.0375, Length: 20375
# Filename: v-09-12-1-48, Frame Rate: 10000, Num Frames: 12538, Duration: 1.2538, Length: 12538
# Filename: v-09-12-1-53, Frame Rate: 10000, Num Frames: 12277, Duration: 1.2277, Length: 12277
# Filename: v-09-12-2-17, Frame Rate: 10000, Num Frames: 10448, Duration: 1.0448, Length: 10448
# Filename: v-09-12-2-20, Frame Rate: 10000, Num Frames: 10448, Duration: 1.0448, Length: 10448
# Filename: v-09-12-2-23, Frame Rate: 10000, Num Frames: 20375, Duration: 2.0375, Length: 20375
# Filename: v-09-12-2-40, Frame Rate: 10000, Num Frames: 37848, Duration: 3.7848, Length: 37848
# Filename: v-09-12-8-10, Frame Rate: 10000, Num Frames: 51857, Duration: 5.1857, Length: 51857
# Filename: v-09-12-8-13, Frame Rate: 10000, Num Frames: 20946, Duration: 2.0946, Length: 20946
# Filename: v-09-12-8-21, Frame Rate: 10000, Num Frames: 1140, Duration: 0.114, Length: 1140
# Filename: v-09-12-8-27, Frame Rate: 10000, Num Frames: 2000, Duration: 0.2, Length: 2000
# Filename: v-09-12-8-30, Frame Rate: 10000, Num Frames: 1509, Duration: 0.1509, Length: 1509
# Filename: v-09-12-8-32, Frame Rate: 10000, Num Frames: 7500, Duration: 0.75, Length: 7500
# Filename: v-09-16-1-43, Frame Rate: 10000, Num Frames: 7878, Duration: 0.7878, Length: 7878
# Filename: v-09-16-1-56, Frame Rate: 10000, Num Frames: 14268, Duration: 1.4268, Length: 14268
# Filename: v-09-18-1-55, Frame Rate: 10000, Num Frames: 31569, Duration: 3.1569, Length: 31569
# Filename: v-09-18-2-7, Frame Rate: 10000, Num Frames: 12607, Duration: 1.2607, Length: 12607
# Filename: v-09-18-4-12, Frame Rate: 10000, Num Frames: 26467, Duration: 2.6467, Length: 26467
# Filename: v-09-18-4-15, Frame Rate: 10000, Num Frames: 7314, Duration: 0.7314, Length: 7314
# Filename: v-09-18-4-16, Frame Rate: 10000, Num Frames: 2554, Duration: 0.2554, Length: 2554
# Filename: v-09-18-4-18, Frame Rate: 10000, Num Frames: 23800, Duration: 2.38, Length: 23800
# Filename: v-09-18-4-22, Frame Rate: 10000, Num Frames: 145695, Duration: 14.5695, Length: 145695
# Filename: v-09-18-4-56, Frame Rate: 10000, Num Frames: 61474, Duration: 6.1474, Length: 61474
# Filename: v-09-23-6-24, Frame Rate: 10000, Num Frames: 20216, Duration: 2.0216, Length: 20216
# Filename: v-09-26-1-39, Frame Rate: 10000, Num Frames: 33743, Duration: 3.3743, Length: 33743
# Filename: v-10-09-1-1, Frame Rate: 10000, Num Frames: 11212, Duration: 1.1212, Length: 11212
# Filename: v-10-09-1-11, Frame Rate: 10000, Num Frames: 19487, Duration: 1.9487, Length: 19487
# Filename: v-10-09-1-12, Frame Rate: 10000, Num Frames: 14454, Duration: 1.4454, Length: 14454
# Filename: v-10-09-1-14, Frame Rate: 10000, Num Frames: 34015, Duration: 3.4015, Length: 34015
# Filename: v-10-09-1-16, Frame Rate: 10000, Num Frames: 33490, Duration: 3.349, Length: 33490
# Filename: v-10-09-1-20, Frame Rate: 10000, Num Frames: 60169, Duration: 6.0169, Length: 60169
# Filename: v-10-09-1-8, Frame Rate: 10000, Num Frames: 42683, Duration: 4.2683, Length: 42683
# Filename: v-10-09-5-0, Frame Rate: 10000, Num Frames: 10448, Duration: 1.0448, Length: 10448
# Filename: v-10-09-5-2, Frame Rate: 10000, Num Frames: 10448, Duration: 1.0448, Length: 10448
# Filename: v-10-09-5-4, Frame Rate: 10000, Num Frames: 10448, Duration: 1.0448, Length: 10448
# Filename: v-10-09-5-7, Frame Rate: 10000, Num Frames: 10448, Duration: 1.0448, Length: 10448
# Filename: v-10-10-1-10, Frame Rate: 10000, Num Frames: 40010, Duration: 4.001, Length: 40010
# Filename: v-10-10-1-18, Frame Rate: 10000, Num Frames: 14339, Duration: 1.4339, Length: 14339
# Filename: v-10-10-1-21, Frame Rate: 10000, Num Frames: 10462, Duration: 1.0462, Length: 10462
# Filename: v-10-10-1-5, Frame Rate: 10000, Num Frames: 27487, Duration: 2.7487, Length: 27487
# Filename: v-10-18-11-11, Frame Rate: 10000, Num Frames: 10462, Duration: 1.0462, Length: 10462
# Filename: v-10-21-2-48, Frame Rate: 10000, Num Frames: 12431, Duration: 1.2431, Length: 12431
# Filename: v-10-21-3-11, Frame Rate: 10000, Num Frames: 6269, Duration: 0.6269, Length: 6269
# Filename: v-10-21-3-17, Frame Rate: 10000, Num Frames: 10448, Duration: 1.0448, Length: 10448
# Filename: v-10-21-3-2, Frame Rate: 10000, Num Frames: 4865, Duration: 0.4865, Length: 4865
# Filename: v-10-21-3-21, Frame Rate: 10000, Num Frames: 5338, Duration: 0.5338, Length: 5338
# Filename: v-10-21-3-30, Frame Rate: 10000, Num Frames: 4963, Duration: 0.4963, Length: 4963
# Filename: v-10-21-3-33, Frame Rate: 10000, Num Frames: 1828, Duration: 0.1828, Length: 1828
# Filename: v-10-21-3-39, Frame Rate: 10000, Num Frames: 2612, Duration: 0.2612, Length: 2612
# Filename: v-10-21-3-4, Frame Rate: 10000, Num Frames: 5251, Duration: 0.5251, Length: 5251
# Filename: v-10-21-3-45, Frame Rate: 10000, Num Frames: 15837, Duration: 1.5837, Length: 15837
# Filename: v-10-21-3-7, Frame Rate: 10000, Num Frames: 5224, Duration: 0.5224, Length: 5224
# Filename: v-10-23-1-10, Frame Rate: 10000, Num Frames: 23745, Duration: 2.3745, Length: 23745
# Filename: v-10-23-1-16, Frame Rate: 10000, Num Frames: 10273, Duration: 1.0273, Length: 10273
# Filename: v-10-23-1-21, Frame Rate: 10000, Num Frames: 12431, Duration: 1.2431, Length: 12431
# Filename: v-10-23-1-23, Frame Rate: 10000, Num Frames: 12431, Duration: 1.2431, Length: 12431
# Filename: v-10-23-1-24, Frame Rate: 10000, Num Frames: 12431, Duration: 1.2431, Length: 12431
# Filename: v-10-28-7-22, Frame Rate: 10000, Num Frames: 32835, Duration: 3.2835, Length: 32835
# Filename: v-10-28-7-23, Frame Rate: 10000, Num Frames: 31021, Duration: 3.1021, Length: 31021
# Filename: v-10-28-7-26, Frame Rate: 10000, Num Frames: 45825, Duration: 4.5825, Length: 45825
# Filename: v-10-28-7-29, Frame Rate: 10000, Num Frames: 39779, Duration: 3.9779, Length: 39779
# Filename: v-10-28-7-31, Frame Rate: 10000, Num Frames: 53818, Duration: 5.3818, Length: 53818
# Filename: v-10-28-7-33, Frame Rate: 10000, Num Frames: 25719, Duration: 2.5719, Length: 25719
# Filename: v-10-28-7-35, Frame Rate: 10000, Num Frames: 23463, Duration: 2.3463, Length: 23463
# Filename: v-10-28-7-36, Frame Rate: 10000, Num Frames: 23815, Duration: 2.3815, Length: 23815
# Filename: v-10-29-4-20, Frame Rate: 10000, Num Frames: 157638, Duration: 15.7638, Length: 157638
# Filename: v-10-29-4-22, Frame Rate: 10000, Num Frames: 20790, Duration: 2.079, Length: 20790
# Wave file information saved to VibViz_files.json
