"""
A library to allow the sending of artists from threads to matplotlib.animation.FuncAnimation
During registration of the various X_Artits objects, the artists get registered by the
ArtistManager function. When an object gets out of scope, the artist gets deleted from
the list of artists.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
import numpy as np
import threading
import queue
import logging
import time
import rasterio
from bisect import bisect
from matplotlib import pyplot as plt
from matplotlib import transforms
from matplotlib import animation
from matplotlib import artist

__author__ = 'Gero Nootz'
__copyright__ = ''
__credits__ = ['', '']
__license__ = ''
__version__ = '1.0.0'
__date__ = '12/26/2021'
__maintainer__ = 'Gero Nootz'
__email__ = 'gero.nootz@usm.edu'
__status__ = 'Prototype'

lock = threading.Lock()

class Add_del_art(Enum):
    add_to_animation_func = auto()
    add_to_init_func = auto()
    delete_from_animation_func = auto()
    delete_from_init_func = auto()

class Gallerist(queue.Queue):
    """
    manages objects of type Artist(ABC) to animate via 
    matplotlib.animation.FuncAnimation.    
    When Artist(ABC) gos out to scope, the artist is deleted from the list of artists. 
    """
    def __init__(self, ax: plt.axes, fig: plt.figure, **kwarks):
        self.ax = ax
        self.fig = fig
        self.animation_artists = []
        self.animation_artist_zorder_list = []
        self.animation_artist_ids = []
        self.init_artists = []
        self.init_artist_zorder_list = []
        self.init_artist_ids = []
        self.q_art = queue.Queue()
        threading.Thread(target=self.__art_manager, daemon = True).start()
        self.anim = animation.FuncAnimation(self.fig,
                                    self.animate,
                                    init_func=self.init_func,
                                    blit=True, **kwarks)
    
    def __art_manager(self):
        """
        Collects new artists received from ABC Artist(ABC) into a list of artists
        to be animated in matplotlib.animation.FuncAnimation.
        When the destructor of Artist(ABC) is called the artist is deleted from the
        list of artists. 
        -> returns a list of artists
        """
        while True:   
            art_obj = self.q_art.get() # notification to add or delete artist
            match art_obj.add_or_del_artist:
                case Add_del_art.add_to_animation_func:      
                    logging.info('added artist with label: %s to animation', art_obj.kwargs['label'])          
                    art_obj.register_ax(self.ax)
                    art_obj.register_fig(self.fig)
                    animation_artist = art_obj.create_artist()
                    # order artists according to zorder
                    zorder_value = animation_artist.get_zorder()
                    zpos = bisect(self.animation_artist_zorder_list, zorder_value)
                    self.animation_artist_zorder_list.insert(zpos, zorder_value)
                    self.animation_artist_ids.insert(zpos, id(art_obj))
                    self.animation_artists.insert(zpos, animation_artist)
                    art_obj.set_artist_exsits(True)
                case Add_del_art.add_to_init_func: # add to init_func
                    logging.info('added artist with label: %s to init_func', art_obj.kwargs['label'])
                    art_obj.register_ax(self.ax)
                    art_obj.register_fig(self.fig)
                    animation_artist = art_obj.create_artist()
                    # order artists according to zorder
                    zorder_value = animation_artist.get_zorder()
                    zpos = bisect(self.init_artist_zorder_list, zorder_value)
                    self.init_artist_zorder_list.insert(zpos, zorder_value)
                    self.init_artist_ids.insert(zpos, id(art_obj))
                    self.init_artists.insert(zpos, animation_artist)
                    art_obj.set_artist_exsits(True)
                case Add_del_art.delete_from_init_func:
                    logging.info('deleted artist with label: %s from init_func', art_obj.kwargs['label'])
                    index = self.init_artist_ids.index(id(art_obj))
                    del self.init_artist_ids[index]
                    del self.init_artist_zorder_list[index]
                    del self.init_artists[index]
                    art_obj.set_artist_exsits(False)
                case Add_del_art.delete_from_animation_func:
                    logging.info('deleted artist with label: %s from animation', art_obj.kwargs['label'])
                    # remove artist from gallery
                    index = self.animation_artist_ids.index(id(art_obj))
                    del self.animation_artist_ids[index]
                    del self.animation_artist_zorder_list[index]
                    del self.animation_artists[index]  
                    art_obj.set_artist_exsits(False)    
                case _:
                    logging.error('not of enum type Add_del_art')

            art_obj = None # delete ref to object so destructor can be called


    def animate(self, i) -> list:
        """
        Returns a list of artists to be animated in matplotlib.animation.FuncAnimation
        -> returns a list of artists
        """
        with lock:
            pass # lock until update by append_data_to_artist() is complete
   
        return self.animation_artists   

            
    def init_func(self):
        """
        Returns a list of artists to initialize matplotlib.animation.FuncAnimation
        -> returns a list of artists
        """
        with lock:
            pass # lock until update by append_data_to_artist() is complete
        logging.info('artgallery.init_func called')  
        return self.init_artists

class Artist(ABC):
    """
    Abstract base class for sending a new artist to artist_manager() function to be added to a list of artists
    When the destructor of Artist(ABC) is called the artist is deleted from the
    list of artists. 
    """

    def __init__(self, gallerist: Gallerist, **kwargs):
        self.q_art = gallerist.q_art
        self.kwargs = kwargs
        self.add_artist_to_init_func = False

        # remove keys that do not belong to artists and set where to add the artist to
        if "add_artist_to_init_func" in self.kwargs:
            self.add_artist_to_init_func =  self.kwargs.pop('add_artist_to_init_func')

        if self.add_artist_to_init_func:
            self.add_or_del_artist = Add_del_art.add_to_init_func
        else:
            self.add_or_del_artist = Add_del_art.add_to_animation_func

        self.artist_exsits = False
        self.q_art.put(self) # notify Gallerist that a new artist was instantiated
        while self.artist_exsits == False: # wait for artist creation by gallerist
            time.sleep(0.1)

    def __del__(self):
        if self.add_artist_to_init_func:
            self.add_or_del_artist = Add_del_art.delete_from_init_func
        else:
            self.add_or_del_artist = Add_del_art.delete_from_animation_func

        self.q_art.put(self) # notify Gallerist that a artist is getting deleted
        while self.artist_exsits == True: #wait for deletion of artist by gallerist
            time.sleep(0.1)   

    @abstractmethod
    def create_artist(self):
        """ Create artist of varius types -> artist"""        

    @abstractmethod
    def add_data_to_artist(self, data) -> None:
        """ add new data to artist
        all privous data is discarded """   
             

    @abstractmethod
    def append_data_to_artist(self, new_data) -> None:
        """ append new data to artist """        

    @abstractmethod
    def clear_data(self)-> None:
        """Clear all data from artist"""        

    def register_ax(self, ax: plt.axes):
            self.ax = ax

    def register_fig(self, fig: plt.figure):
        self.fig = fig
    
    def set_artist_exsits(self, artist_exsits):
        self.artist_exsits = artist_exsits

    def set_xlim(self, min: float, max: float):
        """ set x axis limits"""
        self.ax.set_xlim(min, max)
        self.fig.canvas.draw()

    def set_ylim(self, min: float, max: float):
        """ set y axis limits"""
        self.ax.set_ylim(min, max)
        self.fig.canvas.draw()

class ImageArtist(Artist):
    """ 
    Create an image artist and send to __art_manger() method of a Gallerist object.
    Manipulate the data from within a thread using the methods provided, e.g., 
    append_data_to_artist()
    """

    def create_artist(self):
        self.artist = self.ax.imshow([[]], extent=(
            0, 1, 0, 1), animated=True, aspect='equal', **self.kwargs)
        return self.artist

    def add_data_to_artist(self, fname: str, size: float, position, deg: float):
        """ 
        !!!!!!!!!! Cleanup requierd !!!!!!!!!!!!!!!!
        
        Add data to artist    
        """
        with lock: # prevent animation while updating
            self.size = size
            left, right = self.ax.get_xlim() 
            bottom, top = self.ax.get_ylim()

            del_x = (right - left)*self.size
            del_y = (top - bottom)*self.size
            aspect = del_x/del_y  
            aspect = 1 
            left = -del_x + position[0]
            right = del_x + position[0]
            bottom = -del_x*aspect + position[1]
            top = del_x*aspect + position[1]
            # print('LRBT1: ', left, right, bottom, top)     
            trans_data = transforms.Affine2D().rotate_deg_around(
                position[0], position[1], deg) + self.ax.transData
            self.artist.set_transform(trans_data)  
            plt.setp(self.artist, extent=(left, right, bottom, top))
            self.image = plt.imread(fname)
            self.artist.set_array(self.image)

    def append_data_to_artist(self, fname: str, size: float, position, deg: float):
        """ 
        !!!!!!!!!! Cleanup requierd !!!!!!!!!!!!!!!!
        
        Add data to artist    
        """
        with lock: # prevent animation while updating
            self.size = size
            left, right = self.ax.get_xlim() 
            bottom, top = self.ax.get_ylim()

            del_x = (right - left)*self.size
            del_y = (top - bottom)*self.size
            aspect = del_x/del_y  
            aspect = 1 
            left = -del_x + position[0]
            right = del_x + position[0]
            bottom = -del_x*aspect + position[1]
            top = del_x*aspect + position[1]
            # print('LRBT1: ', left, right, bottom, top)     
            trans_data = transforms.Affine2D().rotate_deg_around(
                position[0], position[1], deg) + self.ax.transData
            self.artist.set_transform(trans_data)  
            plt.setp(self.artist, extent=(left, right, bottom, top))
            self.image = plt.imread(fname)
            self.artist.set_array(self.image)        
    
    def set_position(self, position, deg):
        with lock: # prevent animation while updating
            # print('pos: ', position)
            left, right = self.ax.get_xlim() 
            bottom, top = self.ax.get_ylim()

            del_x = (right - left)*self.size
            del_y = (top - bottom)*self.size
            aspect = del_x/del_y         
            aspect = 1 
            left = -del_x + position[0]
            right = del_x + position[0]
            bottom = -del_x*aspect + position[1]
            top = del_x*aspect + position[1]

            trans_data = transforms.Affine2D().rotate_deg_around(
                position[0], position[1], deg) + self.ax.transData
            self.artist.set_transform(trans_data)
            # print('LRBT: ', left, right, bottom, top)
            plt.setp(self.artist, extent=(left, right, bottom, top))
        
    def clear_data(self):
        with lock: # prevent animation while updating
            self.artist.set_array([[]])

class GeoTifArtist(Artist):
    """ 
    Create an GeoTif artist and send to __art_manger() method of a Gallerist object.
    Manipulate the data from within a thread using the methods provided, e.g., 
    append_data_to_artist()
    """
    
    def create_artist(self):
        self.artist = self.ax.imshow([[]], extent=(
            0, 1, 0, 1), origin='upper', animated=True, aspect='equal', **self.kwargs)
        return self.artist

    def add_data_to_artist(self, data) -> None:
        """ add new data to artist
        all privous data is discarded """   
        pass
    
    def append_data_to_artist(self, fname: str):
        with lock: # prevent animation while updating
            with rasterio.open(fname, driver='GTiff') as geotif: 
                if geotif.crs != 'EPSG:4326':
                    logging.error('the file origon of %s is not EPSG:4326', fname)
                    raise Warning('the file origon of the geotif is not EPSG:4326')  
                self.geotif_xlim=(geotif.bounds.left, geotif.bounds.right)
                self.geotif_ylim=(geotif.bounds.bottom, geotif.bounds.top)
                rgb = np.dstack((geotif.read(1), geotif.read(2), geotif.read(3)))
            
            plt.setp(self.artist, extent=(
                geotif.bounds.left, geotif.bounds.right, geotif.bounds.bottom, geotif.bounds.top))
            self.artist.set_array(rgb)
    
    def clear_data(self):
        with lock: # prevent animation while updating
            self.artist.set_array([[]])
            

class ScatterArtist(Artist):
    """
    Create a scatter artist and send to __art_manger() method of a Gallerist object.
    Manipulate the data from within a thread using the methods provided, e.g., 
    append_data_to_artist()
    """

    def create_artist(self):
        self.art_data = np.array([], dtype=float).reshape(0, 2)
        self.artist = self.ax.scatter([], [], animated=True, **self.kwargs)
        return self.artist

    def add_data_to_artist(self, data: np.array, **kwargs) -> None:
        """Add new data to artist.
        All privous data is discarded """   
        row, col = data.shape
        if col != 2:
            raise ValueError(f'input has dimension ({row}, {col}) but dimension (n, 2) is required')
        self.art_data = data
        # print(artist.get(self.artist))
        self.artist.set_offsets(self.art_data)
        if 'facecolors' in kwargs:
            self.artist.set_facecolors(kwargs.get("facecolors"))
            


    def append_data_to_artist(self, new_data):
        # print(np.shape(new_data))
        with lock: # prevent animation while updating
            self.art_data = np.vstack(
                [self.art_data, [[ new_data[0], new_data[1] ]] ])
            self.artist.set_offsets(self.art_data)

    def clear_data(self):
        with lock: # prevent animation while updating
            self.art_data = np.array([], dtype=float).reshape(
                0, 2)  # prepare (N,2) array
            self.artist.set_offsets(self.art_data)

class LineArtist(Artist):
    """ 
    Create a line plot artist and send to __art_manger() method of a Gallerist object.
    Manipulate the data from within a thread using the methods provided, e.g., 
    append_data_to_artist()
    """

    def create_artist(self):
        self.art_data = np.array([], dtype=float).reshape(0, 2)
        self.artist, = self.ax.plot([], [], animated=True, **self.kwargs)
        return self.artist

    def add_data_to_artist(self, data) -> None:
        """ add new data to artist
        all privous data is discarded """   
        pass    

    def append_data_to_artist(self, new_data):
        with lock: # prevent animation while updating (works so so)
            self.art_data = np.append(
                self.art_data, [new_data], axis=0)            
            # The program crashes when the array is updated while being plotted
            self.artist.set_data(self.art_data[:, 0], self.art_data[:, 1])

    def clear_data(self):
        with lock: # prevent animation while updating
            self.art_data = np.array([], dtype=float).reshape(
                0, 2)  # prepare (N,2) array
            self.artist.set_data(self.art_data[:, 0], self.art_data[:, 1])


if __name__ == '__main__':
    """
    Demonstrate how to update a matplotlib graph from inside a thread
    """
    import tkinter as tk
    from matplotlib.backends.backend_tkagg import (
        FigureCanvasTkAgg, NavigationToolbar2Tk)


    logging.basicConfig(level=logging.INFO) # print to console
    # logging.basicConfig(filename='main.log', encoding='utf-8', level=logging.DEBUG) # append to file
    # logging.basicConfig(filename='example.log', filemode='w', level=logging.INFO) # overide file each run

    
    def holdani(anim):
        """Demonstrate pausing an animation"""
        while True:
            time.sleep(10)    
            print('animation holted')
            anim.pause()
            time.sleep(10) 
            print('animation resumed')
            anim.resume()  


    def plot_geotif(gal: Gallerist): 
        time.sleep(10)
        """Work in progress..."""
        artist = GeoTifArtist(gal, label='GeoTif plot', zorder=(-1))
        artist.append_data_to_artist('Stennis_QW.tif')
        artist.set_xlim(artist.geotif_xlim[0], artist.geotif_xlim[1])
        artist.set_ylim(artist.geotif_ylim[0], artist.geotif_ylim[1])
        while True: 
            time.sleep(2)

    def plot_image(): 
        """Work in progress..."""
        # image = plt.imread('yota.png')    
        artist = ImageArtist(gal, label='image plot')
        artist.append_data_to_artist('yota.png', 0.1, (1,0), 0)
        while True: 
            data = np.random.rand(2)    
            new_xy = (data[0]*2, data[1]*2 - 1) 
            artist.set_position(new_xy, np.random.rand()*360)
            time.sleep(1)            

    
    class PlotRandLine(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self, daemon=True)

        def run(self): 
            delay = np.random.rand()*10    
            sleep = np.random.rand() 
        
            artist = LineArtist(gal, label='line plot', zorder=10)
            logging.debug('createdg artist %i for provide_line1', id(artist))

            time.sleep(delay)   

            i = 0
            while True:        
                data = np.random.rand(2)    
                new_xy = (data[0]*2, data[1]*2 - 1) 
                artist.append_data_to_artist(new_xy)
                if i%10 == 0:
                    artist.clear_data()
                i += 1
                time.sleep(sleep)


    class PlotRandScetter(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self, daemon=True)

        def run(self): 
            """ 
            Demonstrates how to plot a scatter artist from a thread using
            append_data_to_artist(new_xy)
            """       
            scatter_artist = ScatterArtist(gal, s=60, marker='^', label='scatter plot')
            while True:        
                data = np.random.rand(10,2)
                data[:, 1] = (data[:, 1] * 2) - 1
                data[:, 0] = data[:, 0] * 2
                scatter_artist.add_data_to_artist(data, facecolors=np.random.rand(10,4))
                # self.artist.set_facecolors(np.random.rand(10,4))
                time.sleep(1)     
    

    def animate_rand_scatter(): 
        """ 
        Demonstrates how to plot a scatter artist from a thread using
        append_data_to_artist(new_xy)
        """
        delay = np.random.rand()*10    
        sleep = np.random.rand()         
        scatter_artist = ScatterArtist(gal, s=60, marker='x', label='scatter plot animation')
        logging.debug('createdg artist %i for animate_rand_scatter', id(scatter_artist))
        time.sleep(delay) 
        i = 0
        while True:        
            data = np.random.rand(2)    
            new_xy = (data[0]*2, data[1]*2-1) 
            scatter_artist.append_data_to_artist(new_xy)
            if i%10 == 0:
                scatter_artist.clear_data()
            i += 1
            time.sleep(sleep)

    def plot_temp_scatter(): 
        '''
        Demonstrate deleting objects and with it removing  artistsclear
        after some time via the destructor
        '''

        delay = np.random.rand()*10
        sleep = np.random.rand() 

        scatter_artist = ScatterArtist(gal, s=60, marker='o', label='temp scatter plot', zorder=(3))
        logging.debug('createdg artist %i for provide_scatter2', id(scatter_artist))

        time.sleep(delay)
        
        for i in range(10):          
            data = np.random.rand(2)    
            new_xy = (data[0]*2, data[1]*2-1) 
            scatter_artist.append_data_to_artist(new_xy)
            time.sleep(sleep)     

  
    root = tk.Tk()
    root.wm_title("Update mpl in Tk via queue")

    fig = plt.Figure()

    ax = fig.add_subplot(xlim=(0, 2), ylim=(-1.1, 1.1))
    ax.set_xlabel('x-data')
    ax.set_ylabel('y-data')

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    button = tk.Button(master=root, text="Quit", command=root.quit)
    button.pack(side=tk.BOTTOM)

    toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
    toolbar.update()
    toolbar.pack(side=tk.BOTTOM, fill=tk.X)     

    gal = Gallerist(ax, fig, interval=10)

    PlotRandLine().start()   # demonstrate class container 
    threading.Thread(target=plot_temp_scatter, daemon = True).start()        
    threading.Thread(target=animate_rand_scatter, daemon = True).start()        
    threading.Thread(target=plot_image, daemon = True).start()   
    threading.Thread(target=plot_geotif, args=(gal,), daemon = True).start()   
    PlotRandScetter().start()

    # demonstrate pausing the animation
    # threading.Thread(target=holdani, args=(gal.anim,), daemon = True).start()   

    tk.mainloop()
