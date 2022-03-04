from functools import reduce
import matplotlib.pyplot as plt
import numpy as np

vectors = np.load('vectors/vectors.npy')
step = 3

u, v = vectors[0][:, :, 0], vectors[0][:, :, 1]

conv = reduce(np.add, np.gradient(u)) + reduce(np.add, np.gradient(v))
conv[conv>=0] = np.nan

absmin = np.unravel_index(np.nanargmin(conv), conv.shape)
print(absmin, conv[absmin])

plt.imshow(conv)
plt.show()