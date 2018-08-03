
import unittest
import numpy as np

from astropy.io import fits as pyfits

from soar_simager.data_reduction.merge import SoiMerger


class TestSoiMerger(unittest.TestCase):

    @staticmethod
    def can_add_gap(ccdsum):

        header = pyfits.Header()
        header.set('CCDSUM', ccdsum)
        binning = header['CCDSUM']
        binning = int(binning.split()[0])

        naxis1 = 4096 / binning
        naxis2 = 4096 / binning
        pixel_scale = 0.0767
        gap_size = 7.8

        data = np.arange(naxis1)
        data = data[np.newaxis, :]
        data = np.repeat(data, naxis2, axis=0)

        soi_merger = SoiMerger()
        output_data, output_header = soi_merger.add_gap(data, header)

        gap_pixel = int(round(gap_size / pixel_scale / binning))

        np.testing.assert_equal(gap_pixel, int(102 / binning))
        np.testing.assert_equal(output_data.shape[0], data.shape[0])
        np.testing.assert_equal(output_data.shape[1], data.shape[1] + gap_pixel)

    def test_can_add_gap_1x1_binning(self):

        self.can_add_gap('1 1')

    def test_can_add_gap_2x2_binning(self):

        self.can_add_gap('2 2')

    def test_can_add_gap_4x4_binning(self):

        self.can_add_gap('4 4')


if __name__ == '__main__':
    unittest.main()