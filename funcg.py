__author__ = 'Sanjib Sarkar'
__copyright__ = ''
__credits__ = ['', '']
__license__ = ''
__version__ = '1.0.0'
__date__ = '01/19/2022'
__maintainer__ = 'Sanjib Sarkar'
__email__ = 'sanjib.sarkar@usm.edu'
__status__ = 'Prototype'

import numpy as np
from geographiclib.geodesic import Geodesic
import pandas as pd
import pymap3d as pm
from scipy import stats


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
            'retentionsize is greater than the previous retensionsize'
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
            'retentionsize is less than the previous retensionsize'
            data_retention.nparray = np.resize(data_retention.nparray, (retentionsize, len(data)))
            data_retention.nparray = np.roll(data_retention.nparray, 1, axis=0)
            data_retention.nparray[0] = data
            data_retention.retention_size = retentionsize
        return data_retention.nparray[~np.isnan(data_retention.nparray).any(axis=1)]
    else:
        raise RuntimeError('The number of input arguments in data_retention changed.' +
                           'The number of input arguments in data_retention can not be changed after first use.')


def point_on_line(a, b, p):
    """ Returns coordinate of the point p which is perpendicular on the line between a and b."""
    ap = p - a
    ab = b - a
    result = a + np.dot(ap, ab) / np.dot(ab, ab) * ab
    return result


def vehiclestate(df) -> dict:
    """ Fit the coordinates; [[lat1, lng1, t1], [lat2, lng2, t2]]
    returns: {'lat1': lat1, 'lng1': lng1, 'tme1': float(tme_start),
                  'lat2': lat2, 'lng2': lng2, 'tme2': float(tme_last),
                  'speed': speed, 'ha': ha, 'dis12': distance}"""

    geod = Geodesic(6378388, 1 / 297.0)
    df = pd.DataFrame(df, columns=['lat', 'lon', 't'])
    df['h'] = 0
    if len(df.lat) > 2:
        ' Convert to local coordinate system'
        df['e'], df['n'], df['u'] = pm.geodetic2enu(df.lat, df.lon, df.h, df.lat[len(df.lat) - 1],
                                                    df.lon[len(df.lat) - 1],
                                                    df.h, ell=None, deg=True)
        df = df.dropna()
        p1, p2 = np.array([df.e[0], df.n[0]]), np.array([df.e[len(df.e) - 1], df.n[len(df.n) - 1]])
        ' Apply linear regression'
        slope, intercept, r_value, p_value, std_err = stats.linregress(df['e'], df['n'])
        angle = np.arctan(slope)
        print('Angle: ', angle, slope)
        if slope > 1 or slope < -1:
            slope, intercept, r_value, p_value, std_err = stats.linregress(df['n'], df['e'])
            print('Axis swapped')
            df['line'] = intercept + slope * df['n']
            a = np.array([df['n'][0], df['line'][0]])
            b = np.array([df.n[len(df['n']) - 1], df.line[len(df['line']) - 1]])
            p1, p2 = np.array([df.n[0], df.e[0]]), np.array([df.n[len(df.n) - 1], df.e[len(df.e) - 1]])
            y_1, x_1 = point_on_line(a, b, p1)
            y_2, x_2 = point_on_line(a, b, p2)
        else:
            df['line'] = intercept + slope * df['e']
            a = np.array([df['e'][0], df['line'][0]])
            b = np.array([df.e[len(df['e']) - 1], df.line[len(df['line']) - 1]])
            'perpendicular on the '
            x_1, y_1 = point_on_line(a, b, p1)
            x_2, y_2 = point_on_line(a, b, p2)

        'Back to the lat lng'
        lat1, lng1, _h1 = pm.enu2geodetic(x_1, y_1, df.h[0], df.lat[len(df.lat) - 1], df.lon[len(df.lat) - 1], df.h[0],
                                          ell=None, deg=True)
        lat2, lng2, _h2 = pm.enu2geodetic(x_2, y_2, df.h[0], df.lat[len(df.lat) - 1], df.lon[len(df.lat) - 1], df.h[0],
                                          ell=None, deg=True)
        'heading angle, speed calculation'
        tme_start = str(df.t[len(df.t) - 1])
        tme_last = str(df.t[0])
        d = geod.Inverse(float(lat1), float(lng1), float(lat2), float(lng2))
        distance = d['s12']
        ha = d['azi2']
        time_diff = (int(tme_last[0:2]) * 3600 + int(tme_last[2:4]) * 60 + float(tme_last[4:])) - \
                    (int(tme_start[0:2]) * 3600 + int(tme_start[2:4]) * 60 + float(tme_start[4:]))
        try:
            speed = distance / time_diff
            # result = {'speed': speed, 'ha': ha, 'dis12': distance}
        except ZeroDivisionError:
            print('Time difference is zero.')
            speed = 0
        result = {'lat1': lat1, 'lng1': lng1, 'tme1': float(tme_start),
                  'lat2': lat2, 'lng2': lng2, 'tme2': float(tme_last),
                  'speed': speed, 'ha': ha, 'dis12': distance}
        return result
    else:
        raise RuntimeError('Not enough data to fit')


if __name__ == '__main__':
    for i in range(1, 20):
        if i < 5:
            a = data_retention(i, i, i, retentionsize=2)
            print(a, i)
        elif 5 <= i < 10:
            print(data_retention(i, i,  retentionsize=5), i)
        else:
            print(data_retention(i, i, i, retentionsize=3), i)
