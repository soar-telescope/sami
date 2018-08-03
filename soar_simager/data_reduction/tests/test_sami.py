
import os

from unittest import TestCase, main
from soar_simager.data_reduction import sami


class TestCreateRedFolder(TestCase):

    def test_can_create_folder(self):

        raw_path = os.getcwd()
        red_fname = 'RED'
        red_path = os.path.join(raw_path, red_fname)
        self.assertFalse(os.path.exists(red_path))

        sami.create_reduced_folder(red_path)
        self.assertTrue(os.path.exists(red_path))

        os.rmdir(red_path)

    def test_skip_existing_folder(self):

        raw_path = os.getcwd()
        red_fname = 'RED'
        red_path = os.path.join(raw_path, red_fname)

        os.mkdir(red_path)
        self.assertTrue(os.path.exists(red_path))

        sami.create_reduced_folder(red_path)
        self.assertTrue(os.path.exists(red_path))

        os.rmdir(red_path)


if __name__ == '__main__':
    main()