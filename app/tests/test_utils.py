import unittest
import numpy as np
import pandas as pd

from src.utils import resize_image_slices


class TestResizeImageSlices(unittest.TestCase):
    def setUp(self):
        # Create a sample 3D image array for testing
        pixels = np.random.randint(0, 256, (5460, 200), dtype=np.uint8)
        depths = np.arange(9000.1, 9546.0 + 0.1, 0.1)

        df = pd.DataFrame(pixels, columns=[f'col{i}' for i in range(1, 201)])
        df.insert(0, 'depth', depths)
        df.loc[5460] = np.nan
        self.sample_image = df.copy()

    def test_resize_image_slices(self):
        # Resize the sample image
        resized_image = resize_image_slices(self.sample_image, 150)

        # Check if the number of slices remain the same
        self.assertEqual(resized_image.shape[0], self.sample_image.shape[0])

        # Check if the width of each slice is resized to 150
        self.assertEqual(resized_image.shape[1], 150)
