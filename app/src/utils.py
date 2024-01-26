import numpy as np
import pandas as pd
import cv2
import io
import matplotlib.pyplot as plt


def resize_image_slices(image_2d: pd.DataFrame, target_width: int = 150) -> np.ndarray:
    """
    Resize the width of the image to the target width.

    :param image_2d: The 2D image to resize.
    :param target_width: The target width to resize the image to.
    :return: The resized image.
    """

    height = int(image_2d.shape[0])
    new_size = (target_width, height)

    if isinstance(image_2d, pd.DataFrame):
        resized_image = cv2.resize(
            image_2d.to_numpy(), new_size, interpolation=cv2.INTER_AREA
        )
    elif isinstance(image_2d, np.ndarray):
        resized_image = cv2.resize(image_2d, new_size, interpolation=cv2.INTER_AREA)
    else:
        raise TypeError("The image must be a pandas DataFrame or a numpy array.")

    return resized_image


def convert_to_numpy(image_bytes: io.BytesIO) -> np.ndarray:
    """
    Convert the image to a numpy array.

    :param image_2d: The 2D image to convert.
    :return: The converted image.
    """
    # convert to pandas
    image_2d = pd.read_csv(image_bytes)

    # remove the depth column and NaN row
    image = image_2d.iloc[:-1, 1:]

    return image.to_numpy()


def plot_image(image: np.ndarray, buffer: io.BytesIO):
    """
    Plot the image and save to a buffer.

    :param image: The image to plot.
    :param buffer: The buffer to save the image to.
    """
    fig, ax = plt.subplots()
    ax.imshow(image, aspect="auto", cmap="inferno")
    plt.savefig(buffer, format="png")  # Save the figure to the buffer
    plt.close(fig)
