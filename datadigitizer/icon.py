r"""
Create icon for the app.

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
import os
import numpy as np
import matplotlib.pyplot as plt


x = np.arange(0, 10, 1)
y = x+1

icon_size = 128

dpi = icon_size/2
figsize_pix = np.asarray((icon_size, icon_size))

figsize = (figsize_pix/dpi).tolist()

fig = plt.figure(figsize=figsize, dpi=dpi)
ax = fig.add_subplot(111)
ax.plot(x, y, color='k', marker='o', ms=10, ls="")
ax.set_xlabel('X LABEL')

folder = os.path.dirname(os.path.abspath(__file__))
fig.savefig(folder + '/icon.png', dpi=dpi, facecolor='grey')
