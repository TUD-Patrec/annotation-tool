import logging
import os
from os.path import join

import numpy as np
from scipy import spatial

NORM_MAX_THRESHOLDS = [
    392.85,
    345.05,
    311.295,
    460.544,
    465.25,
    474.5,
    392.85,
    345.05,
    311.295,
    574.258,
    575.08,
    589.5,
    395.81,
    503.798,
    405.9174,
    322.9,
    331.81,
    338.4,
    551.829,
    598.326,
    490.63,
    667.5,
    673.4,
    768.6,
    560.07,
    324.22,
    379.405,
    193.69,
    203.65,
    159.297,
    474.144,
    402.57,
    466.863,
    828.46,
    908.81,
    99.14,
    482.53,
    381.34,
    386.894,
    478.4503,
    471.1,
    506.8,
    420.04,
    331.56,
    406.694,
    504.6,
    567.22,
    269.432,
    474.144,
    402.57,
    466.863,
    796.426,
    863.86,
    254.2,
    588.38,
    464.34,
    684.77,
    804.3,
    816.4,
    997.4,
    588.38,
    464.34,
    684.77,
    889.5,
    910.6,
    1079.7,
    392.0247,
    448.56,
    673.49,
    322.9,
    331.81,
    338.4,
    528.83,
    475.37,
    473.09,
    679.69,
    735.2,
    767.5,
    377.568,
    357.569,
    350.501,
    198.86,
    197.66,
    114.931,
    527.08,
    412.28,
    638.503,
    691.08,
    666.66,
    300.48,
    532.11,
    426.02,
    423.84,
    467.55,
    497.1,
    511.9,
    424.76,
    348.38,
    396.192,
    543.694,
    525.3,
    440.25,
    527.08,
    412.28,
    638.503,
    729.995,
    612.41,
    300.33,
    535.94,
    516.121,
    625.628,
    836.13,
    920.7,
    996.8,
    535.94,
    516.121,
    625.628,
    916.15,
    1009.5,
    1095.6,
    443.305,
    301.328,
    272.984,
    138.75,
    151.84,
    111.35,
]

NORM_MIN_THRESHOLDS = [
    -382.62,
    -363.81,
    -315.691,
    -472.2,
    -471.4,
    -152.398,
    -382.62,
    -363.81,
    -315.691,
    -586.3,
    -581.46,
    -213.082,
    -400.4931,
    -468.4,
    -409.871,
    -336.8,
    -336.2,
    -104.739,
    -404.083,
    -506.99,
    -490.27,
    -643.29,
    -709.84,
    -519.774,
    -463.02,
    -315.637,
    -405.5037,
    -200.59,
    -196.846,
    -203.74,
    -377.15,
    -423.992,
    -337.331,
    -817.74,
    -739.91,
    -1089.284,
    -310.29,
    -424.74,
    -383.529,
    -465.34,
    -481.5,
    -218.357,
    -442.215,
    -348.157,
    -295.41,
    -541.82,
    -494.74,
    -644.24,
    -377.15,
    -423.992,
    -337.331,
    -766.42,
    -619.98,
    -1181.528,
    -521.9,
    -581.145,
    -550.187,
    -860.24,
    -882.35,
    -645.613,
    -521.9,
    -581.145,
    -550.187,
    -936.12,
    -982.14,
    -719.986,
    -606.395,
    -471.892,
    -484.5629,
    -336.8,
    -336.2,
    -104.739,
    -406.6129,
    -502.94,
    -481.81,
    -669.58,
    -703.12,
    -508.703,
    -490.22,
    -322.88,
    -322.929,
    -203.25,
    -203.721,
    -201.102,
    -420.154,
    -466.13,
    -450.62,
    -779.69,
    -824.456,
    -1081.284,
    -341.5005,
    -396.88,
    -450.036,
    -486.2,
    -486.1,
    -222.305,
    -444.08,
    -353.589,
    -380.33,
    -516.3,
    -503.152,
    -640.27,
    -420.154,
    -466.13,
    -450.62,
    -774.03,
    -798.599,
    -1178.882,
    -417.297,
    -495.1,
    -565.544,
    -906.02,
    -901.77,
    -731.921,
    -417.297,
    -495.1,
    -565.544,
    -990.83,
    -991.36,
    -803.9,
    -351.1281,
    -290.558,
    -269.311,
    -159.9403,
    -153.482,
    -162.718,
]


def normalize(data):
    """Normalizes all sensor channels
    :param data: numpy integer matrix
        Sensor data
    :return:
        Normalized sensor data
    """
    try:
        max_list = np.array(NORM_MAX_THRESHOLDS)
        min_list = np.array(NORM_MIN_THRESHOLDS)
        diffs = max_list - min_list
        for i in np.arange(data.shape[1]):
            data[:, i] = (data[:, i] - min_list[i]) / diffs[i]
        #     Checking the boundaries
        data[data > 1] = 0.99
        data[data < 0] = 0.00
    except Exception as e:
        raise e

    return data


def __get_combinations__():
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )
    attribute_combinations = np.genfromtxt(
        join(__location__, "attr_per_class.txt"), delimiter=",", dtype=int
    )
    return np.unique(attribute_combinations, axis=0)


def __attr_to_class__(attr_vec: np.ndarray, combinations: np.ndarray) -> np.ndarray:
    assert combinations.shape[0] > 0

    logging.debug(f"{attr_vec = }")

    tmp = np.argwhere((combinations[:, 1:] == attr_vec.round()).all(axis=1))
    if tmp.shape[0] == 1:
        idx = tmp.flatten().item()
    elif tmp.shape[0] == 0:
        # find closest one
        dist = spatial.distance.cdist(
            combinations[:, 1:], attr_vec.reshape(1, -1), "cosine"
        )
        idx = np.argmin(dist.flatten())
    else:
        raise ValueError(f"{tmp.shape[0] = } must be in [0,1]")

    logging.debug(f"{idx = }")

    n_labels = np.unique(combinations[:, 0]).flatten().shape[0]
    label = combinations[idx, 0]
    logging.debug(f"{label = }")
    one_hot = np.zeros(n_labels, dtype=np.int8)
    one_hot[label] = 1
    logging.debug(f"{one_hot = }")
    return one_hot


def get_annotation_vector(attr_vector: np.ndarray) -> np.ndarray:
    combinations = __get_combinations__()
    label_one_hot = __attr_to_class__(attr_vector, combinations)
    x = np.append(label_one_hot, attr_vector).astype(dtype=np.int8)
    assert x.shape[0] == 27
    return x


if __name__ == "__main__":
    combs = __get_combinations__()
    print(combs[5])

    arr = combs[5, 1:]
    attr_vec = get_annotation_vector(arr)
    print(attr_vec)
