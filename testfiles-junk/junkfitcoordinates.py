import numpy as np
import pandas as pd
import pymap3d as pm
from geographiclib.geodesic import Geodesic
from scipy import stats
import junkdataretention


def point_on_line(a, b, p):
    ap = p - a
    ab = b - a
    result = a + np.dot(ap, ab) / np.dot(ab, ab) * ab
    return result


def coordinate_fit(df):
    """ Fit the coordinates; [[lat1, lng1, t1], [lat2, lng2, t2]"""
    geod = Geodesic(6378388, 1 / 297.0)
    df = pd.DataFrame(df, columns=['lat', 'lon', 't'])
    df['h'] = df.apply(lambda h: 0, axis=1)
    lat1, lng1 = lat2, lng2 = df['lat'][0], df['lon'][0]
    if len(df.lat) > 3:
        ' Convert to cartesian coordinate'
        df['e'], df['n'], df['u'] = pm.geodetic2enu(df.lat[0:len(df.lat)-1], df.lon[0:len(df.lat)-1], df.h[0:len(df.lat)-1],
                                                    df.lat[len(df.lat)-1], df.lon[len(df.lat)-1], df.h, ell=None, deg=True)
        df = df.dropna()
        m, n = df['e'], df['n']
        p1, p2 = np.array([df.e[0], df.n[0]]), np.array([df.e[len(df.e) - 1], df.n[len(df.n) - 1]])

        ' Apply linear regression'
        slope, intercept, r_value, p_value, std_err = stats.linregress(m, n)
        df['line'] = intercept + slope * m
        'perpendicular on the '
        a = np.array([df['e'][0], df['line'][0]])
        b = np.array([df.e[len(df['e']) - 1], df.line[len(df['line']) - 1]])
        x_1, y_1 = point_on_line(a, b, p1)
        x_2, y_2 = point_on_line(a, b, p2)
        'Back to the lat lng'
        lat1, lng1, _h1 = pm.enu2geodetic(x_1, y_1, df.h[0], df.lat[0], df.lon[0], df.h[0], ell=None, deg=True)
        lat2, lng2, _h2 = pm.enu2geodetic(x_2, y_2, df.h[0], df.lat[0], df.lon[0], df.h[0], ell=None, deg=True)
    'heading angle, speed calculation'
    tme_start = str(df.t[len(df.t)-1])
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
        print('Time differences is zero.')
        speed = 0
    result = {'lat1': lat1, 'lng1': lng1, 'tme1': float(tme_start),
              'lat2': lat2, 'lng2': lng2, 'tme2': float(tme_last),
              'speed': speed, 'ha': ha, 'dis12': distance}

    # result = {'lat1': lat1, 'lng1': lng1,'lat2': lat2, 'lng2': lng2}
    return result


if __name__ == '__main__':
    daa = pd.read_csv('20220104-212027-UTC_0-CAT3-IVER3-3089.log', header=0, delimiter=';')
    lat = daa['Latitude']
    lng = daa['Longitude']
    tme = daa['Time']
    for i in range(100):
        a = junkdataretention.data_retention(lat[i], lng[i], ''.join(tme[i].split(':')), retentionsize=10)
        print(a)
        print(coordinate_fit(a))
        i +=1