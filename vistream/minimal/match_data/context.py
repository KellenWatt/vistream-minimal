from ..match_data import MatchData, BoundingBox
import math

from wpimath.geometry import Translation3d


class ContextualMatchData(MatchData):
    """Does not actually function by itself. Requires a subclass with the following constants:
        - SIZE - the object size in pixels. Assumes the object can be described by a square
        - REAL_SIZE - the object's size in real life
        - FOV - a tuple of the horizontal and vertical field of view in degrees
    """
    def relative_box(self) -> BoundingBox:
        origin = self.box.center()
        return BoundingBox(self.box.x - origin.x, self.box.y - origin.y, self.box.width, self.box.height)
 
    def normal_position(self) -> tuple[float, float]:
        width = self.box.width
        height = self.box.height
        pos = self.box.center()
        x_norm = pos.x / width
        y_norm = pos.y / height
        x_norm = x_norm * 2 - 1
        y_norm = y_norm * 2 - 1
        return (x_norm, -y_norm)
 
    def yaw(self) -> Optional[float]:
        if self.is_partial():
            return None
        return self.normal_position()[0] * type(self).FOV[0]
 
    def pitch(self) -> Optional[float]:
        if self.is_partial():
            return None
        return self.normal_position[1] * type(self).FOV[1]
 
    def distance(self) -> Optional[float]:
        if self.is_partial():
            return None
 
        ratio = type(self).SIZE / self.box.major_axis
        return ratio
 
    def position(self) -> Optional[Translation3d]:
        if self.is_partial():
            return None
        center = self.relative_box().center()
        x = (center.x / self.box.major_axis) * type(self).REAL_SIZE
        z = (center.y / self.box.major_axis) * type(self).REAL_SIZE

        hyp = self.distance()
        y = math.sqrt(hyp*hyp - z*z)

        return Translation3d(x, y, z)
   

class GamePieceMatchData(ContextualMatchData):
    SIZE = 0 # px @ 1m
    REAL_SIZE = 0.3556 # size in meters
    FOV = (65.368, 36.770)

def _for_game_piece(self) -> GamePieceMatchData:
    self.__class__ = GamePieceMatchData
    return self

MatchData.for_game_piece = _for_game_piece

class AprilTagMatchData(ContextualMatchData):
    SIZE = 0 # px @ 1m
    REAL_SIZE = 0.1651
    FOV = (136.0, 102.0)


def _for_apriltag(self) -> AprilTagMatchData:
    self.__class__ = AprilTagMatchData
    return self

MatchData.for_game_piece = _for_apriltag
