
import numpy as _np
import pandas as _pd
import os

from unittest import main, TestCase
from soar_sami.data_reduction import reduce


class TestCreateRedFolder(TestCase):

    def test_can_create_folder(self):

        red_path = './RED'
        cwd = os.getcwd()

        self.assertFalse(os.path.exists(os.path.join(cwd, red_path)))

        reduce.create_reduced_folder(cwd, red_path)

        self.assertTrue(os.path.exists(os.path.join(cwd, red_path)))

        os.remove(os.path.join(cwd, red_path))


if __name__ == '__main__':
    main()