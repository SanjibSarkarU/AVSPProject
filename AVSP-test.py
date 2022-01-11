import tkinter as tk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib import (pyplot as plt, animation)
import threading
import time
import logging
import socket
from queue import Queue
import artgallery as ag
import fungnss as fg

__author__ = 'Sanjib Sarkar'
__copyright__ = ''
__credits__ = ['', '']
__license__ = ''
__version__ = '1.0.0'
__date__ = 'Jan11, 2022'
__maintainer__ = 'Sanjib Sarkar'
__email__ = 'sanjib.sarkar@usm.edu'
__status__ = 'test'

UDP_IP = 'localhost'
UDP_PORT = 10000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((UDP_IP, UDP_PORT))

q_co_lvs = Queue()


def coordinates():
    while True:
        try:
            data, addr = sock.recvfrom(1350)  # buffer size is 1024
            data = data.decode()
            coordinate = fg.gpglldecode(data)
            lat_w_c, lng_w_c, tme = coordinate['Lat_dd'], coordinate['Lng_dd'], coordinate['time']
            q_co_lvs.put({'lat': lat_w_c, 'lng': lng_w_c, 'tme': tme})
        except Exception as e:
            print('Exception at coordinates function', e)


def lvs():
    time.sleep(2)
    iver_art = ag.ImageArtist(gal, label='wam-v animation', alpha=1, zorder=4)
    trace_art = ag.LineArtist(gal, label='vam-v trace', c='g', alpha=0.6, zorder=3)
    icon_size = 0.02
    iver_art.add_data_to_artist('WAM-V_icon_small.png', icon_size, (0, 0), 0)
    while True:
        lead_coordinate = q_co_lvs.get()
        x_pos, y_pos = lead_coordinate['lng'], lead_coordinate['lat']
        new_xy = (x_pos, y_pos)
        deg = 65  # * (math.cos(2 * (math.pi / x_range) * (x_pos - iver_art.ax.get_xlim()[0])) - 90)
        iver_art.set_position(new_xy, deg)
        trace_art.add_data_to_artist(new_xy)
        # i += 0.01
        # if (x_pos - iver_art.ax.get_xlim()[0]) > x_range:
        #     trace_art.clear_data()
        #     i = 0
        time.sleep(0.1)


def plot_geotif():
    """Work in progress..."""
    sat = ag.GeoTifArtist(gal, label='Sat plot', zorder=5, alpha=1, add_artist_to_init_func=True)
    sat.add_data_to_artist('Cat_Island_Low_2.tif')

    noaachart = ag.GeoTifArtist(gal, label='Cat Island ENC', zorder=6, alpha=0.6, add_artist_to_init_func=True)
    noaachart.add_data_to_artist('Cat_Island_ENC.tif')

    sat.set_xlim(sat.geotif_xlim[0], sat.geotif_xlim[1])
    sat.set_ylim(sat.geotif_ylim[0], sat.geotif_ylim[1])

    while True:
        time.sleep(5)


def _quit():
    root.quit()
    root.destroy()


def holdani(anim):
    while True:
        time.sleep(10)
        print('animation holted')
        anim.pause()
        time.sleep(10)
        anim.resume()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)  # print to console
    root = tk.Tk()
    root.wm_title("plot on map")
    fig = plt.Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)

    gal = ag.Gallerist(ax, fig)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    button = tk.Button(master=root, text="Quit", command=_quit)
    button.pack(side=tk.BOTTOM)

    # Using init function is much faster in terms of updating but slower to rescale. It also is not stable!!!
    anim = animation.FuncAnimation(gal.fig, gal.animate, init_func=gal.init_func, interval=100, blit=True)

    threading.Thread(target=plot_geotif, daemon=True).start()
    threading.Thread(target=coordinates, daemon=True).start()
    threading.Thread(target=lvs, daemon=True).start()
    tk.mainloop()

