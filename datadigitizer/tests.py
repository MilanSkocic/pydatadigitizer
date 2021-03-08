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