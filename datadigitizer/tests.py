r"""
Tests module.

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
import pathlib
import numpy as np
import matplotlib.pyplot as plt

x = np.arange(0, 10, 1)


fig = plt.figure()
ax = fig.add_subplot(111)


y = 1*x+1
ax.plot(x, y, 'k+')

m = np.vstack((x, y)).transpose()
np.savetxt('./linear.txt', X=m, header='x\ty', delimiter='\t')
fig.savefig('linear.png', dpi=100, format='png')



ax.clear()
y = 10**x
ax.plot(x, y, 'k+')
ax.set_yscale('log')
m = np.vstack((x, y)).transpose()
np.savetxt('./log.txt', X=m, header='x\ty', delimiter='\t')
fig.savefig('log.png', dpi=100, format='png')


ax.clear()
y = 10**x
ax.plot(y, y, 'k+')
ax.loglog()
m = np.vstack((x, y)).transpose()
np.savetxt('./loglog.txt', X=m, header='x\ty', delimiter='\t')
fig.savefig('loglog.png', dpi=100, format='png')