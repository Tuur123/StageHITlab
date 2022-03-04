import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation

vectors = np.load('vectors/vectors.npy')
X, Y = vectors.shape[1:3]

step = 10


fig, ax = plt.subplots(1,1, figsize=(12, 12))
Q = ax.quiver(range(vectors[0].shape[1]), range(vectors[0].shape[0]), vectors[0][:, :, 0], vectors[0][:, :, 1])

ax.set_xlim(0, X)
ax.set_ylim(0, Y)

def update_quiver(num, Q, X, Y):    
    
    U = vectors[num][:, :, 0]
    V = vectors[num][:, :, 1]

    Q.set_UVC(U, V)
    
    return Q

# you need to set blit=False, or the first set of arrows never gets
# cleared on subsequent frames
anim = animation.FuncAnimation(fig, update_quiver, fargs= (Q, X, Y), interval=35, blit=False, frames=len(vectors) - 1)

# writervideo = animation.FFMpegWriter(fps=28) 
# anim.save('vectors.mp4', writer=writervideo)

plt.show()