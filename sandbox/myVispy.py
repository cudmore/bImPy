import numpy as np
from vispy import plot as vp

fig = vp.Fig(size=(600, 500), show=False)

ax1 = fig[0, 0]
ax2 = fig[1, 0]

x = np.linspace(0, 10, 1000)
y = np.zeros(1000)
y[1:500] = 1
y[500:-1] = -1
line = ax1.plot((x, y), width=3, color='k',
                      title='Square Wave Fourier Expansion', xlabel='x',
                      ylabel='4/π Σ[ 1/n sin(nπx/L) | n=1,3,5,...]')

line.set_data((x,y))

if __name__ == '__main__':
    fig.show(run=True)
