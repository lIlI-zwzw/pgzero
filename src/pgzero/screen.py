import pygame
import pygame.draw

from . import ptext
from .rect import RECT_CLASSES, ZRect
from . import loaders
from .surface_painter import SurfacePainter

def blit_gradient(start, stop, dest_surface):
    """Blit a gradient into a destination surface.

    The function does not return anything as the gradient is written
    in-place in the destination surface.

    Args:
      start: The starting (top) color as a tuple (red, green, blue).
      stop: The stopping (bottom) color as a tuple (red, green, blue).
      dest_surface: A pygame.Surface to write the gradient into.
    Returns:
      None."""
    surface_compact = pygame.Surface((2, 2))
    pixelarray = pygame.PixelArray(surface_compact)
    pixelarray[0][0] = start
    pixelarray[0][1] = stop
    pixelarray[1][0] = start
    pixelarray[1][1] = stop
    pygame.transform.smoothscale(surface_compact,
                                 pygame.PixelArray(dest_surface).shape,
                                 dest_surface=dest_surface)


class Screen:
    """Interface to the screen."""
    def _set_surface(self, surface):
        self.surface = surface
        self.width, self.height = surface.get_size()

    def bounds(self):
        """Return a Rect representing the bounds of the screen."""
        return ZRect((0, 0), (self.width, self.height))

    def clear(self):
        """Clear the screen to black."""
        self.fill((0, 0, 0))

    def fill(self, color, gcolor=None):
        """Fill the screen with a colour."""
        if gcolor:
            start = make_color(color)
            stop = make_color(gcolor)
            blit_gradient(start, stop, self.surface)
        else:
            self.surface.fill(make_color(color))

    def blit(self, image, pos):
        """Draw a sprite onto the screen.

        "blit" is an archaic name for this operation, but one that is is still
        frequently used, for example in Pygame. See the `Wikipedia article`__
        for more about the etymology of the term.

        .. __: http://en.wikipedia.org/wiki/Bit_blit

        :param image: A Surface or the name of an image object to load.
        :param pos: The coordinates at which the top-left corner of the sprite
                    will be positioned. This may be given as a pair of
                    coordinates or as a Rect. If a Rect is given the sprite
                    will be drawn at ``rect.topleft``.

        """
        if isinstance(image, str):
            image = loaders.images.load(image)
        self.surface.blit(image, pos, None, pygame.BLEND_ALPHA_SDL2)

    @property
    def draw(self):
        return SurfacePainter(self.surface)

    def __repr__(self):
        return "<Screen width={} height={}>".format(self.width, self.height)


screen_instance = Screen()
