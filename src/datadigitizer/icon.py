r"""
Create icon for the app.
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
