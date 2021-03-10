import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import os
import sys
import webbrowser
import pathlib
from typing import Union, Iterable
import numpy as np
from matplotlib import image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from . import version
from .settings import read_cfg, read_profiles, save_cfg
from .settings import CFG_FOLDER, DEFAULT_PROFILE_VALUES


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

    def _prepare_x(self, x: Iterable):
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
        """
        _x = self._prepare_x(x)
        return (_x - self._x1_min) * self._dx2 / self._dx1 + self._x2_min

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
        """
        _value = (x - self._x2_min) * self._dx1 / self._dx2 + self._x1_min
        if self._which == 'log':
            return 10 ** _value
        else:
            return _value

    @property
    def forward_scale(self):
        r"""Return the scale for transforming values into pixels."""
        return self._dx2 / self._dx1

    @property
    def backward_scale(self):
        r"""Return the scale for transforming pixels into values."""
        return self._dx1 / self._dx2


class App(ttk.Frame):
    r"""Class for main graphical interface. See __init__.__doc__."""

    def __init__(self, master=None):
        r"""HOW TO USE:

        The cursor is used to point a specific position in the graph
        whereas all operations are done through keyboard combinations.

        Legend:

        - Red crosses are data points
        - Blue crosses are Xmin and Xmax
        - Green crosses are Ymin and Ymax

        Commands:

        * <Ctrl-o> for loading image.
        * <Ctrl-a> add data point.

        * <Ctrl-g> set Xmin from last data point.
        * <Ctrl-h> set Xmax from last data point.

        * <Ctrl-j> set Ymin from last data point.
        * <Ctrl-k> set Ymax from last data point.

        * <Ctrl-l> set all limits from last 4 points.
        * <Ctrl-n> remove all limits.

        * <Ctrl-z> remove last data point.
        * <Ctrl-d> remove all data points.

        * <Ctrl-m> compute the data points.
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
        # self.master.title('Data Digitizer - {0:s} - Running in Python {1:s}'.format(version.__version__, sys.version))
        self.master.title('Data Digitizer')
        folder = pathlib.Path(__file__).parent
        self.master.iconphoto(True, tk.PhotoImage(file=folder / 'icon.png'))
        self.master.protocol("WM_DELETE_WINDOW", self._ask_quit)
        self.url = 'http://www.github.com/MilanSkocic/datadigitizer'

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
        self.master.bind('<Control-d>', self._cb_delete)
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

        # get screen width and height
        ws = self.master.winfo_screenwidth()
        hs = self.master.winfo_screenheight()
        # master.geometry(("%dx%d")%(ws,hs))
        width = int(0.75 * ws)
        height = int(0.75 * hs)
        x = int((ws / 2) - (width / 2))
        y = int((hs / 2) - (height / 2) - 25)
        self.master.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        # Grid config
        tk.Grid.columnconfigure(self, 0, weight=1)
        tk.Grid.columnconfigure(self, 1, weight=3)
        tk.Grid.rowconfigure(self, 0, weight=1)

        # flags and variables
        profile_type = 'folders'
        folders_profile_name = self._profiles_ini.defaults()[profile_type].upper()
        self._image_folder = self._folders_profile.get_typed_option(section=folders_profile_name,
                                                                    option='image folder')
        self._axes_image = None
        self._axes_image_threshold = None
        self._data_indexes = []
        self._percentage = 0.01
        self.R, self.G, self.B, self.alpha = 0, 1, 2, 3
        self.dtypes = [('type', (np.str_, 32)),
                       ('Xpix', np.int32),
                       ('Ypix', np.int32),
                       ('x', np.float64),
                       ('y', np.float64)]
        self._line = np.zeros(shape=(1,), dtype=self.dtypes)
        self._data_array = np.zeros(shape=(0,), dtype=self.dtypes)
        self._triggered_event = None
        self._scale_pixel_to_value = 1.0
        self._scale_value_to_pixel = 1 / self._scale_pixel_to_value
        self._pixel_offset = 0.0
        self._value_offset = 0.0

        # Menu
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        # File Menu
        self.file_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.file_menu, label='File')
        self.file_menu.add_command(label='Load Image <Ctrl-o>', command=self._trigger_load_event)
        self.file_menu.add_command(label='Save Data <Ctrl-s>', command=self._trigger_save_event)
        self.file_menu.add_command(label='Clear All <Ctrl-w>', command=self._trigger_clearall_event)
        self.file_menu.add_command(label='Quit <Ctrl-q>', command=self._ask_quit)

        # Data Menu
        self.data_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.data_menu, label='Data')
        self.data_menu.add_command(label='Add Data Point <Ctrl-a>', command=self._trigger_add_event)
        self.data_menu.add_command(label='Remove Last Data Point <Ctrl-z>', command=self._trigger_undo_event)
        self.data_menu.add_command(label='Remove All Data Points <Ctrl-d>', command=self._trigger_delete_all_event)
        self.data_menu.add_command(label='Set Xmin from last point <Ctrl-g>', command=self._trigger_xmin_event)
        self.data_menu.add_command(label='Set Xmax from last point <Ctrl-h>', command=self._trigger_xmax_event)
        self.data_menu.add_command(label='Set Ymin from last point <Ctrl-j>', command=self._trigger_ymin_event)
        self.data_menu.add_command(label='Set Ymax from last point <Ctrl-k>', command=self._trigger_ymax_event)
        self.data_menu.add_command(label='Set all limits from 4 last points <Ctrl-l>',
                                   command=self._trigger_all_limits_event)
        self.data_menu.add_command(label='Remove all limits <Ctrl-n>',
                                   command=self._trigger_delete_all_limits_event)
        self.data_menu.add_command(label='Compute <Ctrl-m>', command=self._measure)

        # Help Menu
        self.help_menu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.help_menu, label='Help')
        self.help_menu.add_command(label='About', command=self._about)
        self.help_menu.add_command(label='Documentation', command=self._documentation)
        self.help_menu.add_command(label='Sources', command=self._sources)

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
        self._fig = Figure()
        self._ax = self._fig.add_subplot(111)
        self._ax.set_axis_off()
        self._canvas = FigureCanvasTkAgg(self._fig, master=self.right_frame)
        self._canvas_widget = self._canvas.get_tk_widget()
        self._canvas_widget.grid(row=0, column=0, sticky='nswe')
        self._toolbar = NavigationToolbar2Tk(self._canvas, self.master)
        self._toolbar.update()
        # self._canvas.mpl_connect("button_press_event", self._cb_button_press)
        self._canvas.mpl_connect("key_press_event", self._cb_key_press)
        self._canvas.mpl_connect("button_press_event", self._cb_button_press)

        # Help Label
        row = 0
        msg = self.__init__.__doc__.split('Parameters')[0]

        style = ttk.Style()
        # style.theme_use('vista')

        style.configure('help.TLabel')

        style.configure('Xlimits.TEntry')
        style.map('Xlimits.TEntry',
                  foreground=[('focus', 'blue')])

        style.configure('Ylimits.TEntry')
        style.map('Ylimits.TEntry', foreground=[('focus', 'green')])

        style.configure('TestData.TEntry')
        style.map('TestData.TEntry', foreground=[('focus', 'red')])

        self._help_label = ttk.Label(self.left_frame, text=msg, style='help.TLabel')
        self._help_label.grid(row=row, column=0, columnspan=2, sticky='nswe')
        self._help_label.focus_set()

        # X Axis
        row = row + 1
        container = self.left_frame
        ttk.Separator(container, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky='nswe')

        row += 1
        ttk.Label(self.left_frame, text='X Axis').grid(row=row, column=0, columnspan=2, sticky='nswe')
        self._tkvar_log_xscale = tk.BooleanVar()
        self._tkvar_log_xscale.set(False)
        self._log_xscale_cb = ttk.Checkbutton(container, variable=self._tkvar_log_xscale, text='log X scale?',
                                              command=self._xlog_scale)
        self._log_xscale_cb.grid(row=row, column=1, sticky='nswe')

        row = row + 1
        ttk.Label(self.left_frame, text='Xmin=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_xmin = tk.DoubleVar()
        self._tkvar_xmin.set(0.0)
        self._xmin_entry = ttk.Entry(container, textvariable=self._tkvar_xmin, style='Xlimits.TEntry')
        self._xmin_entry.grid(row=row, column=1, sticky='nswe')
        self._xmin_entry.bind('<Return>', self._cb_measure)

        row += 1
        ttk.Label(self.left_frame, text='Xmax=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_xmax = tk.DoubleVar()
        self._tkvar_xmax.set(1.0)
        self._xmax_entry = ttk.Entry(container, textvariable=self._tkvar_xmax, style='Xlimits.TEntry')
        self._xmax_entry.grid(row=row, column=1, sticky='nswe')
        self._xmax_entry.bind('<Return>', self._cb_measure)

        # Y Axis
        row += 1
        container = self.left_frame
        ttk.Separator(container, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky='nswe')

        row += 1
        ttk.Label(self.left_frame, text='Y Axis').grid(row=row, column=0, columnspan=2, sticky='nswe')
        self._tkvar_log_yscale = tk.BooleanVar()
        self._tkvar_log_yscale.set(False)
        self._log_yscale_cb = ttk.Checkbutton(container, variable=self._tkvar_log_yscale, text='log Y scale?',
                                              command=self._ylog_scale)
        self._log_yscale_cb.grid(row=row, column=1, sticky='nswe')

        row += 1
        ttk.Label(self.left_frame, text='Ymin=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_ymin = tk.DoubleVar()
        self._tkvar_ymin.set(0.0)
        self._ymin_entry = ttk.Entry(container, textvariable=self._tkvar_ymin, style='Ylimits.TEntry')
        self._ymin_entry.grid(row=row, column=1, sticky='nswe')
        self._ymin_entry.bind('<Return>', self._cb_measure)

        row += 1
        ttk.Label(self.left_frame, text='Ymax=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_ymax = tk.DoubleVar()
        self._tkvar_ymax.set(1.0)
        self._ymax_entry = ttk.Entry(container, textvariable=self._tkvar_ymax, style='Ylimits.TEntry')
        self._ymax_entry.grid(row=row, column=1, sticky='nswe')
        self._ymax_entry.bind('<Return>', self._cb_measure)

        # Data
        row += 1
        container = self.left_frame
        ttk.Separator(container, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky='nswe')

        row += 1
        ttk.Label(self.left_frame, text='N points=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_npoints = tk.IntVar()
        self._tkvar_npoints.set(0)
        ttk.Label(container, textvariable=self._tkvar_npoints).grid(row=row, column=1, sticky='nswe')

        row += 1
        ttk.Separator(container, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky='nswe')

        row += 1
        ttk.Label(container, text='Test values with defined scale:').grid(row=row, column=0,
                                                                          columnspan=2, sticky='nswe')

        row += 1
        ttk.Label(container, text='X=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_xtest = tk.DoubleVar()
        self._tkvar_xtest.set(1)
        self._xtest_entry = ttk.Entry(container, textvariable=self._tkvar_xtest, style='TestData.TEntry')
        self._xtest_entry.grid(row=row, column=1, sticky='nswe')
        self._xtest_entry.bind('<Return>', self._cb_test_data)

        row += 1
        ttk.Label(container, text='Y=').grid(row=row, column=0, sticky='nswe')
        self._tkvar_ytest = tk.DoubleVar()
        self._tkvar_ytest.set(1)
        self._ytest_entry = ttk.Entry(container, textvariable=self._tkvar_ytest, style='TestData.TEntry')
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

    def _cb_open(self, event):
        self._triggered_event = event
        self._load_image()

    def _cb_undo(self, event):
        self._triggered_event = event
        self._undo()

    def _cb_delete(self, event):
        self._triggered_event = event
        self._delete_all()

    def _cb_delete_limits(self, event):
        self._triggered_event = event
        self._delete_limits()

    def _cb_clear(self, event):
        self._triggered_event = event
        self._clear_all()

    def _cb_key_press(self, event):
        self._triggered_event = event
        if event.key == 'ctrl+a':
            if (event.xdata is not None) and (event.ydata is not None) and (self._axes_image is not None):
                y = int(round(event.xdata, 0))
                x = int(round(event.ydata, 0))
                self._add_data(x, y)
        elif event.key == 'ctrl+z':
            self._undo()
        elif event.key == 'right':
            self._shift_data(direction='right')
        elif event.key == 'left':
            self._shift_data(direction='left')
        elif event.key == 'up':
            self._shift_data(direction='up')
        elif event.key == 'down':
            self._shift_data(direction='down')

    def _cb_button_press(self, event):

        if event.button == 1:
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
        data_indexes = np.argwhere(self._data_array['type'] == 'data')
        if data_indexes.size >= 4:
            self._add_limits(which='ymax')
            self._add_limits(which='ymin')
            self._add_limits(which='xmax')
            self._add_limits(which='xmin')
        else:
            messagebox.showinfo("Infos", "You must add at least 4 points before setting all limits at once.")

    def _cb_save(self, event):
        self._triggered_event = event
        if self._measure():
            self._save()

    def _cb_quit(self, event):
        self._triggered_event = event
        self._ask_quit()

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
        self.master.event_generate('<Control-d>')

    def _trigger_delete_all_limits_event(self):
        self.master.event_generate('<Control-n>')

    def _load_image(self):
        self._clear_all()
        _filepath = filedialog.askopenfilename(title='Open Plot',
                                               defaultextension='.png',
                                               filetypes=[('png', '.png'),
                                                          ('jpeg', '.jpeg'),
                                                          ('tif', '.tif'),
                                                          ('all files', '.*')],
                                               initialdir=self._image_folder,
                                               parent=self)

        if len(_filepath):
            filepath = os.path.abspath(_filepath)
            if os.path.isfile(filepath):
                self._image_folder = os.path.dirname(filepath)
                image_array = image.imread(filepath)
                shape = image_array.shape
                dim = len(shape)
                if dim > 1:
                    self._delete_all()
                    self._ax.set_axis_on()
                    row, col = image_array.shape[0:2]
                    image_threshold = np.zeros(shape=(row, col, 4))
                    self._axes_image = self._ax.imshow(image_array, cmap='Greys_r')
                    self._axes_image_threshold = self._ax.imshow(image_threshold)
                    self._ax.relim()
                    self._canvas.draw()
                else:
                    messagebox.showinfo("Infos", f"{filepath} is not a valid image (ndim={dim}).")
                self._image_folder = os.path.dirname(filepath)
            else:
                messagebox.showerror("Error", f"File Error: {filepath}")

    def _add_data(self, x: Union[int, float], y: Union[int, float]):

        self._data_indexes.append((x, y))
        self._line[0] = ('data', x, y, 0, 0)
        self._data_array = np.append(self._data_array, self._line)
        self._display_data()

    def _undo(self):
        mask = self._data_array['type'] == 'data'
        if self._data_array[mask].size:
            indexes = np.argwhere(self._data_array['type'] == 'data')
            self._data_array = np.delete(self._data_array, indexes[-1])
            self._display_data()

    def _add_limits(self, which: str):

        if self._data_array.size:
            data_indexes = np.argwhere(self._data_array['type'] == 'data')
            if data_indexes.size:
                indexes = np.argwhere(self._data_array['type'] == which)
                self._data_array = np.delete(self._data_array, indexes)
                data_indexes = np.argwhere(self._data_array['type'] == 'data')
                self._data_array['type'][data_indexes[-1]] = which
                self._display_data()
            else:
                messagebox.showinfo("Infos", "You must add at least 1 point.")
        else:
            messagebox.showinfo("Infos", "You must add at least 1 point.")

    def _delete_all(self):

        indexes = np.argwhere(self._data_array['type'] == 'data')
        if indexes.size:
            self._data_array = np.delete(self._data_array, indexes)
            self._display_data()

    def _delete_limits(self):

        for which in ['xmin', 'xmax', 'ymin', 'ymax']:
            indexes = np.argwhere(self._data_array['type'] == which)
            if indexes.size:
                self._data_array = np.delete(self._data_array, indexes)
                self._display_data()

    def _clear_all(self):

        self._ax.clear()
        self._axes_image = None
        self._axes_image_threshold = None
        self._line = np.zeros(shape=(1,), dtype=self.dtypes)

        self._data_array = np.zeros(shape=(0,), dtype=self.dtypes)
        self._ax.set_axis_off()

        self._reset_ui()

        self._canvas_widget.focus_set()
        self._canvas.draw()

    def _shift_data(self, direction: str):

        indexes = np.argwhere(self._data_array['type'] == 'data')
        if indexes.size:
            if direction == 'right':
                self._data_array['Ypix'][indexes[-1]] += 1
            elif direction == 'left':
                self._data_array['Ypix'][indexes[-1]] -= 1
            elif direction == 'up':
                self._data_array['Xpix'][indexes[-1]] -= 1
            elif direction == 'down':
                self._data_array['Xpix'][indexes[-1]] += 1
            self._display_data()

    def _display_data(self):

        array = self._axes_image_threshold.get_array()
        array[:, :, :] = 0
        channel = self.R
        for ix in np.ndindex(self._data_array.shape):
            if self._data_array['type'][ix] == 'data':
                channel = self.R
            elif (self._data_array['type'][ix] == 'xmin') | (self._data_array['type'][ix] == 'xmax'):
                channel = self.B
            elif (self._data_array['type'][ix] == 'ymin') | (self._data_array['type'][ix] == 'ymax'):
                channel = self.G
            x = self._data_array['Xpix'][ix]
            y = self._data_array['Ypix'][ix]

            dx = int(array.shape[0] * self._percentage)
            dy = int(array.shape[1] * self._percentage)
            xmask = slice(x - dx, x + dx + 1)
            ymask = slice(y - dy, y + dy + 1)
            array[xmask, y, self.alpha] = 1
            array[xmask, y, channel] = 1
            array[x, ymask, self.alpha] = 1
            array[x, ymask, channel] = 1

        mask = self._data_array['type'] == 'data'
        self._tkvar_npoints.set(mask.sum())

        self._axes_image_threshold.set_array(array)
        self._canvas.draw()
        self._canvas_widget.focus_set()

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
            xpix_min = self._data_array['Ypix'][mask_xmin][0]
            xpix_max = self._data_array['Ypix'][mask_xmax][0]

            ypix_min = self._data_array['Xpix'][mask_ymin][0]
            ypix_max = self._data_array['Xpix'][mask_ymax][0]

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
        except tk.TclError:
            raise ValueError("Xmin, Xmax, Ymin and Ymax must be floats.")

        return xvalue_min, xvalue_max, yvalue_min, yvalue_max

    def _xy_test_values(self):
        r"""if an error happens a tk.TclError will be raised."""
        try:
            xtext_value = self._tkvar_xtest.get()
            ytext_value = self._tkvar_ytest.get()
        except tk.TclError:
            raise ValueError("x and y must be floats.")

        return xtext_value, ytext_value

    def _measure(self):
        r"""
        x and y positions are indicated as matrix indexes: row index x is for y axis and column index y is for x axis
        """
        flag = False
        try:
            xpix_min, xpix_max, ypix_min, ypix_max = self._xy_pix_limits()
            xvalue_min, xvalue_max, yvalue_min, yvalue_max = self._xy_values_limits()

            xpix = self._data_array['Ypix']
            ypix = self._data_array['Xpix']

            which = 'linear'
            unit = 'unit/pixel'
            if self._tkvar_log_xscale.get():
                which = 'log'
                unit = 'unit/pixel (log scale)'
            trans = Transform(values_min=xvalue_min,
                              values_max=xvalue_max,
                              pix_min=xpix_min,
                              pix_max=xpix_max,
                              which=which)
            self._data_array['x'] = trans.backward(xpix)
            msg = f'{trans.backward_scale}' + ' ' + unit
            self._ax.set_xlabel(msg)

            which = 'linear'
            if self._tkvar_log_yscale.get():
                which = 'log'
            trans = Transform(values_min=yvalue_min,
                              values_max=yvalue_max,
                              pix_min=ypix_min,
                              pix_max=ypix_max,
                              which=which)
            self._data_array['y'] = trans.backward(ypix)
            msg = f'{trans.backward_scale}' + ' ' + unit
            self._ax.set_ylabel(msg)

            flag = True
            self._canvas.draw()
            self._canvas_widget.focus_set()

        except ValueError as e:
            messagebox.showwarning('Warning', e)

        return flag

    def _plot_test_data(self):
        r"""
        x and y positions are indicated as matrix indexes: row index x is for y axis and column index y is for x axis
        """
        flag = False

        try:
            xpix_min, xpix_max, ypix_min, ypix_max = self._xy_pix_limits()
            xvalue_min, xvalue_max, yvalue_min, yvalue_max = self._xy_values_limits()
            xtext_value, ytext_value = self._xy_test_values()

            which = 'linear'
            if self._tkvar_log_xscale.get():
                which = 'log'
            trans = Transform(values_min=xvalue_min,
                              values_max=xvalue_max,
                              pix_min=xpix_min,
                              pix_max=xpix_max,
                              which=which)
            y = trans.forward(xtext_value)

            which = 'linear'
            if self._tkvar_log_yscale.get():
                which = 'log'
            trans = Transform(values_min=yvalue_min,
                              values_max=yvalue_max,
                              pix_min=ypix_min,
                              pix_max=ypix_max,
                              which=which)
            x = trans.forward(ytext_value)
            flag = True
            self._add_data(x, y)
            self._canvas.draw()
            self._canvas_widget.focus_set()

        except ValueError as e:
            messagebox.showwarning('Warning', e)

        return flag

    def _ask_quit(self):
        if messagebox.askyesno("Exit", "Do you want to quit the application?"):
            profile_type = 'folders'
            folders_profile_name = self._profiles_ini.defaults()[profile_type].upper()
            self._folders_profile.set(section=folders_profile_name,
                                      option='image folder',
                                      value=self._image_folder)
            save_cfg(CFG_FOLDER, 'folders', self._folders_profile)
            self.master.quit()
            self.master.destroy()

    def _save(self):

        _filepath = filedialog.asksaveasfilename(title='Open Plot',
                                                 defaultextension='.txt',
                                                 filetypes=[('txt', '.txt'),
                                                            ('all files', '.*')],
                                                 initialdir=self._image_folder,
                                                 parent=self)

        if len(_filepath):
            filepath = os.path.abspath(_filepath)
            headers = ['x', 'y']
            mask = self._data_array['type'] == 'data'
            mask_sort = np.argsort(self._data_array['x'][mask])
            np.savetxt(filepath, X=self._data_array[headers][mask][mask_sort],
                       header='\t'.join(headers),
                       delimiter='\t',
                       comments='#')
            self._image_folder = os.path.dirname(filepath)

    def _documentation(self):
        self._sources()

    def _sources(self):
        b = webbrowser.get()
        b.open(self.url)

    def run(self):
        r"""
        Start the application.
        """
        self.mainloop()


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

        for i in kwargs.keys():
            if i not in self._default_options.keys():
                raise tk.TclError('Unknow option --' + i)

        self._default_options.update(kwargs)

        self.pack(expand=True, fill=tk.BOTH)
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
            raise tk.TclError('Bad scroll style \"' + self._default_options['scrolled'] + '\" must be x, y or both')

        self._canvas = tk.Canvas(self, bd=0, relief=tk.FLAT, yscrollcommand=self.yscrollbar.set,
                                 xscrollcommand=self.xscrollbar.set)
        self._canvas.grid(row=0, column=0, sticky='nswe')

        self.yscrollbar.config(command=self._canvas.yview)
        self.xscrollbar.config(command=self._canvas.xview)

        self._canvas.config(scrollregion=self._canvas.bbox(all))

        self._frame = ttk.Frame(self._canvas)
        self.pack(expand=True, fill=tk.BOTH)

        self._canvas_window_id = self._canvas.create_window(0, 0, window=self._frame, anchor='nw')
        self._canvas.itemconfig(self._canvas_window_id, width=self._frame.winfo_reqwidth())
        self._canvas.bind("<Configure>", self._update_canvas_window_size)

    def _update_canvas_window_size(self, event):
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

        Parameters
        ----------
        master: tkinter widget
            Master container.
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
        width = int(0.75*ws)
        height = int(0.1*hs)
        x = int((ws / 2) - (width / 2))
        y = int((hs / 2) - (height / 2) - 25)
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        self.resizable(height=True, width=True)

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

        msg = 'Python : ' + sys.version
        label = ttk.Label(self.frame, text=msg)
        label.configure(anchor='center')
        label.grid(row=1, column=0, sticky='nswe')

        self.initial_focus.focus_set()
        self.wait_window(self)

    def _quit(self):
        self.master.focus_set()
        self.destroy()
