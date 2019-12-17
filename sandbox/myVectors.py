import napari
from skimage import data
import numpy as np

# create vector data
n = 250
vectors = np.zeros((n, 2, 2), dtype=np.float32)
phi_space = np.linspace(0, 4 * np.pi, n)
radius_space = np.linspace(0, 100, n)
# assign x-y projection
vectors[:, 1, 0] = radius_space * np.cos(phi_space)
vectors[:, 1, 1] = radius_space * np.sin(phi_space)
# assign x-y position
vectors[:, 0] = vectors[:, 1] + 256



with napari.gui_qt():
    # add the image
    viewer = napari.view_image(data.camera(), name='photographer')
    # add the vectors
    viewer.add_vectors(vectors, edge_width=3)

    viewer.add_points(myPoints, size=30, face_colors=myPointColors)