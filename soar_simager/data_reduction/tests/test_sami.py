
import os

from unittest import TestCase, main
from soar_simager.data_reduction import sami


class TestCreateRedFolder(TestCase):

    def test_can_create_folder(self):

        raw_path = os.getcwd()
        red_fname = './RED'
        red_path = os.path.join(raw_path, red_fname)
        self.assertFalse(os.path.exists(red_path))

        sami.create_reduced_folder(raw_path, red_fname)
        self.assertTrue(os.path.exists(os.path.join(red_path)))

        os.remove(red_path)

    def test_skip_existing_folder(self):

        raw_path = os.getcwd()
        red_fname = './RED'
        red_path = os.path.join(raw_path, red_fname)
        self.assertTrue(os.path.exists(red_path))

        sami.create_reduced_folder(raw_path, red_fname)
        self.assertTrue(os.path.exists(os.path.join(red_path)))

        os.remove(red_path)


if __name__ == '__main__':
    main()