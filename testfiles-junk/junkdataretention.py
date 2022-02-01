import numpy as np


def data_retention(*data, retentionsize=0):
    """ Store retentionsize data; cannot save if changes in the data size
     input: data and retention size
     return: ndarray"""
    if not hasattr(data_retention, 'nparray'):
        data_retention.nparray = np.empty((retentionsize, len(data))) * np.nan
        data_retention.data_size = len(data)  # edit contions
        data_retention.retention_size = retentionsize
    if data_retention.data_size == len(data):
        if retentionsize > data_retention.retention_size:
            data_retention.nparray = np.vstack([data_retention.nparray,
                                                np.empty((retentionsize - data_retention.retention_size,
                                                          len(data))) * np.nan])
            data_retention.nparray = np.roll(data_retention.nparray, 1, axis=0)
            data_retention.nparray[0] = data
            data_retention.retention_size = retentionsize
        elif retentionsize == data_retention.retention_size:
            data_retention.nparray = np.roll(data_retention.nparray, 1, axis=0)
            data_retention.nparray[0] = data
        elif retentionsize < data_retention.retention_size:
            'retentionsize '
            data_retention.nparray = np.resize(data_retention.nparray, (retentionsize, len(data)))
            data_retention.nparray = np.roll(data_retention.nparray, 1, axis=0)
            data_retention.nparray[0] = data
            data_retention.retention_size = retentionsize
        return data_retention.nparray[~np.isnan(data_retention.nparray).any(axis=1)]
    else:
        raise RuntimeError('The number of input arguments in data_retention changed.' +
                           'The number of input arguments in data_retention can not be changed after first use.')


if __name__ == '__main__':
    for i in range(1, 20):
        if i < 5:
            a = data_retention(i, i, i, retentionsize=2)
            print(a, i)
        elif 5 <= i < 10:
            print(data_retention(i, i, i, retentionsize=5), i)
        else:
            print(data_retention(i, i, i, retentionsize=3), i)

