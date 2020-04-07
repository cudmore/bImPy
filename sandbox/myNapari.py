from skimage import data
import napari

#path = '/Volumes/fourt/2020/resize/cell1.tif'

with napari.gui_qt():
    #viewer = napari.view_image(data.astronaut(), rgb=True)
    #viewer = napari.view_image(path=path)
    viewer = napari.Viewer()
