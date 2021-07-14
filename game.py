"""Game components."""
import logging
import os
from typing import Iterable, Iterator, List, Union

import blessed
import numpy as np
import pytweening as pt
from blessed.keyboard import Keystroke

from core.render import Render

if "logs" not in os.listdir():
    os.mkdir("logs")
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)  # or whatever
handler = logging.FileHandler("logs/debug.log", "w", "utf-8")  # or whatever
handler.setFormatter(logging.Formatter("%(name)s %(message)s"))  # or whatever
root_logger.addHandler(handler)
logging.info("=" * 15)

NEXT_SCENE = 1
RESET = 2
QUIT = 3

term = blessed.Terminal()

render = Render()


class Scene:
    """This should be subclassed to create each new level.

    The subclass should implement the functions `rest` and `next_frame`
    """

    def __init__(self, col: str = "black", bg_col: str = "peachpuff2"):
        self.height = term.height
        self.width = term.width
        self.current_frame = ""
        self.col = col
        self.bg_col = bg_col

    def reset(self) -> None:
        """Reset the current scene/level to its initial state."""

    def next_frame(self, val: Keystroke) -> Union[str, int]:
        """Draw next frame in the scene."""


class Game:
    """Main game class. Should be initiated with a list of scenes."""

    def __init__(self, scenes: Iterable[Scene]) -> None:
        self.scenes: Iterator = iter(scenes)
        self.current_scene: Scene = next(self.scenes)

    def run(self) -> None:
        """Run the main game loop."""
        with term.cbreak():
            val = Keystroke()
            while (val.lower() != "q") or (val.lower != "x"):
                # user input
                try:
                    command = self.current_scene.next_frame(val)
                except AttributeError as e:
                    logging.info(f"game ended with {e}")
                    print("Game ended.")
                    break
                # get all the frames and print
                print(render.screen())

                if command == NEXT_SCENE:
                    self.current_scene = next(self.scenes, None)
                    continue
                elif command == RESET:
                    self.current_scene.reset()
                    val = Keystroke()
                    continue
                elif command == QUIT:
                    break
                val = term.inkey(timeout=0.05)  # 20 fps


class Camera:
    """Main camera class. Can have multiple cameras in multiplayer."""

    def __init__(
        self,
        game_map: np.ndarray,
        cam_x: int = 0,
        cam_y: int = 0,
        camera_size: int = 100,
        quickness: float = 0.0,
    ) -> None:
        """Initialize the camera.

        :param cam_x: initial position of camera's x coordinates
        :param cam_y: initial position of camera's y coordinates
        :param camera_size: Pov size
        :param game_map: The whole game map
        :param quickness: how fast camera should transition from one point to another
        """
        self.game_map = game_map
        self.cam_x = cam_x
        self.cam_y = cam_y
        self.camera_size = camera_size
        self.quickness = quickness

    def set_position_styled(self, x: int, y: int) -> List:
        """
        Transition coordinates.

        :param x: x coordinate to move to
        :param y: y coordinate to move to
        :return: list of coordinates of animation
        """
        transition_length = int(1 / 0.1)
        interval = 10
        cx = self.cam_x
        cy = self.cam_y
        diff_x = x - cx
        diff_y = y - cy
        animation_coords = []
        for i in range(transition_length):
            cx = cx + pt.easeInOutSine((1 / interval) * i) * diff_x
            cy = cy + pt.easeInOutSine((1 / interval) * i) * diff_y
            animation_coords.append((cx, cy))
        return animation_coords

    def set_position(self, x: int, y: int) -> np.ndarray:
        """
        Set position function

        :param x: x coordinate to move to
        :param y: y coordinate to move to
        :return: player vision
        """

        def clip(x: int, p: int, u: int) -> int:
            return p if x < p else u if x > u else x

        shape = np.shape(self.game_map)
        y_min = clip(0, y, shape[0] - 1)
        y_max = clip(0, y + self.camera_size, shape[0] - 1)
        x_min = clip(0, y, shape[1] - 1)
        x_max = clip(0, y + self.camera_size, shape[1] - 1)
        return self.game_map[y_min:y_max, x_min:x_max]
