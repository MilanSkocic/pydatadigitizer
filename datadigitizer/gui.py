r"""
Main GUI.

Copyright (C) 2020-2021 Milan Skocic.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Milan Skocic <milan.skocic@gmail.com>
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import sys
import webbrowser
import pathlib
from typing import Union
import numpy as np
from matplotlib import image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from . import version
from .settings import read_cfg, read_profiles, save_cfg
from .settings import CFG_FOLDER, DEFAULT_PROFILE_VALUES
from .tests import test_linear, test_ylog, test_loglog, test_xlog


class Transform(object):
    r"""Class for coordinate transformation. See __init__.__doc__."""

    def __init__(self, values_min: float, values_max: float,
                 pix_min: Union[int, float], pix_max: Union[int, float],
                 which: str = 'linear'):
        r"""
        Transform class converting values coordinates into pixel coordinates.

        Parameters
        ----------
        values_min: int, float
            Minimum value.
        values_max: int, float
            Maximum value.
        pix_min: int, float
            Minimum pixel.
        pix_max: int, float
            Maximum pixel.
        which: str, optional
            Which kind of transform i.e. linear or log.
        """

        if which not in ['linear', 'log']:
            raise ValueError('which must be either linear or log.')

        self._which = which

        self.x1_min = values_min
        self.x1_max = values_max
        self.x2_min = pix_min
        self.x2_max = pix_max

        self._x1_min = self.x1_min
        self._x1_max = self.x1_max
        self._x2_min = self.x2_min
        self._x2_max = self.x2_max

        if self._which == 'log':
            self._x1_min = np.log10(values_min)
            self._x1_max = np.log10(values_max)

        self._dx2 = self._x2_max - self._x2_min
        self._dx1 = self._x1_max - self._x1_min

    def _prepare_x(self, x: Union[float, int, np.ndarray]):
        if self._which == 'log':
            return np.log10(x)
        else:
            return x

    def forward(self, x: Union[int, float, np.ndarray]):
        r"""
        Transform values to pixels.

        Parameters
        -----------
        x: int or floats or array-like, shape(n,)
            Values to be transformed.

        Returns
        --------
        pixels: int or floats or array-like, shape(n,)
            Values corresponding to the pixels.

        Notes
        ----------
        .. math::

            x_{pix} = (x-x_{min})\frac{x_{pix, max} - x_{pix, min}}{x_{max}-x_{min}} + x_{pix,min}
            
        """
        _x = self._prepare_x(x)
        x_forward = (_x - self._x1_min) * self._dx2 / self._dx1 + self._x2_min
        return x_forward

    def backward(self, x: Union[int, float, np.ndarray]):
        r"""
        Transform pixels to values.

        Parameters
        -----------
        x: int or floats or array-like, shape(n,)
            Pixels to be transformed.

        Returns
        --------
        values: int or floats or array-like, shape(n,)
            Values corresponding to the pixels.
        
        Notes
        ----------
        .. math::

            x = (x_{pix}-x_{pix, min})\frac{x_{max} - x_{min}}{x_{pix,max}-x_{pix, min}} + x_{min}
        """
        x_backward = (x - self._x2_min) * self._dx1 / self._dx2 + self._x1_min
        if self._which == 'log':
            return 10 ** x_backward
        else:
            return x_backward

    @property
    def forward_scale(self):
        r"""Return the scale for transforming values into pixels.
        
        .. math::

            \frac{x_{pix, max} - x_{pix, min}}{x_{max}-x_{min}}

        """
        return self._dx2 / self._dx1

    @property
    def backward_scale(self):
        r"""Return the scale for transforming pixels into values.
        
        .. math::

            \frac{x_{max} - x_{min}}{x_{pix,max}-x_{pix, min}}
        
        """
        return self._dx1 / self._dx2


class FigureFrame(ttk.Frame):
    r"""
    Class for encapsulating a matplotlib figure and a toolbar. See __init__.__doc__"""
    def __init__(self, master, **kwargs):
        r"""
        Tk frame encapsulating a matplotlib figure and a toolbar.

        Parameters
        ------------
        kwargs: dict, optional
            Keyword arguments for the tk frame.
        """
        super().__init__(master, **kwargs)
        self.master = master

        self.figure = Figure()
        self.subplot = self.figure.add_subplot(111)

        # frame widgets and grid properties
        nrows = 1
        for i in range(nrows):
            self.rowconfigure(index=i, weight=1)
        cols = 1
        for i in range(cols):
            self.columnconfigure(index=i, weight=1)

        nrows = 2
        for i in range(nrows):
            self.rowconfigure(index=i, weight=1)
        ncols = 0
        for i in range(ncols):
            self.columnconfigure(index=i, weight=1)

        # top frame => figure and toolbar
        container = self
        self.canvas = FigureCanvasTkAgg(self.figure, master=container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, expand=tk.TRUE, fill=tk.BOTH)

        self.toolbar = NavigationToolbar2Tk(self.canvas, container)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, expand=tk.TRUE, fill=tk.BOTH)

    def refresh(self):
        r"""
        Refresh the plot.
        """
        self.subplot.relim()
        self.subplot.autoscale()
        self.subplot.autoscale_view()
        self.canvas.draw()


class ScrolledFrame(ttk.Frame):
    r"""Class for scrolled frames. See __init__.__doc__."""

    def __init__(self, master, **kwargs):
        r"""
        Scrolled Frame widget which may contain other widgets and can have a 3D border.

        Parameters
        ------------
        master: tkinter widget
            Master container.
        kwargs: dict, optional
            Keyword arguments for the scrolled frame.
        """
        ttk.Frame.__init__(self, master)
        self._default_options = {'scrolled': 'y'}
        self.pack(expand=tk.TRUE, fill=tk.BOTH)
        for i in kwargs:
            if i not in self._default_options.keys():
                raise tk.TclError('Unknow option --' + i)

        self._default_options.update(kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.yscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.xscrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL)

        if self._default_options['scrolled'] == 'y':
            self.yscrollbar.grid(row=0, column=1, sticky='ns')
        elif self._default_options['scrolled'] == 'x':
            self.xscrollbar.grid(row=1, column=0, sticky='ew')
        elif self._default_options['scrolled'] == 'both':
            self.yscrollbar.grid(row=0, column=1, sticky='ns')
            self.xscrollbar.grid(row=1, column=0, sticky='ew')
        else:
            raise tk.TclError('Bad scroll style \"' + 
                              self._default_options['scrolled'] + 
                              '\" must be x, y or both')

        self._canvas = tk.Canvas(self, bd=0, relief=tk.FLAT, 
                                 yscrollcommand=self.yscrollbar.set,
                                 xscrollcommand=self.xscrollbar.set)
        self._canvas.grid(row=0, column=0, sticky='nswe')

        self.yscrollbar.config(command=self._canvas.yview)
        self.xscrollbar.config(command=self._canvas.xview)

        self._canvas.config(scrollregion=self._canvas.bbox(tk.ALL))

        self._frame = ttk.Frame(self._canvas)
        self._frame.pack(expand=tk.TRUE, fill=tk.BOTH)
        self._frame.bind('<Configure>', self._update_canvas_window_size)

        self._canvas_window_id = self._canvas.create_window(0, 0, window=self._frame, anchor='nw')
        self._canvas.itemconfig(self._canvas_window_id, width=self._frame.winfo_reqwidth())
        self._canvas.bind("<Configure>", self._update_canvas_window_size)

    def _update_canvas_window_size(self, event):
        r"""Update canvas size when window is resized."""
        if event.width <= self._frame.winfo_reqwidth():
            self._canvas.itemconfig(self._canvas_window_id, width=self._frame.winfo_reqwidth())
        else:
            self._canvas.itemconfig(self._canvas_window_id, width=event.width)

        if event.height <= self._frame.winfo_reqheight():
            self._canvas.itemconfig(self._canvas_window_id, height=self._frame.winfo_reqheight())
        else:
            self._canvas.itemconfig(self._canvas_window_id, height=event.height)

        self._update_canvas_bbox()

    def _update_canvas_bbox(self):
        r"""Update scroll region when window is resized."""
        self._canvas.config(scrollregion=self._canvas.bbox(tk.ALL))

    @property
    def frame(self):
        r"""Return the frame that contains the widgets."""
        return self._frame

    @property
    def canvas(self):
        r"""Return the canvas that contains the scrollbars."""
        return self._canvas


class AboutWindow(tk.Toplevel):
    r"""Class for about window. See __init__.__doc__."""
    def __init__(self, master):
        r"""
        About window.

        Parameters
        ----------
        master: tkinter widget
            Container.
        """
        super().__init__(master)
        self.transient(master)

        self.master = master
        self.title('About')

        self.grab_set()

        self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self._quit)

        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        width = int(0.65*ws)
        height = int(0.1*hs)
        x = int((ws / 2) - (width / 2))
        y = int((hs / 2) - (height / 2) - 25)
        self.geometry(f'{width}x{height}+{x}+{y}')
        self.resizable(height=False, width=False)

        self.frame = ttk.Frame(self)
        self.frame.pack(fill=tk.BOTH, expand=tk.TRUE)

        for i in range(2):
            self.frame.grid_rowconfigure(i, weight=1)
        for i in range(1):
            self.frame.grid_columnconfigure(i, weight=1)

        msg = version.__package_name__ + ': ' + version.__version__
        label = ttk.Label(self.frame, text=msg)
        label.configure(anchor='center')
        label.grid(row=0, column=0, sticky='nswe')

        msg = 'Python : ' + sys.version.replace('\n', ' ')
        label = ttk.Label(self.frame, text=msg)
        label.configure(anchor='center')
        label.grid(row=1, column=0, sticky='nswe')

        self.initial_focus.focus_set()
        self.wait_window(self)

    def _quit(self):
        r"""Close the top level window."""
        self.master.focus_set()
        self.destroy()


class HowToUse(tk.Toplevel):
    r"""Class for quick help window. See __init__.__doc__."""
    def __init__(self, master):
        r"""
        How to use window.

        Parameters
        ----------
        master: tkinter widget
            Container.
        """
        super().__init__(master)
        self.transient(master)

        self.master = master
        self.title('How To Use')

        self.grab_set()

        self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self._quit)

        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        width = int(0.5*ws)
        height = int(0.7*hs)
        x = int((ws / 2) - (width / 2))
        y = int((hs / 2) - (height / 2) - 25)
        self.geometry(f'{width}x{height}+{x}+{y}')
        kwargs = {'scrolled': 'both'}
        self.sframe = ScrolledFrame(self, **kwargs)

        msg = self.master.__init__.__doc__.split('Parameters')[0]
        label = ttk.Label(self.sframe.frame, text=msg)
        label.configure(anchor='w', justify='left')
        label.grid(row=0, column=0, sticky='nswe')

    def _quit(self):
        r"""Close the toplevel window."""
        self.master.focus_set()
        self.destroy()


class DataTable(ScrolledFrame):
    r"""Scrolled data table. See __init__.__doc__."""
    def __init__(self, master, **kwargs):
        r"""
        Scrolled data table widget.

        Parameters
        ------------
        master: tkinter widget
            Master container.
        kwargs: dict, optional
            Keyword arguments for the scrolled frame.
        """
        ScrolledFrame.__init__(self, master, **kwargs)
        self.pack(expand=tk.TRUE, fill=tk.BOTH)

        self._ncols = 8
        self._nrows = 0
        self._headers = None
        self._has_header = False

        self._data = None

        # do not check number of columns because it is always the same
        self._wdg_line = np.zeros(shape=(1, self._ncols), dtype=np.object_)
        self._wdg_line_tkvar = np.zeros(shape=(1, self._ncols), dtype=np.object_)

        self._wdg_array = np.zeros(shape=(0, self._ncols), dtype=np.object_)
        self._wdg_array_tkvar = np.zeros(shape=(0, self._ncols), dtype=np.object_)

    def set_new_data(self, data):
        """Set new data in the displayed data table.

        Parameters
        ----------
        data : structured array, shape=(n,) 
            Numpy structured array used for registering the extracted data.
        """
        
        nrows = data.shape[0]

        # difference between old and new array
        d = nrows - self._nrows
        if d == 0:
            sign = 0
        else:
            sign = d / abs(d)

        self._data = data
        self._nrows = self._data.shape[0]
        self._ncols = len(self._data.dtype.names)
        self._headers = self._data.dtype.names

        if not self._has_header:
            for j in range(self._ncols):
                ttk.Label(self.frame, text=self._headers[j]).grid(row=0, column=j, sticky='nswe')
            self._has_header = True

        for j in range(self._ncols):
            self.frame.grid_columnconfigure(j, weight=1)
        for i in range(self._nrows+1):
            self.frame.grid_rowconfigure(i, weight=0)

        for i in range(abs(d)):
            if sign > 0:
                self._add_line()
            elif sign < 0:
                self._remove_line()

        self._display()


    def _create_line_widget(self):

        for j in range(self._ncols):
            self._wdg_line_tkvar[0, j] = tk.StringVar()
            self._wdg_line[0, j] = ttk.Label(self.frame, 
                                             textvariable=self._wdg_line_tkvar[0, j])

    def _grid_widgets(self):
        for i, j in np.ndindex(self._wdg_array.shape):
            self._wdg_array[i, j].grid(row=i+1, column=j, sticky='nswe')
        
    def _add_line(self):
        self._create_line_widget()
        self._wdg_array = np.append(self._wdg_array, self._wdg_line, axis=0)        
        self._wdg_array_tkvar = np.append(self._wdg_array_tkvar, self._wdg_line_tkvar, axis=0)        

    def _remove_line(self):
        
        if self._wdg_array.shape[0] > 0:
            for j in range(self._ncols):
                self._wdg_array[-1, j].destroy()
                self._wdg_array[-1, j] = np.empty

            self._wdg_array = np.delete(self._wdg_array, -1, axis=0)
            self._wdg_array_tkvar = np.delete(self._wdg_array_tkvar, -1, axis=0)

    def _update_widget_values(self):
        for i, j in np.ndindex(self._wdg_array.shape):
            col = self._headers[j]
            value = self._data[col][i]
            self._wdg_array_tkvar[i, j].set(value)

    def _display(self):

        self._update_widget_values()
        self._grid_widgets()
        

class DataWindow(tk.Toplevel):
    r"""Class for data window. See __init__.__doc__."""
    def __init__(self, master):
        r"""
        How to use window.

        Parameters
        ----------
        master: tkinter widget
            Container.
        """
        super().__init__(master)
        self.transient(master)

        self.master = master
        self.title('Data Table')

        self.grab_set()

        self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self._quit)

        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        width = int(0.5*ws)
        height = int(0.7*hs)
        x = int((ws / 2) - (width / 2))
        y = int((hs / 2) - (height / 2) - 25)
        self.geometry(f'{width}x{height}+{x}+{y}')
        kwargs = {'scrolled': 'both'}
        self.datatable = DataTable(self, **kwargs)
        self.datatable.pack(fill=tk.BOTH, expand=tk.TRUE)

    def _quit(self):
        self.master.focus_set()
        self.destroy()

class App(ttk.Frame):
    r"""Class for main graphical interface. See __init__.__doc__."""

    def __init__(self, master=None):
        r"""
        The cursor is used to point a specific position in the graph
        whereas all operations are done through keyboard combinations or through the main menu.

        Legend:

        - Red crosses are data points
        - Blue crosses are Xmin and Xmax
        - Green crosses are Ymin and Ymax

        Commands:

        * <Ctrl-o> for loading image.
        * <Ctrl-a> add data point.
        * <Hold a+Left Click> add data point.
        * <Left Click> select a data point.
        * <Hold Ctrl+Left Click> multiple data point selection.

        * <Ctrl-g> set Xmin from last data point or from selected data point.
        * <Ctrl-h> set Xmax from last data point or from selected data point.

        * <Ctrl-j> set Ymin from last data point or from selected data point.
        * <Ctrl-k> set Ymax from last data point or from selected data point

        * <Ctrl-l> set all limits from last 4 data points or from last 4 selected data points.
        * <Ctrl-n> remove all limits.

        * <Ctrl-z> remove last data point.
        * <Ctrl-d> remove selected data point.
        * <Ctrl-D> remove all data points.

        * <Ctrl-m> compute the data points.
        * <Ctrl-t> view data table.
        * <Ctrl-s> save data points.
        * <Ctrl-w> clear all.

        Parameters
        ------------
        master: tkinter.Tk instance
            Root instanciation of tkinter.
        """
        # main frame
        ttk.Frame.__init__(self, master)
        self.pack(expand=tk.YES, fill=tk.BOTH)
        self.master.title('Data Digitizer')
        folder = pathlib.Path(__file__).parent
        self.master.iconphoto(True, tk.PhotoImage(file=folder / 'icon.png'))
        self.master.protocol("WM_DELETE_WINDOW", self.stop)
        self.url_download = 'http://www.github.com/MilanSkocic/PyDatadigitizer'
        self.url = 'https://milanskocic.github.io/PyDatadigitizer/index.html'
        self._filepath = None

        # profiles
        self._profiles_ini = read_profiles()

        # folders configuration
        profile_name = 'folders'
        self._folders_profile = read_cfg(cfg_folder=CFG_FOLDER,
                                         cfg_name=profile_name,
                                         cfg_default=DEFAULT_PROFILE_VALUES[profile_name],
                                         update=True)

        # bindings
        self.master.bind('<Control-o>', self._cb_open)
        self.master.bind('<Control-d>', self._cb_delete_selected)
        self.master.bind('<Control-D>', self._cb_delete_all)
        self.master.bind('<Control-w>', self._cb_clear)
        self.master.bind('<Control-q>', self._cb_quit)
        self.master.bind('<Control-g>', self._cb_set_xmin)
        self.master.bind('<Control-h>', self._cb_set_xmax)
        self.master.bind('<Control-j>', self._cb_set_ymin)
        self.master.bind('<Control-k>', self._cb_set_ymax)
        self.master.bind('<Control-m>', self._cb_measure)
        self.master.bind('<Control-s>', self._cb_save)
        self.master.bind('<Control-l>', self._cb_set_all_limits)
        self.master.bind('<Control-n>', self._cb_delete_limits)
        self.master.bind('<Control-z>', self._cb_undo)
        self.master.bind('<Control-t>', self._cb_datatable)

        # get screen width and height
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        # master.geometry(("%dx%d")%(ws,hs))
        width = int(0.75 * ws)
        height = int(0.75 * hs)
        x = int((ws / 2) - (width / 2))
        y = int((hs / 2) - (height / 2) - 25)
        self.master.geometry(f'{width}x{height}+{x}+{y}')

        # Grid config
        tk.Grid.columnconfigure(self, 0, weight=0)
        tk.Grid.columnconfigure(self, 1, weight=1)
        tk.Grid.rowconfigure(self, 0, weight=1)
        tk.Grid.rowconfigure(self, 1, weight=0)

        # flags and variables
        profile_type = 'folders'
        folders_profile_name = self._profiles_ini.defaults()[profile_type].upper()
        self._image_folder = self._folders_profile.get_typed_option(section=folders_profile_name,
                                                                    option='image folder')
        self._image_name = self._folders_profile.get_typed_option(section=folders_profile_name,
                                                                  option = 'image name')
        self._data_folder = self._folders_profile.get_typed_option(section=folders_profile_name,
                                                                  option = 'data folder')
        self._data_name = self._folders_profile.get_typed_option(section=folders_profile_name,
                                                                  option = 'data name')
        self._axes_image = None
        self._axes_image_threshold = None
        # self._data_indexes = []
        self._percentage = 0.01
        self._percentage_shift = 0.05
        self.R, self.G, self.B, self.alpha = 0, 1, 2, 3
        self.dtypes = [('type', 'U32'),
                       ('i', 'i4'),
                       ('j', 'i4'),
                       ('Xpix', 'i4'),
                       ('Ypix', 'i4'),
                       ('x', 'f8'),
                       ('y', 'f8'),
                       ('selected', 'i2')]
        self._line = np.zeros(shape=(1,), dtype=self.dtypes)
        self._data_array = np.zeros(shape=(0,), dtype=self.dtypes)
        self._triggered_event = None
        self.row = None
        self.col = None
        self._ctrl_key_pressed = False
        self._a_key_pressed = False

        # Menu
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        # File Menu
        self.file_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.file_menu, label='File')
        self.file_menu.add_command(label='Load Image <Ctrl-o>', command=self._trigger_load_event)
        self.file_menu.add_command(label='Save Data <Ctrl-s>', command=self._trigger_save_event)
        self.file_menu.add_command(label='Clear All <Ctrl-w>', command=self._trigger_clearall_event)
        self.file_menu.add_command(label='Quit <Ctrl-q>', command=self.stop)

        # Data Menu
        self.data_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.data_menu, label='Data')
        self.data_menu.add_command(label='Add <Ctrl-a> or <Hold a+Left Click>',
                                   command=self._trigger_add_event)
        self.data_menu.add_command(label='Remove last <Ctrl-z>', 
                                   command=self._trigger_undo_event)
        self.data_menu.add_command(label='Remove all <Ctrl-D>', 
                                   command=self._trigger_delete_all_event)
        self.data_menu.add_command(label='Remove selected <Ctrl-d>',
                                   command=self._trigger_delete_selected_event)
        self.data_menu.add_separator()
        self.data_menu.add_command(label='Set Xmin <Ctrl-g>', 
                                   command=self._trigger_xmin_event)
        self.data_menu.add_command(label='Set Xmax <Ctrl-h>', 
                                   command=self._trigger_xmax_event)
        self.data_menu.add_command(label='Set Ymin <Ctrl-j>', 
                                   command=self._trigger_ymin_event)
        self.data_menu.add_command(label='Set Ymax <Ctrl-k>', 
                                   command=self._trigger_ymax_event)
        self.data_menu.add_command(label='Set all limits <Ctrl-l>',
                                   command=self._trigger_all_limits_event)
        self.data_menu.add_command(label='Remove all limits <Ctrl-n>',
                                   command=self._trigger_delete_all_limits_event)
        self.data_menu.add_separator()
        self.data_menu.add_command(label='Compute <Ctrl-m>', 
                                   command=self._trigger_measure_event)
        self.data_menu.add_command(label='View Data <Ctrl-t>', 
                                   command=self._trigger_datatable_event)

        # Test Menu
        self.test_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.test_menu, label='Tests')
        self.test_menu.add_command(label="Test Linear", command=self._test_linear)
        self.test_menu.add_command(label="Test YLog", command=self._test_ylog)
        self.test_menu.add_command(label="Test XLog", command=self._test_xlog)
        self.test_menu.add_command(label="Test LogLog", command=self._test_loglog)

        # Help Menu
        self.help_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.help_menu, label='Help')
        self.help_menu.add_command(label='About', command=self._about)
        self.help_menu.add_command(label='How to use', command=self._how_to_use)
        self.help_menu.add_command(label='Online Documentation', command=self._online_documentation)
        self.help_menu.add_command(label='GitHub Sources', command=self._sources)

        # panes
        self.left_frame = ttk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky='nswe')
        for i in range(2):
            tk.Grid.columnconfigure(self.left_frame, i, weight=1)

        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=0, column=1, sticky='nswe')
        tk.Grid.columnconfigure(self.right_frame, 0, weight=1)
        tk.Grid.rowconfigure(self.right_frame, 0, weight=1)

        # figure
        self._figframe = FigureFrame(self.right_frame)
        self._fig = self._figframe.figure
        self._ax = self._figframe.subplot
        self._canvas = self._figframe.canvas
        self._canvas_widget = self._figframe.canvas.get_tk_widget()
        self._ax.set_axis_off()
        self._figframe.canvas.mpl_connect("key_press_event", self._cb_key_press)
        self._figframe.canvas.mpl_connect("button_press_event", self._cb_button_press)
        self._figframe.canvas.mpl_connect('key_release_event', self._cb_key_release)
        self._figframe.grid(row=0, column=0, sticky='nswe')

        # Help Label
        row = 0

        style = ttk.Style()

        style.configure('Xlimits.TEntry')
        style.map('Xlimits.TEntry', foreground=[('focus', 'blue')])

        style.configure('Ylimits.TEntry')
        style.map('Ylimits.TEntry', foreground=[('focus', 'green')])

        style.configure('TestData.TEntry')
        style.map('TestData.TEntry', foreground=[('focus', 'red')])

        # X Axis
        row = row + 1
        container = self.left_frame
        sep = ttk.Separator(container, orient="horizontal")
        sep.grid(row=row, column=0, columnspan=2, sticky='nswe')

        row += 1
        label = ttk.Label(container, text='X Axis')
        label.grid(row=row, column=0, columnspan=2, sticky='nswe')
        self._tkvar_log_xscale = tk.BooleanVar()
        self._tkvar_log_xscale.set(False)
        self._log_xscale_cb = ttk.Checkbutton(container, 
                                              variable=self._tkvar_log_xscale, 
                                              text='log X scale?',
                                              command=self._xlog_scale)
        self._log_xscale_cb.grid(row=row, column=1, sticky='nswe')

        row = row + 1
        ttk.Label(container, text='Xmin=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_xmin = tk.DoubleVar()
        self._tkvar_xmin.set(0.0)
        self._xmin_entry = ttk.Entry(container, 
                                     textvariable=self._tkvar_xmin, 
                                     style='Xlimits.TEntry')
        self._xmin_entry.grid(row=row, column=1, sticky='nswe')
        self._xmin_entry.bind('<Return>', self._cb_measure)

        row += 1
        ttk.Label(container, text='Xmax=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_xmax = tk.DoubleVar()
        self._tkvar_xmax.set(1.0)
        self._xmax_entry = ttk.Entry(container, 
                                     textvariable=self._tkvar_xmax, 
                                     style='Xlimits.TEntry')
        self._xmax_entry.grid(row=row, column=1, sticky='nswe')
        self._xmax_entry.bind('<Return>', self._cb_measure)

        row += 1 # X unit entry
        ttk.Label(container, text='X Unit').grid(row=row, column=0, sticky='nswe')
        self._tkvar_xunit = tk.StringVar()
        self._tkvar_xunit.set('a.u.')
        self._xunit_entry = ttk.Entry(container,
                                      textvariable=self._tkvar_xunit)
        self._xunit_entry.grid(row=row, column=1, sticky='nswe')
        self._xunit_entry.bind('<Return>', self._cb_measure)

        # Y Axis
        row += 1
        container = self.left_frame
        sep = ttk.Separator(container, orient="horizontal")
        sep.grid(row=row, column=0, columnspan=2, sticky='nswe', pady=30)

        row += 1
        label = ttk.Label(self.left_frame, text='Y Axis')
        label.grid(row=row, column=0, columnspan=2, sticky='nswe')
        self._tkvar_log_yscale = tk.BooleanVar()
        self._tkvar_log_yscale.set(False)
        self._log_yscale_cb = ttk.Checkbutton(container, 
                                              variable=self._tkvar_log_yscale, 
                                              text='log Y scale?',
                                              command=self._ylog_scale)
        self._log_yscale_cb.grid(row=row, column=1, sticky='nswe')

        row += 1
        ttk.Label(self.left_frame, text='Ymin=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_ymin = tk.DoubleVar()
        self._tkvar_ymin.set(0.0)
        self._ymin_entry = ttk.Entry(container, 
                                     textvariable=self._tkvar_ymin, 
                                     style='Ylimits.TEntry')
        self._ymin_entry.grid(row=row, column=1, sticky='nswe')
        self._ymin_entry.bind('<Return>', self._cb_measure)

        row += 1
        label = ttk.Label(self.left_frame, text='Ymax=')
        label.grid(row=row, column=0, sticky='nswe')
        self._tkvar_ymax = tk.DoubleVar()
        self._tkvar_ymax.set(1.0)
        self._ymax_entry = ttk.Entry(container, 
                                     textvariable=self._tkvar_ymax, 
                                     style='Ylimits.TEntry')
        self._ymax_entry.grid(row=row, column=1, sticky='nswe')
        self._ymax_entry.bind('<Return>', self._cb_measure)

        row += 1 # Y unit entry
        ttk.Label(container, text='Y Unit').grid(row=row, column=0, sticky='nswe')
        self._tkvar_yunit = tk.StringVar()
        self._tkvar_yunit.set('a.u.')
        self._yunit_entry = ttk.Entry(container,
                                      textvariable=self._tkvar_yunit)
        self._yunit_entry.grid(row=row, column=1, sticky='nswe')
        self._yunit_entry.bind('<Return>', self._cb_measure)

        # Data
        row += 1
        container = self.left_frame
        sep = ttk.Separator(container, orient="horizontal")
        sep.grid(row=row, column=0, columnspan=2, sticky='nswe', pady=30)

        row += 1
        label = ttk.Label(self.left_frame, text='N points=')
        label.grid(row=row, column=0, sticky='nswe')
        self._tkvar_npoints = tk.IntVar()
        self._tkvar_npoints.set(0)
        label = ttk.Label(container, textvariable=self._tkvar_npoints)
        label.grid(row=row, column=1, sticky='nswe')

        row += 1
        sep = ttk.Separator(container, orient="horizontal")
        sep.grid(row=row, column=0, columnspan=2, sticky='nswe', pady=30)

        # Test scale
        row += 1
        label = ttk.Label(container, text='Test values with defined scale:')
        label.grid(row=row, column=0, columnspan=2, sticky='nswe')

        row += 1
        ttk.Label(container, text='X=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_xtest = tk.DoubleVar()
        self._tkvar_xtest.set(1)
        self._xtest_entry = ttk.Entry(container, 
                                      textvariable=self._tkvar_xtest, 
                                      style='TestData.TEntry')
        self._xtest_entry.grid(row=row, column=1, sticky='nswe')
        self._xtest_entry.bind('<Return>', self._cb_test_data)

        row += 1
        ttk.Label(container, text='Y=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_ytest = tk.DoubleVar()
        self._tkvar_ytest.set(1)
        self._ytest_entry = ttk.Entry(container, 
                                      textvariable=self._tkvar_ytest, 
                                      style='TestData.TEntry')
        self._ytest_entry.grid(row=row, column=1, sticky='nswe')
        self._ytest_entry.bind('<Return>', self._cb_test_data)

        self._reset_ui()

    def _reset_ui(self):

        self._tkvar_log_xscale.set(False)
        self._tkvar_log_yscale.set(False)

        self._tkvar_npoints.set(0)

        self._tkvar_xmin.set(0.0)
        self._tkvar_xmax.set(1.0)
        self._tkvar_ymin.set(0.0)
        self._tkvar_ymax.set(1.0)

    def _about(self):
        AboutWindow(self)

    def _how_to_use(self):
        HowToUse(self)

    def _cb_open(self, event):
        self._triggered_event = event
        self._open_image()
        self._load_image()

    def _cb_undo(self, event):
        self._triggered_event = event
        self._undo()

    def _cb_delete_all(self, event):
        self._triggered_event = event
        self._delete_all()

    def _cb_delete_selected(self, event):
        self._triggered_event = event
        self._delete_selected()

    def _cb_delete_limits(self, event):
        self._triggered_event = event
        self._delete_limits()

    def _cb_clear(self, event):
        self._triggered_event = event
        self._clear_all()

    def _cb_key_press(self, event):
        self._triggered_event = event
        if self._axes_image is not None:
            dx = int(self.row * self._percentage_shift)
            dy = int(self.col * self._percentage_shift)
            if event.key == 'ctrl+a':
                if (event.xdata is not None) and (event.ydata is not None):
                    j = int(round(event.xdata, 0))
                    i = int(round(event.ydata, 0))
                    self._add_data(i, j)
            elif event.key == 'right':
                self._shift_data(direction='right')
            elif event.key == 'ctrl+right':
                self._shift_data(direction='right', d=dx)
            elif event.key == 'left':
                self._shift_data(direction='left')
            elif event.key == 'ctrl+left':
                self._shift_data(direction='left', d=dx)
            elif event.key == 'up':
                self._shift_data(direction='up')
            elif event.key == 'ctrl+up':
                self._shift_data(direction='up', d=dy)
            elif event.key == 'down':
                self._shift_data(direction='down')
            elif event.key == 'ctrl+down':
                self._shift_data(direction='down', d=dy)
            elif event.key == 'control':
                self._ctrl_key_pressed = True
            elif event.key == 'a':
                self._a_key_pressed = True

    def _cb_key_release(self, event):
        self._triggered_event = event
        if self._axes_image is not None:
            if event.key == 'control':
                self._ctrl_key_pressed = False
            elif event.key == 'a':
                self._a_key_pressed = False

    def _cb_button_press(self, event):
        self._triggered_event = event
        if self._axes_image is not None:
            if event.button == 1:
                if (event.xdata is not None) and (event.ydata is not None):
                    if self._data_array.size:
                        y = int(round(event.xdata, 0))
                        x = int(round(event.ydata, 0))
                        dx_lim = int(self.row * self._percentage)
                        dy_lim = int(self.col * self._percentage)
                        dxy_lim = np.sqrt(dx_lim**2 + dy_lim**2)
                        dx = x - self._data_array['i']
                        dy = y - self._data_array['j']
                        dxy = np.sqrt(dx**2 + dy**2)
                        ix = np.argmin(dxy)
                        if dxy[ix] <= dxy_lim:
                            if not self._ctrl_key_pressed:
                                self._data_array['selected'] = 0
                            arr = self._data_array['selected'][ix]
                            self._data_array['selected'][ix] = np.logical_not(arr)
                        else:
                            self._data_array['selected'] = 0

                    if self._a_key_pressed:
                        self._trigger_add_event()
                    self._display_data()

                self._canvas_widget.focus_set()

    def _cb_set_xmin(self, event):
        self._triggered_event = event
        self._add_limits(which='xmin')

    def _cb_set_xmax(self, event):
        self._triggered_event = event
        self._add_limits(which='xmax')

    def _cb_set_ymin(self, event):
        self._triggered_event = event
        self._add_limits(which='ymin')

    def _cb_set_ymax(self, event):
        self._triggered_event = event
        self._add_limits(which='ymax')

    def _cb_measure(self, event):
        self._triggered_event = event
        self._measure()

    def _cb_test_data(self, event):
        self._triggered_event = event
        self._plot_test_data()

    def _cb_set_all_limits(self, event):
        self._triggered_event = event
        if self._data_array.size >= 4:
            self._add_limits(which='ymax')
            self._add_limits(which='ymin')
            self._add_limits(which='xmax')
            self._add_limits(which='xmin')
        else:
            msg = "You must add at least 4 points \
                   before setting all limits at once."
            messagebox.showinfo("Infos", msg)

    def _cb_save(self, event):
        self._triggered_event = event
        if self._measure():
            self._save()

    def _cb_datatable(self, event):
        self._triggered_event = event
        if self._measure():
            datawindow = DataWindow(self)
            datawindow.datatable.set_new_data(self._data_array)

    def _cb_quit(self, event):
        self._triggered_event = event
        self.stop()

    def _trigger_load_event(self):
        self.master.event_generate('<Control-o>')

    def _trigger_add_event(self):
        self._canvas_widget.event_generate('<Control-a>')

    def _trigger_undo_event(self):
        self._canvas_widget.event_generate('<Control-z>')

    def _trigger_save_event(self):
        self.master.event_generate('<Control-s>')

    def _trigger_xmin_event(self):
        self.master.event_generate('<Control-g>')

    def _trigger_xmax_event(self):
        self.master.event_generate('<Control-h>')

    def _trigger_ymin_event(self):
        self.master.event_generate('<Control-j>')

    def _trigger_ymax_event(self):
        self.master.event_generate('<Control-k>')

    def _trigger_clearall_event(self):
        self.master.event_generate('<Control-w>')

    def _trigger_all_limits_event(self):
        self.master.event_generate('<Control-l>')

    def _trigger_delete_all_event(self):
        self.master.event_generate('<Control-D>')

    def _trigger_delete_selected_event(self):
        self.master.event_generate('<Control-d>')

    def _trigger_delete_all_limits_event(self):
        self.master.event_generate('<Control-n>')

    def _trigger_measure_event(self):
        self.master.event_generate('<Control-m>')

    def _trigger_datatable_event(self):
        self.master.event_generate('<Control-t>')

    def _open_image(self):
        _filepath = filedialog.askopenfilename(title='Open Plot',
                                               defaultextension='.png',
                                               filetypes=[('png', '.png'),
                                                          ('jpeg', '.jpeg'),
                                                          ('tif', '.tif'),
                                                          ('all files', '.*')],
                                               initialdir=self._image_folder,
                                               parent=self)
        if len(_filepath) > 0:
            self._filepath = pathlib.Path(_filepath).absolute()
        else:
            self._filepath = None

    def _load_image(self):
        r"""load image"""
        self._clear_all()
        if self._filepath is not None:
            image_array = image.imread(str(self._filepath))
            shape = image_array.shape
            dim = len(shape)
            if dim > 1:
                self._delete_all()
                self._ax.set_axis_on()
                self.row, self.col = image_array.shape[0:2]
                image_threshold = np.zeros(shape=(self.row, self.col, 4))
                self._axes_image = self._ax.imshow(image_array, cmap='Greys_r')
                self._axes_image_threshold = self._ax.imshow(image_threshold)
                self._ax.relim()
                self._canvas.draw()
            else:
                messagebox.showinfo("Infos", f"{self._filepath} is not a valid image (ndim={dim}).")
            self._image_folder = self._filepath.parent
            self._image_name = self._filepath.name

    def _ij_to_xypix(self, i: int, j: int):
        """Convert matrix indexes i,j into graph pixels."""
        xpix = j
        ypix = self.row - i

        return xpix, ypix

    def _xypix_to_ij(self, xpix, ypix):
        """Convert graph pixels into matrix indexes."""
        i = self.row - ypix
        j = xpix

        return i, j

    def _add_data(self, i: int, j: int):
        r"""Add a point."""
        xpix, ypix = self._ij_to_xypix(i, j)
        self._line[0] = ('data', i, j, xpix, ypix, 0, 0, 0)
        self._data_array = np.append(self._data_array, self._line)
        self._display_data()

    def _undo(self):
        r"""Delete last point."""
        indexes = np.argwhere(self._data_array['type'] == 'data')
        if indexes.size:
            self._data_array = np.delete(self._data_array, indexes[-1])
            self._display_data()

    def _add_limits(self, which: str):
        r"""Set limit from the selected or the available points."""
        if self._data_array.size:
            indexes = np.argwhere(self._data_array['type'] == which)
            selected = np.argwhere(self._data_array['selected'] == 1)
            if selected.size >= 1:
                self._data_array['type'][indexes] = 'data'
                self._data_array['type'][selected[-1]] = which
                self._data_array['selected'][selected[-1]] = 0
            else:
                data_indexes = np.argwhere(self._data_array['type'] == 'data')
                if data_indexes.size >= 1:
                    self._data_array['type'][indexes] = 'data'
                    self._data_array['type'][data_indexes[-1]] = which
                    self._data_array['selected'][data_indexes[-1]] = 0
            self._display_data()
        else:
            messagebox.showinfo("Infos", "You must add at least 1 point.")

    def _delete_all(self):
        r"""Delete all points except the limits."""
        indexes = np.argwhere(self._data_array['type'] == 'data')
        if indexes.size:
            self._data_array = np.delete(self._data_array, indexes)
            self._display_data()

    def _delete_selected(self):
        r"""Delete selected points."""
        indexes = np.argwhere((self._data_array['selected'] == 1) \
                              & (self._data_array['type'] == 'data'))
        self._data_array = np.delete(self._data_array, indexes)
        self._display_data()

    def _delete_limits(self):
        r"""Change type from xy lim to data."""
        for which in ['xmin', 'xmax', 'ymin', 'ymax']:
            indexes = np.argwhere(self._data_array['type'] == which)
            if indexes.size:
                self._data_array['type'][indexes] = 'data'
        self._display_data()

    def _clear_all(self):

        self._ax.clear()
        self._axes_image = None
        self._axes_image_threshold = None
        self.row = None
        self.col = None
        self._line = np.zeros(shape=(1,), dtype=self.dtypes)

        self._data_array = np.zeros(shape=(0,), dtype=self.dtypes)
        self._ax.set_axis_off()

        self._reset_ui()

        self._refresh()

    def _shift_data(self, direction: str, d: int = 1):

        if self._data_array.size:
            d = int(abs(d))
            mask = self._data_array['selected'] == 1
            if direction == 'right':
                ypix = self._data_array['j'][mask] + d
                self._data_array['j'][mask] = ypix % self.col
            elif direction == 'left':
                ypix = self._data_array['j'][mask] - d
                self._data_array['j'][mask] = ypix % self.col
            elif direction == 'up':
                xpix = self._data_array['i'][mask] - d
                self._data_array['i'][mask] = xpix % self.row
            elif direction == 'down':
                xpix = self._data_array['i'][mask] + d
                self._data_array['i'][mask] = xpix % self.row
            i, j = self._data_array['i'][mask], self._data_array['j'][mask]
            xpix, ypix = self._ij_to_xypix(i, j)
            self._data_array['Xpix'][mask] = xpix
            self._data_array['Ypix'][mask] = ypix
            self._display_data()

    def _display_data(self):

        array = self._axes_image_threshold.get_array()
        array[:, :, :] = 0
        channel = self.R
        dx = int(self.row * self._percentage)
        dy = int(self.col * self._percentage)

        # display not displayed
        for ix in np.ndindex(self._data_array.shape):
            if self._data_array['type'][ix] == 'data':
                channel = self.R
            elif (self._data_array['type'][ix] == 'xmin') \
                 | (self._data_array['type'][ix] == 'xmax'):
                channel = self.B
            elif (self._data_array['type'][ix] == 'ymin') \
                 | (self._data_array['type'][ix] == 'ymax'):
                channel = self.G
            x = self._data_array['i'][ix]
            y = self._data_array['j'][ix]

            if self._data_array['selected'][ix]:
                xmask = slice(x - dx*2, x + dx*2 + 1)
                ymask = slice(y - dy*2, y + dy*2 + 1)
            else:
                xmask = slice(x - dx, x + dx + 1)
                ymask = slice(y - dy, y + dy + 1)

            array[xmask, y, self.alpha] = 1
            array[xmask, y, channel] = 1
            array[x, ymask, self.alpha] = 1
            array[x, ymask, channel] = 1

        mask = self._data_array['type'] == 'data'
        self._tkvar_npoints.set(mask.sum())
        self._axes_image_threshold.set_array(array)

        self._refresh()

    def _xlog_scale(self):

        if self._tkvar_log_xscale.get():
            if (self._tkvar_xmin.get() <= 0.0) or (self._tkvar_xmax.get() <= 0.0):
                self._tkvar_log_xscale.set(False)
                messagebox.showwarning("Warning", "X limits must be greater than 0 in log scales.")
            else:
                self._measure()
        else:
            self._measure()

    def _ylog_scale(self):

        if self._tkvar_log_yscale.get():
            if (self._tkvar_ymin.get() <= 0.0) or (self._tkvar_ymax.get() <= 0.0):
                self._tkvar_log_yscale.set(False)
                messagebox.showwarning("Warning", "Y limits must be greater than 0 in log scales.")
            else:
                self._measure()
        else:
            self._measure()

    def _xy_pix_limits(self):

        mask_xmin = self._data_array['type'] == 'xmin'
        mask_xmax = self._data_array['type'] == 'xmax'
        mask_ymin = self._data_array['type'] == 'ymin'
        mask_ymax = self._data_array['type'] == 'ymax'

        if (mask_xmin.sum() == 1.0) and (mask_xmax.sum() == 1.0) and (mask_ymin.sum() == 1.0) and (
                mask_ymax.sum() == 1.0):
            xpix_min = self._data_array['Xpix'][mask_xmin][0]
            xpix_max = self._data_array['Xpix'][mask_xmax][0]

            ypix_min = self._data_array['Ypix'][mask_ymin][0]
            ypix_max = self._data_array['Ypix'][mask_ymax][0]

        else:
            raise ValueError('X limits and Y limits must be set.')

        return xpix_min, xpix_max, ypix_min, ypix_max

    def _xy_values_limits(self):
        r"""if an error happens a tk.TclError will be raised."""
        try:
            xvalue_min = self._tkvar_xmin.get()
            xvalue_max = self._tkvar_xmax.get()
            yvalue_min = self._tkvar_ymin.get()
            yvalue_max = self._tkvar_ymax.get()
        except tk.TclError as tclerror:
            raise ValueError("Xmin, Xmax, Ymin and Ymax must be floats.") from tclerror

        return xvalue_min, xvalue_max, yvalue_min, yvalue_max

    def _xy_test_values(self):
        r"""if an error happens a tk.TclError will be raised."""
        try:
            xtext_value = self._tkvar_xtest.get()
            ytext_value = self._tkvar_ytest.get()
        except tk.TclError as tclerror:
            raise ValueError("x and y must be floats.") from tclerror

        return xtext_value, ytext_value

    def _measure(self):
        r"""
        x and y positions are indicated as matrix indexes: 
        row index x is for y axis and column index y is for x axis
        """
        flag = False
        try:
            xpix_min, xpix_max, ypix_min, ypix_max = self._xy_pix_limits()
            xvalue_min, xvalue_max, yvalue_min, yvalue_max = self._xy_values_limits()

            xpix = self._data_array['Xpix']
            ypix = self._data_array['Ypix']

            which = 'linear'
            unit = f'{self._xunit_entry.get()}/pixel'
            if self._tkvar_log_xscale.get():
                which = 'log'
                unit = f'{self._xunit_entry.get():s}/pixel (log scale)'
            trans = Transform(values_min=xvalue_min,
                              values_max=xvalue_max,
                              pix_min=xpix_min,
                              pix_max=xpix_max,
                              which=which)
            self._data_array['x'] = trans.backward(xpix)
            msg = f'{trans.backward_scale}' + ' ' + unit
            self._ax.set_xlabel(msg)

            which = 'linear'
            unit = f'{self._yunit_entry.get()}/pixel'
            if self._tkvar_log_yscale.get():
                which = 'log'
                unit = f'{self._yunit_entry.get()}/pixel (log scale)'
            trans = Transform(values_min=yvalue_min,
                              values_max=yvalue_max,
                              pix_min=ypix_min,
                              pix_max=ypix_max,
                              which=which)
            self._data_array['y'] = trans.backward(ypix)
            msg = f'{trans.backward_scale}' + ' ' + unit
            self._ax.set_ylabel(msg)

            flag = True
            self._refresh()

        except ValueError as e:
            messagebox.showwarning('Warning', e)

        return flag

    def _plot_test_data(self):
        r"""
        x and y positions are indicated as matrix indexes: 
        row index x is for y axis and column index y is for x axis
        """
        flag = False

        try:
            xpix_min, xpix_max, ypix_min, ypix_max = self._xy_pix_limits()
            xvalue_min, xvalue_max, yvalue_min, yvalue_max = self._xy_values_limits()
            xtest_value, ytest_value = self._xy_test_values()

            which = 'linear'
            if self._tkvar_log_xscale.get():
                which = 'log'
            trans = Transform(values_min=xvalue_min,
                              values_max=xvalue_max,
                              pix_min=xpix_min,
                              pix_max=xpix_max,
                              which=which)
            xpix = trans.forward(xtest_value)

            which = 'linear'
            if self._tkvar_log_yscale.get():
                which = 'log'
            trans = Transform(values_min=yvalue_min,
                              values_max=yvalue_max,
                              pix_min=ypix_min,
                              pix_max=ypix_max,
                              which=which)
            ypix = trans.forward(ytest_value)
            flag = True
            i,j = self._xypix_to_ij(xpix, ypix)
            self._add_data(i, j)
            self._refresh()

        except ValueError as e:
            messagebox.showwarning('Warning', e)

        return flag

    def _save(self):
        """Save data."""
        _filepath = filedialog.asksaveasfilename(title='Open Plot',
                                                 defaultextension='.txt',
                                                 filetypes=[('txt', '.txt'),
                                                            ('all files', '.*')],
                                                 initialdir=self._data_folder,
                                                 parent=self)

        if len(_filepath) > 0:
            filepath = pathlib.Path(_filepath).absolute()
            info = version.__package_name__ + "-" + version.__version__
            
            names = list(self._data_array.dtype.names)
            names[5] = names[5] + f' /{self._xunit_entry.get()}'
            names[6] = names[6] + f' /{self._yunit_entry.get()}'
            
            col_names = '\t'.join(names)
            header = '\n'.join((info, col_names))
            
            mask = self._data_array['type'] == 'data'
            mask_sort = np.argsort(self._data_array['x'][mask])
            sorted_data = self._data_array[mask][mask_sort].copy()
            self._data_array[mask][mask_sort] = sorted_data
            
            np.savetxt(filepath, X=self._data_array,
                       header=header,
                       fmt=('%s', '%d', '%d', '%d', '%d', '%.6e', '%.6e', '%d'),
                       delimiter='\t',
                       comments='#')
            self._data_folder = filepath.parent
            self._data_name = filepath.name

    def _refresh(self):
        """Refresh plot."""
        self._canvas.draw()
        self._canvas_widget.focus_set()

    def _test_linear(self):
        """Test linear scale."""
        self._filepath = test_linear()
        self._load_image()

    def _test_ylog(self):
        """Test semi-log scale."""
        self._filepath = test_ylog()
        self._load_image()

    def _test_xlog(self):
        """Test semi-log scale."""
        self._filepath = test_xlog()
        self._load_image()

    def _test_loglog(self):
        """Test semi-log scale."""
        self._filepath = test_loglog()
        self._load_image()

    def _online_documentation(self):
        """Display online documentation."""
        b = webbrowser.get()
        b.open(self.url)

    def _sources(self):
        """Display sources."""
        b = webbrowser.get()
        b.open(self.url_download)

    def stop(self):
        r"""
        Stop the main tk loop.
        """
        if messagebox.askyesno("Exit", "Do you want to quit the application?"):
            profile_type = 'folders'
            folders_profile_name = self._profiles_ini.defaults()[profile_type].upper()
            self._folders_profile.set(section=folders_profile_name,
                                      option='image folder',
                                      value=str(self._image_folder))
            self._folders_profile.set(section=folders_profile_name,
                                      option='image name',
                                      value=self._image_name)
            self._folders_profile.set(section=folders_profile_name,
                                      option='data folder',
                                      value=str(self._data_folder))
            self._folders_profile.set(section=folders_profile_name,
                                      option='data name',
                                      value=self._data_name)
            save_cfg(CFG_FOLDER, 'folders', self._folders_profile)
            self.master.quit()
            self.master.destroy()

    def run(self):
        r"""
        Start the application.
        """
        self.mainloop()
