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


def resize_image_keep_depth(image: pd.DataFrame, new_width: int = 150) -> pd.DataFrame:
    if isinstance(image, io.BytesIO):
        image = pd.read_csv(image)

    # Separate the 'depth' column
    depth_data = image['depth']
    pixel_data = image.drop('depth', axis=1)

    print(f'Original image shape: {pixel_data.shape}')
    resized_img = resize_image_slices(pixel_data, new_width)
    print(f'Resized image shape: {resized_img.shape}')

    # Convert the resized array back to DataFrame
    resized_pixels_df = pd.DataFrame(resized_img, columns=[f'col{i}' for i in range(resized_img.shape[1])])

    # Concatenate the 'depth' column back with the resized pixel data
    # Ensure the depth_data has the same number of rows as the resized_pixels_df after resizing
    resized_pixels_df.insert(0, 'depth', depth_data.values[:resized_pixels_df.shape[0]])

    return resized_pixels_df


def get_slice(df: pd.DataFrame, start: float, end: float) -> pd.DataFrame:
    """
    Get a slice of the image.

    :param df: The image to slice.
    :param start: The start depth.
    :param end: The end depth.
    :return: The sliced image.
    """
    mask = (df['depth'] >= start) & (df['depth'] <= end)
    return df[mask]


def convert_to_array(df: pd.DataFrame) -> np.ndarray:
    """
    Convert the image dataframe to a numpy array.

    :param df: The image dataframe to convert.
    """
    if not isinstance(df, pd.DataFrame):
        image = pd.read_csv(df)

    # remove the depth column
    image = df.iloc[:, 1:]

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
