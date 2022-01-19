import numpy as np


def data_retention(*data, retentionsize=0):
    """ Store retentionsize data; cannot save if data size change
     input: data and retention size
     return: ndarray"""
    if not hasattr(data_retention, 'nparray'):
        data_retention.nparray = np.empty((retentionsize, len(data))) * np.nan
        data_retention.count = 0
    if data_retention.nparray.shape[1] == len(data):
        if retentionsize > data_retention.nparray.shape[0]:
            data_retention.nparray = np.vstack([data_retention.nparray,
                                                np.empty((retentionsize - data_retention.nparray.shape[0],
                                                          len(data))) * np.nan])
            data_retention.nparray = np.roll(data_retention.nparray, 1, axis=0)
            data_retention.nparray[0] = data
        else:
            data_retention.nparray = np.resize(data_retention.nparray, (retentionsize, len(data)))
            data_retention.nparray = np.roll(data_retention.nparray, 1, axis=0)
            data_retention.nparray[0] = data
    else:
        print('excess data unable to store ')
    return data_retention.nparray


if __name__ == '__main__':
    for i in range(1, 20):
        if i < 5:
            a = data_retention(i, i, retentionsize=2)
            print(a, i)
        elif 5 <= i < 10:
            print(data_retention(i, i, retentionsize=5), i)
        else:
            print(data_retention(i, i, retentionsize=3), i)