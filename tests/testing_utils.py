import numpy as np
import os
import sys
import inspect
import logging
import pytest

from manim import logger
from manim import config


class SceneTester:
    """Class used to test the animations.

    Parameters
    ----------
    scene_object : :class:`~.Scene`
        The scene to be tested
    config_scene : :class:`dict`
        The configuration of the scene
    module_tested : :class:`str`
        The name of the module tested. i.e if we are testing functions of creation.py, the module will be "creation"

    Attributes
    -----------
    path_tests_medias_cache : : class:`str`
        Path to 'media' folder generated by manim. This folder contains cached data used by some tests.
    path_tests_data : : class:`str`
        Path to the data used for the tests (i.e the pre-rendered frames).
    scene : :class:`Scene`
        The scene tested
    """

    def __init__(self, scene_object, module_tested, caching_needed=False):
        # Disable the the logs, (--quiet is broken) TODO
        logging.disable(logging.CRITICAL)
        self.path_tests_medias_cache = os.path.join('tests_cache', module_tested)
        self.path_tests_data = os.path.join('tests_data', module_tested)

        if caching_needed:
            config['text_dir'] = os.path.join(
                self.path_tests_medias_cache, scene_object.__name__, 'Text')
            config['tex_dir'] = os.path.join(
                self.path_tests_medias_cache, scene_object.__name__, 'Tex')

        config['pixel_height'] = 480
        config['pixel_width'] = 854
        config['frame_rate'] = 15

        # By invoking this, the scene is rendered.
        self.scene = scene_object()

    def load_data(self):
        """Load the np.array of the last frame of a pre-rendered scene. If not found, throw FileNotFoundError.

        Returns
        -------
        :class:`numpy.array`
            The pre-rendered frame.
        """
        frame_data_path = os.path.join(
            self.path_tests_data, "{}.npy".format(str(self.scene)))
        return np.load(frame_data_path)


    def test(self):
        """Compare pre-rendered frame to the frame rendered during the test."""
        frame_data = self.scene.get_frame()
        expected_frame_data = self.load_data()

        assert frame_data.shape == expected_frame_data.shape, \
            "The frames have different shape:" \
            + f"\nexpected_frame_data.shape = {expected_frame_data.shape}" \
            + f"\nframe_data.shape = {frame_data.shape}"

        test_result = np.array_equal(frame_data, expected_frame_data)
        if not test_result:
            incorrect_indices = np.argwhere(frame_data != expected_frame_data)
            first_incorrect_index = incorrect_indices[0][:2]
            first_incorrect_point = frame_data[tuple(first_incorrect_index)]
            expected_point = expected_frame_data[tuple(first_incorrect_index)]
            assert test_result, \
                f"The frames don't match. {str(self.scene).replace('Test', '')} has been modified." \
                + "\nPlease ignore if it was intended." \
                + f"\nFirst unmatched index is at {first_incorrect_index}: {first_incorrect_point} != {expected_point}"


def get_scenes_to_test(module_name):
    """Get all Test classes of the module from which it is called. Used to fetch all the SceneTest of the module.

    Parameters
    ----------
    module_name : :class:`str`
        The name of the module tested.

    Returns
    -------
    :class:`list`
        The list of all the classes of the module.
    """
    return inspect.getmembers(sys.modules[module_name], lambda m: inspect.isclass(m) and m.__module__ == module_name)


def utils_test_scenes(scenes_to_test, module_name, caching_needed=False):
    for _, scene_tested in scenes_to_test:
        SceneTester(scene_tested, module_name,
                    caching_needed=caching_needed).test()


def set_test_scene(scene_object, module_name):
    """Function used to set up the test data for a new feature. This will basically set up a pre-rendered frame for a scene. This is meant to be used only
    when setting up tests. Please refer to the wiki.

    Parameters
    ----------
    scene_object : :class:`~.Scene`
        The scene with wich we want to set up a new test.
    module_name : :class:`str`
        The name of the module in which the functionnality tested is contained. For example, 'Write' is contained in the module 'creation'. This will be used in the folder architecture
        of '/tests_data'.

    Examples
    --------
    Normal usage::
        set_test_scene(DotTest, "geometry")
    """

    CONFIG_TEST = {
        'camera_config': {
            'frame_rate': 15,
            'pixel_height': 480,
            'pixel_width': 854
        },
        'end_at_animation_number': None,
        'file_writer_config': {
            'file_name': None,
            'input_file_path': 'test.py',
            'movie_file_extension': '.mp4',
            'png_mode': 'RGB',
            'save_as_gif': False,
            'save_last_frame': False,
            'save_pngs': False,
            'write_to_movie': False
        },
        'leave_progress_bars': False,
        'skip_animations': True,
        'start_at_animation_number': None
    }

    scene = scene_object(**CONFIG_TEST)
    data = scene.get_frame()
    path = os.path.join("manim", "tests", "tests_data",
                        "{}".format(module_name))
    if not os.path.isdir(path):
        os.makedirs(path)
    np.save(os.path.join(path, str(scene)), data)
    logger.info('Test data saved in ' + path + '\n')
