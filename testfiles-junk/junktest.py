import logging
import time
import numpy as np
import pymap3d as pm
from scipy import stats
from geographiclib.geodesic import Geodesic
import artgallery as ag
import tkinter as tk
from matplotlib import (pyplot as plt, animation)
import threading
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)


def point_on_line(a, b, p):
    ap = p - a
    ab = b - a
    result = a + np.dot(ap, ab) / np.dot(ab, ab) * ab
    return result


def heading(x, y):
    geod = Geodesic(6378388, 1 / 297.0)
    if not hasattr(heading, 'data'):
        heading.data = np.empty((y, len(x))) * np.nan
        heading.count = 0
        # heading.e = heading.n = heading.u = np.empty(y) * np.nan
        heading.h = np.zeros(y)
    heading.data[0] = x
    e = n = u = np.empty(heading.count+1) * np.nan
    al = 0
    # heading.lat0, heading.ln0 = heading.data[heading.count][0], heading.data[heading.count][1]
    # e, n, u = pm.geodetic2enu(heading.data[0:heading.count+1][0], heading.data[0:heading.count+1][1], heading.h[heading.count],
    #     heading.lat0, heading.ln0, heading.h[heading.count], ell=None, deg=True)
    while al <= heading.count:
        heading.lat0, heading.ln0 = heading.data[heading.count][0], heading.data[heading.count][1]
        ' Convert to cartesian coordinate'
        e[0], n[0], u[0] = pm.geodetic2enu(
            heading.data[al][0], heading.data[al][1], heading.h[heading.count],
            heading.lat0, heading.ln0, heading.h[heading.count], ell=None, deg=True)
        e = np.roll(e, 1)
        n = np.roll(n, 1)
        u = np.roll(u, 1)
        al += 1
    print('e::::', e)
    lat1, lng1 = heading.data[0][0], heading.data[0][1]
    lat2, lng2 = heading.data[heading.count][0], heading.data[heading.count][1]

    if heading.count > 2:
        p2 = np.array([e[0], n[0]])
        p1 = np.array([e[heading.count], n[heading.count]])
        # e = np.array(heading.e[~np.isnan(heading.e)])
        # n = np.array(heading.n[~np.isnan(heading.n)])
        # print('e', e)
        ' Apply linear regression'
        slope, intercept, r_value, p_value, std_err = stats.linregress(e, n)
        # line = list(map(lambda b: intercept + slope * b, heading.e))
        line = intercept + slope * e
        'perpendicular on the '
        b = np.array([e[0], line[0]])
        a = np.array([e[heading.count], line[heading.count]])
        x_1, y_1 = point_on_line(a, b, p1)
        x_2, y_2 = point_on_line(a, b, p2)
        'Back to the lat lng'
        lat1, lng1, _h1 = pm.enu2geodetic(x_1, y_1, heading.h[heading.count], heading.lat0, heading.ln0,
                                          heading.h[heading.count], ell=None, deg=True)
        lat2, lng2, _h2 = pm.enu2geodetic(x_2, y_2, heading.h[heading.count], heading.lat0, heading.ln0,
                                          heading.h[heading.count], ell=None, deg=True)
    tme_start = str(heading.data[heading.count][-1])
    tme_last = str(heading.data[0][-1])
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

    heading.data = np.roll(heading.data, 1, axis=0)  # roll trough axis

    heading.count = heading.count if heading.count >= y-1 else heading.count + 1
    return result


def test_fit():
    daa = pd.read_csv('../20220104-212027-UTC_0-CAT3-IVER3-3089.log', header=0, delimiter=';')
    lat = daa['Latitude']
    lng = daa['Longitude']
    tme = daa['Time']

    sctter_ori = ag.ScatterArtist(gal, s=40, marker='o',  label='original location')
    sctter_fit_a = ag.ScatterArtist(gal, s=20, marker='*', c='r', label='after fitting')
    sctter_fit_b = ag.ScatterArtist(gal, s=20, marker='X', alpha=0.5, label='after fitting')
    # sctter_ori.set_xlim(min=lng[0], max=lng[len(lng)-1])
    # sctter_ori.set_ylim(min=lat[0], max=lat[len(lat)-1])
    # sctter_ori.set_xlim(min=-89.0815868500, max=-89.08149442350692)
    # sctter_ori.set_ylim(min=30.2601162000, max=30.260170774102900)
    sctter_ori.set_xlim(min=-89.0815869500, max=-89.08135937721608)
    sctter_ori.set_ylim(min=30.2601162000, max=30.26024044069797)

    # sctter_fit.set_xlim(min=-89.0815852770, max=-89.0815450572)
    # sctter_fit.set_ylim(min=30.2601181123, max=30.2601379353)

    for i in range(1, 50):
        print((lng[i], lat[i]))
        fitted_data = heading(x=[lat[i], lng[i], ''.join(tme[i].split(':'))], y=9)
        sctter_ori.add_data_to_artist((lng[i], lat[i]))
        print(fitted_data)
        sctter_fit_a.add_data_to_artist((fitted_data['lng1'], fitted_data['lat1']))
        sctter_fit_b.add_data_to_artist((fitted_data['lng2'], fitted_data['lat2']))
        time.sleep(1)


def _quit():
    root.quit()
    root.destroy()


if __name__ == '__main__':
    import pandas as pd

    logging.basicConfig(level=logging.INFO)  # print to console

    root = tk.Tk()
    root.wm_title("Test")
    fig = plt.Figure(figsize=(6,6), dpi=100)
    ax = fig.add_subplot(111)
    # ax = fig.add_subplot(xlim=(, 2), ylim=(-1.1, 1.1))

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    button = tk.Button(master=root, text="Quit", command=_quit)
    button.pack(side=tk.BOTTOM)

    gal = ag.Gallerist(ax, fig)

    threading.Thread(target=test_fit, daemon=True).start()

    anim = animation.FuncAnimation(gal.fig, gal.animate, init_func=gal.init_func, interval=100, blit=True)
    tk.mainloop()
