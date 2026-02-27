"""pygame-text - high-level text rendering with Pygame.

This module is directly copied from

    https://github.com/cosmologicon/pygame-text

at revision c04e59b7382a832e117f0598cdcbc1bb3eb26db5
and used under CC0.

"""
# ptext module: place this in your import directory.

# ptext.draw(text, pos=None, **options)

# Please see README.md for explanation of options.
# https://github.com/cosmologicon/pygame-text

# flake8: noqa: E501
from __future__ import division

from math import ceil, sin, cos, radians
import pygame

from .font import Font
DEFAULT_FONT_SIZE = 24
REFERENCE_FONT_SIZE = 100
DEFAULT_LINE_HEIGHT = 1.0
DEFAULT_FONT_NAME = None
FONT_NAME_TEMPLATE = "%s"
DEFAULT_COLOR = "white"
DEFAULT_BACKGROUND = None
DEFAULT_OUTLINE_COLOR = "black"
DEFAULT_SHADOW_COLOR = "black"
OUTLINE_UNIT = 1 / 24
SHADOW_UNIT = 1 / 18
DEFAULT_ALIGN = "left"  # left, center, or right
DEFAULT_ANCHOR = 0, 0  # 0, 0 = top left ;  1, 1 = bottom right
DEFAULT_STRIP = True
ALPHA_RESOLUTION = 16
ANGLE_RESOLUTION_DEGREES = 3

AUTO_CLEAN = True
MEMORY_LIMIT_MB = 64
MEMORY_REDUCTION_FACTOR = 0.5

pygame.font.init()

_font_cache = {}


def getfont(fontname=None, fontsize=None, sysfontname=None,
            bold=None, italic=None, underline=None):
    if fontname is not None and sysfontname is not None:
        raise ValueError("Can't set both fontname and sysfontname")
    if fontname is None and sysfontname is None:
        fontname = DEFAULT_FONT_NAME
    if fontsize is None:
        fontsize = DEFAULT_FONT_SIZE
    key = fontname, fontsize, sysfontname, bold, italic, underline
    if key in _font_cache:
        return _font_cache[key]
    if sysfontname is not None:
        font = pygame.font.SysFont(
            sysfontname, fontsize, bold or False, italic or False)
    else:
        if fontname is not None:
            fontname = FONT_NAME_TEMPLATE % fontname
        try:
            font = pygame.font.Font(fontname, fontsize)
        except IOError:
            raise IOError("unable to read font filename: %s" % fontname)
    if bold is not None:
        font.set_bold(bold)
    if italic is not None:
        font.set_italic(italic)
    if underline is not None:
        font.set_underline(underline)
    _font_cache[key] = font
    return font


def wrap(text, fontname=None, fontsize=None, sysfontname=None,
         bold=None, italic=None, underline=None, width=None, widthem=None, strip=None):
    if widthem is None:
        font = getfont(fontname, fontsize, sysfontname,
                       bold, italic, underline)
    elif width is not None:
        raise ValueError("Can't set both width and widthem")
    else:
        font = getfont(fontname, REFERENCE_FONT_SIZE,
                       sysfontname, bold, italic, underline)
        width = widthem * REFERENCE_FONT_SIZE
    if strip is None:
        strip = DEFAULT_STRIP
    texts = text.replace("\t", "    ").split("\n")
    lines = []
    for text in texts:
        if strip:
            text = text.rstrip(" ")
        if width is None:
            lines.append(text)
            continue
        if not text:
            lines.append("")
            continue
        # Preserve leading spaces in all cases.
        a = len(text) - len(text.lstrip(" "))
        # At any time, a is the rightmost known index you can legally split a line. I.e. it's legal
        # to add text[:a] to lines, and line is what will be added to lines if
        # text is split at a.
        a = text.index(" ", a) if " " in text else len(text)
        line = text[:a]
        while a + 1 < len(text):
            # b is the next legal place to break the line, with bline the
            # corresponding line to add.
            if " " not in text[a + 1:]:
                b = len(text)
                bline = text
            elif strip:
                # Lines may be split at any space character that immediately follows a non-space
                # character.
                b = text.index(" ", a + 1)
                while text[b - 1] == " ":
                    if " " in text[b + 1:]:
                        b = text.index(" ", b + 1)
                    else:
                        b = len(text)
                        break
                bline = text[:b]
            else:
                # Lines may be split at any space character, or any character immediately following
                # a space character.
                b = a + 1 if text[a] == " " else text.index(" ", a + 1)
            bline = text[:b]
            if font.size(bline)[0] <= width:
                a, line = b, bline
            else:
                lines.append(line)
                text = text[a:].lstrip(" ") if strip else text[a:]
                a = text.index(" ", 1) if " " in text[1:] else len(text)
                line = text[:a]
        if text:
            lines.append(line)
    return lines


_fit_cache = {}


def _fitsize(text, fontname, sysfontname, bold, italic, underline, width, height, lineheight, strip):
    key = text, fontname, sysfontname, bold, italic, underline, width, height, lineheight, strip
    if key in _fit_cache:
        return _fit_cache[key]

    def fits(fontsize):
        texts = wrap(text, fontname, fontsize, sysfontname,
                     bold, italic, underline, width, strip)
        font = getfont(fontname, fontsize, sysfontname,
                       bold, italic, underline)
        w = max(font.size(line)[0] for line in texts)
        linesize = font.get_linesize() * lineheight
        h = int(round((len(texts) - 1) * linesize)) + font.get_height()
        return w <= width and h <= height
    a, b = 1, 256
    if not fits(a):
        fontsize = a
    elif fits(b):
        fontsize = b
    else:
        while b - a > 1:
            c = (a + b) // 2
            if fits(c):
                a = c
            else:
                b = c
        fontsize = a
    _fit_cache[key] = fontsize
    return fontsize


def _resolvecolor(color, default):
    if color is None:
        color = default
    if color is None:
        return None
    try:
        return tuple(pygame.Color(color))
    except ValueError:
        return tuple(color)


def _resolvealpha(alpha):
    if alpha >= 1:
        return 1
    return max(int(round(alpha * ALPHA_RESOLUTION)) / ALPHA_RESOLUTION, 0)


def _resolveangle(angle):
    if not angle:
        return 0
    angle %= 360
    return int(round(angle / ANGLE_RESOLUTION_DEGREES)) * ANGLE_RESOLUTION_DEGREES


# Return the set of points in the circle radius r, using Bresenham's
# circle algorithm
_circle_cache = {}


def _circlepoints(r):
    r = int(round(r))
    if r in _circle_cache:
        return _circle_cache[r]
    x, y, e = r, 0, 1 - r
    _circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()
    return points


_surf_cache = {}
_surf_tick_usage = {}
_surf_size_total = 0
_unrotated_size = {}
_tick = 0


def getsurf(text, fontname=None, fontsize=None, sysfontname=None, bold=None, italic=None,
            underline=None, width=None, widthem=None, strip=None, color=None,
            background=None, antialias=True, ocolor=None, owidth=None, scolor=None, shadow=None,
            gcolor=None, alpha=1.0, align=None, lineheight=None, angle=0, cache=True):
    global _tick, _surf_size_total
    if fontname is None:
        fontname = DEFAULT_FONT_NAME
    if fontsize is None:
        fontsize = DEFAULT_FONT_SIZE
    fontsize = int(round(fontsize))
    if align is None:
        align = DEFAULT_ALIGN
    if align in ["left", "center", "right"]:
        align = [0, 0.5, 1][["left", "center", "right"].index(align)]
    if lineheight is None:
        lineheight = DEFAULT_LINE_HEIGHT
    color = _resolvecolor(color, DEFAULT_COLOR)
    background = _resolvecolor(background, DEFAULT_BACKGROUND)
    gcolor = _resolvecolor(gcolor, None)
    ocolor = None if owidth is None else _resolvecolor(
        ocolor, DEFAULT_OUTLINE_COLOR)
    scolor = None if shadow is None else _resolvecolor(
        scolor, DEFAULT_SHADOW_COLOR)
    opx = None if owidth is None else ceil(owidth * fontsize * OUTLINE_UNIT)
    spx = None if shadow is None else tuple(
        ceil(s * fontsize * SHADOW_UNIT) for s in shadow)
    alpha = _resolvealpha(alpha)
    angle = _resolveangle(angle)
    strip = DEFAULT_STRIP if strip is None else strip
    key = (text, fontname, fontsize, sysfontname, bold, italic, underline, width, widthem, strip,
           color, background, antialias, ocolor, opx, scolor, spx, gcolor, alpha, align, lineheight, angle)
    if key in _surf_cache:
        _surf_tick_usage[key] = _tick
        _tick += 1
        return _surf_cache[key]
    texts = wrap(text, fontname, fontsize, sysfontname, bold, italic, underline,
                 width=width, widthem=widthem, strip=strip)
    if angle:
        surf0 = getsurf(text, fontname, fontsize, sysfontname, bold, italic, underline,
                        width, widthem, strip, color, background, antialias,
                        ocolor, owidth, scolor, shadow, gcolor, alpha, align, lineheight, cache=cache)
        if angle in (90, 180, 270):
            surf = pygame.transform.rotate(surf0, angle)
        else:
            surf = pygame.transform.rotozoom(surf0, angle, 1.0)
        _unrotated_size[(surf.get_size(), angle, text)] = surf0.get_size()
    elif alpha < 1.0:
        surf0 = getsurf(text, fontname, fontsize, sysfontname, bold, italic, underline,
                        width, widthem, strip, color, background, antialias,
                        ocolor, owidth, scolor, shadow, gcolor=gcolor, align=align,
                        lineheight=lineheight, cache=cache)
        surf = surf0.copy()
        array = pygame.surfarray.pixels_alpha(surf)
        array[:, :] = (array[:, :] * alpha).astype(array.dtype)
        del array
    elif spx is not None:
        surf0 = getsurf(text, fontname, fontsize, sysfontname, bold, italic, underline,
                        width, widthem, strip, color=color, background=(0, 0, 0, 0), antialias=antialias,
                        gcolor=gcolor, align=align, lineheight=lineheight, cache=cache)
        ssurf = getsurf(text, fontname, fontsize, sysfontname, bold, italic, underline,
                        width, widthem, strip, color=scolor, background=(0, 0, 0, 0), antialias=antialias,
                        align=align, lineheight=lineheight, cache=cache)
        w0, h0 = surf0.get_size()
        sx, sy = spx
        surf = pygame.Surface((w0 + abs(sx), h0 + abs(sy))).convert_alpha()
        surf.fill(background or (0, 0, 0, 0))
        dx, dy = max(sx, 0), max(sy, 0)
        surf.blit(ssurf, (dx, dy))
        x0, y0 = abs(sx) - dx, abs(sy) - dy
        if len(color) > 3 and color[3] == 0:
            array = pygame.surfarray.pixels_alpha(surf)
            array0 = pygame.surfarray.pixels_alpha(surf0)
            array[x0:x0 + w0, y0:y0 +
                  h0] -= array0.clip(max=array[x0:x0 + w0, y0:y0 + h0])
            del array, array0
        else:
            surf.blit(surf0, (x0, y0))
    elif opx is not None:
        surf0 = getsurf(text, fontname, fontsize, sysfontname, bold, italic, underline,
                        width, widthem, strip, color=color, background=(0, 0, 0, 0), antialias=antialias,
                        gcolor=gcolor, align=align, lineheight=lineheight, cache=cache)
        osurf = getsurf(text, fontname, fontsize, sysfontname, bold, italic, underline,
                        width, widthem, strip, color=ocolor, background=(0, 0, 0, 0), antialias=antialias,
                        align=align, lineheight=lineheight, cache=cache)
        w0, h0 = surf0.get_size()
        surf = pygame.Surface((w0 + 2 * opx, h0 + 2 * opx)).convert_alpha()
        surf.fill(background or (0, 0, 0, 0))
        for dx, dy in _circlepoints(opx):
            surf.blit(osurf, (dx + opx, dy + opx))
        if len(color) > 3 and color[3] == 0:
            array = pygame.surfarray.pixels_alpha(surf)
            array0 = pygame.surfarray.pixels_alpha(surf0)
            array[opx:-opx, opx:-
                  opx] -= array0.clip(max=array[opx:-opx, opx:-opx])
            del array, array0
        else:
            surf.blit(surf0, (opx, opx))
    else:
        font = getfont(fontname, fontsize, sysfontname,
                       bold, italic, underline)
        # pygame.Font.render does not allow passing None as an argument value
        # for background.
        if background is None or (len(background) > 3 and background[3] == 0) or gcolor is not None:
            lsurfs = [font.render(text, antialias, color).convert_alpha()
                      for text in texts]
        else:
            lsurfs = [font.render(text, antialias, color,
                                  background).convert_alpha() for text in texts]
        if gcolor is not None:
            import numpy
            for lsurf in lsurfs:
                m = numpy.clip(numpy.arange(
                    lsurf.get_height()) * 2.0 / font.get_ascent() - 1.0, 0, 1)
                array = pygame.surfarray.pixels3d(lsurf)
                for j in (0, 1, 2):
                    array[:, :, j] = (
                        (1.0 - m) * array[:, :, j] + m * gcolor[j]).astype(array.dtype)
                del array

        if len(lsurfs) == 1 and gcolor is None:
            surf = lsurfs[0]
        else:
            w = max(lsurf.get_width() for lsurf in lsurfs)
            linesize = font.get_linesize() * lineheight
            ys = [int(round(k * linesize)) for k in range(len(lsurfs))]
            h = ys[-1] + font.get_height()
            surf = pygame.Surface((w, h)).convert_alpha()
            surf.fill(background or (0, 0, 0, 0))
            for y, lsurf in zip(ys, lsurfs):
                x = int(round(align * (w - lsurf.get_width())))
                surf.blit(lsurf, (x, y))
    if cache:
        w, h = surf.get_size()
        _surf_size_total += 4 * w * h
        _surf_cache[key] = surf
        _surf_tick_usage[key] = _tick
        _tick += 1
    return surf


_default_surf_sentinel = ()


def draw(text, pos=None,
         fontname=None, fontsize=None, sysfontname=None,
         antialias=True, bold=None, italic=None, underline=None,
         color=None, background=None,
         top=None, left=None, bottom=None, right=None,
         topleft=None, bottomleft=None, topright=None, bottomright=None,
         midtop=None, midleft=None, midbottom=None, midright=None,
         center=None, centerx=None, centery=None,
         width=None,	widthem=None, lineheight=None, strip=None,
         align=None,
         owidth=None, ocolor=None,
         shadow=None, scolor=None,
         gcolor=None,
         alpha=1.0,
         anchor=None,
         angle=0,
         surf=_default_surf_sentinel,
         cache=True, 
         fontclass: Font=None):

    '''
    High-level text drawing function for Pygame with rich styling and positioning options.
    
    Renders and draws text to a Pygame surface with support for font styling, text wrapping,
    outlines, shadows, gradients, rotation, alpha transparency, and flexible positioning.
    
    Args:
        text (str): The text string to render and draw.
        pos (tuple[int, int], optional): Base position (x, y) for text placement before anchor adjustment.
            Overridden by explicit position parameters (e.g., topleft, center). Defaults to None.
        fontname (str, optional): Path/name of the custom font file to use. Mutually exclusive with sysfontname.
            Defaults to DEFAULT_FONT_NAME.
        fontsize (int, optional): Font size in pixels. Defaults to DEFAULT_FONT_SIZE.
        sysfontname (str, optional): Name of system font to use (from pygame.font.get_fonts()).
            Mutually exclusive with fontname. Defaults to None.
        antialias (bool, optional): Whether to use antialiasing for text rendering. Defaults to True.
        bold (bool, optional): Whether to render text in bold. Overrides font's default bold setting. Defaults to None.
        italic (bool, optional): Whether to render text in italic. Overrides font's default italic setting. Defaults to None.
        underline (bool, optional): Whether to render text with underline. Overrides font's default underline setting. Defaults to None.
        color (str/tuple, optional): Text color (name or RGB/RGBA tuple). Defaults to DEFAULT_COLOR.
        background (str/tuple, optional): Background color for text (name or RGB/RGBA tuple).
            Set to None for transparent background. Defaults to DEFAULT_BACKGROUND.
        top (int, optional): Explicit top y-coordinate for text anchor. Overrides pos's y value. Defaults to None.
        left (int, optional): Explicit left x-coordinate for text anchor. Overrides pos's x value. Defaults to None.
        bottom (int, optional): Explicit bottom y-coordinate for text anchor. Overrides pos's y value. Defaults to None.
        right (int, optional): Explicit right x-coordinate for text anchor. Overrides pos's x value. Defaults to None.
        topleft (tuple[int, int], optional): Explicit top-left (x, y) position for text anchor.
            Overrides pos and individual left/top parameters. Defaults to None.
        bottomleft (tuple[int, int], optional): Explicit bottom-left (x, y) position for text anchor.
            Overrides pos and individual left/bottom parameters. Defaults to None.
        topright (tuple[int, int], optional): Explicit top-right (x, y) position for text anchor.
            Overrides pos and individual right/top parameters. Defaults to None.
        bottomright (tuple[int, int], optional): Explicit bottom-right (x, y) position for text anchor.
            Overrides pos and individual right/bottom parameters. Defaults to None.
        midtop (tuple[int, int], optional): Explicit middle-top (x, y) position for text anchor.
            Overrides pos and centerx/top parameters. Defaults to None.
        midleft (tuple[int, int], optional): Explicit middle-left (x, y) position for text anchor.
            Overrides pos and left/centery parameters. Defaults to None.
        midbottom (tuple[int, int], optional): Explicit middle-bottom (x, y) position for text anchor.
            Overrides pos and centerx/bottom parameters. Defaults to None.
        midright (tuple[int, int], optional): Explicit middle-right (x, y) position for text anchor.
            Overrides pos and right/centery parameters. Defaults to None.
        center (tuple[int, int], optional): Explicit center (x, y) position for text anchor.
            Overrides pos and centerx/centery parameters. Defaults to None.
        centerx (int, optional): Explicit horizontal center x-coordinate for text anchor.
            Overrides pos's x value. Defaults to None.
        centery (int, optional): Explicit vertical center y-coordinate for text anchor.
            Overrides pos's y value. Defaults to None.
        width (int, optional): Maximum width (pixels) for text wrapping. Defaults to None (no wrapping).
        widthem (float, optional): Relative maximum width (scaled to REFERENCE_FONT_SIZE) for text wrapping.
            Mutually exclusive with width. Defaults to None.
        lineheight (float, optional): Line height multiplier relative to font's default line height.
            Defaults to DEFAULT_LINE_HEIGHT.
        strip (bool, optional): Whether to strip trailing spaces from text lines before wrapping.
            Defaults to DEFAULT_STRIP.
        align (str/float, optional): Horizontal text alignment within wrapped lines:
            "left"/0, "center"/0.5, "right"/1. Defaults to DEFAULT_ALIGN.
        owidth (float, optional): Outline width multiplier (scaled by fontsize * OUTLINE_UNIT).
            Set to None to disable outline. Defaults to None.
        ocolor (str/tuple, optional): Outline color (name or RGB/RGBA tuple). Used only if owidth is set.
            Defaults to DEFAULT_OUTLINE_COLOR.
        shadow (tuple[float, float], optional): Shadow offset (dx, dy) multiplier (scaled by fontsize * SHADOW_UNIT).
            Set to None to disable shadow. Defaults to None.
        scolor (str/tuple, optional): Shadow color (name or RGB/RGBA tuple). Used only if shadow is set.
            Defaults to DEFAULT_SHADOW_COLOR.
        gcolor (str/tuple, optional): Gradient color (name or RGB/RGBA tuple) for vertical text gradient.
            Blends from text color to gcolor from top to bottom. Set to None to disable gradient. Defaults to None.
        alpha (float, optional): Alpha transparency (0.0 = fully transparent, 1.0 = fully opaque).
            Defaults to 1.0.
        anchor (tuple[float, float], optional): Text anchor point (hanchor, vanchor) where:
            - hanchor: 0 (left) to 1 (right) for horizontal anchor
            - vanchor: 0 (top) to 1 (bottom) for vertical anchor
            Defaults to DEFAULT_ANCHOR.
        angle (float, optional): Rotation angle (degrees) for the text surface (clockwise).
            Defaults to 0 (no rotation).
        surf (pygame.Surface, optional): Target surface to draw text on. Defaults to display surface if None.
        cache (bool, optional): Whether to cache rendered text surfaces for performance. Defaults to True.
        fontclass (Font, optional): Custom Font class instance to override default font properties.
            Overrides individual font parameters if they are None. Defaults to None.
    
    Returns:
        tuple[pygame.Surface, tuple[int, int]]: Tuple containing:
            - Rendered text surface
            - Final (x, y) position where the surface was blitted
    '''


    # Initialize font properties from custom Font class if provided
    # Override default values with fontclass attributes when available
    if fontclass is not None:
        font = fontclass
        if fontsize is None:fontsize = font.size
        if antialias:antialias = font.antialias
        if underline is None:underline = font.underline
        if center is None:center = font.center
        if lineheight is None:lineheight = font.lineheight
        if owidth is None:owidth = font.owidth
        if scolor is None:scolor = font.scolor
        if anchor is None:anchor = font.anchor
        if fontname is None and sysfontname is None:
            fontname,sysfontname = font.name,font.sysname
        if bold is None:bold = font.bold
        if italic is None:italic = font.italic
        if color is None:color = font.color
        if background is None:background = font.background
        if width is None:width = font.width
        if widthem is None:widthem = font.widthem
        if strip is None:strip = font.strip
        if align is None:align = font.align
        if ocolor is None:ocolor = font.ocolor
        if shadow is None:shadow = font.shadow
        if gcolor is None:gcolor = font.gcolor
        if alpha is None:alpha = font.alpha
        if angle is None:angle = font.angle

    # Resolve position parameters to base x/y coordinates and anchor points
    # Priority: explicit position tuples (topleft, center, etc.) > single edge positions (left, top, etc.)


    if topleft:
        left, top = topleft
    if bottomleft:
        left, bottom = bottomleft
    if topright:
        right, top = topright
    if bottomright:
        right, bottom = bottomright
    if midtop:
        centerx, top = midtop
    if midleft:
        left, centery = midleft
    if midbottom:
        centerx, bottom = midbottom
    if midright:
        right, centery = midright
    if center:
        centerx, centery = center

    x, y = pos or (None, None)
    hanchor, vanchor = anchor or (None, None)
    if left is not None:
        x, hanchor = left, 0
    if centerx is not None:
        x, hanchor = centerx, 0.5
    if right is not None:
        x, hanchor = right, 1
    if top is not None:
        y, vanchor = top, 0
    if centery is not None:
        y, vanchor = centery, 0.5
    if bottom is not None:
        y, vanchor = bottom, 1
    if x is None:
        raise ValueError("Unable to determine horizontal position")
    if y is None:
        raise ValueError("Unable to determine vertical position")

    if align is None:
        align = hanchor
    if hanchor is None:
        hanchor = DEFAULT_ANCHOR[0]
    if vanchor is None:
        vanchor = DEFAULT_ANCHOR[1]

    tsurf = getsurf(text, fontname, fontsize, sysfontname, bold, italic, underline, width, widthem,
                    strip, color, background, antialias, ocolor, owidth, scolor, shadow, gcolor, alpha, align,
                    lineheight, angle, cache)
    angle = _resolveangle(angle)
    if angle:
        w0, h0 = _unrotated_size[(tsurf.get_size(), angle, text)]
        S, C = sin(radians(angle)), cos(radians(angle))
        dx, dy = (0.5 - hanchor) * w0, (0.5 - vanchor) * h0
        x += dx * C + dy * S - 0.5 * tsurf.get_width()
        y += -dx * S + dy * C - 0.5 * tsurf.get_height()
    else:
        x -= hanchor * tsurf.get_width()
        y -= vanchor * tsurf.get_height()
    x = int(round(x))
    y = int(round(y))

    if surf is _default_surf_sentinel:
        surf = pygame.display.get_surface()
    if surf is not None:
        surf.blit(tsurf, (x, y))

    if AUTO_CLEAN:
        clean()

    return tsurf, (x, y)


def drawbox(text, rect, fontname=None, sysfontname=None, lineheight=None, anchor=None,
            bold=None, italic=None, underline=None, strip=None, **kwargs):
    if fontname is None:
        fontname = DEFAULT_FONT_NAME
    if lineheight is None:
        lineheight = DEFAULT_LINE_HEIGHT
    hanchor, vanchor = anchor = anchor or (0.5, 0.5)
    rect = pygame.Rect(rect)
    x = rect.x + hanchor * rect.width
    y = rect.y + vanchor * rect.height
    fontsize = _fitsize(text, fontname, sysfontname, bold, italic, underline,
                        rect.width, rect.height, lineheight, strip)
    return draw(text, (x, y), fontname=fontname, fontsize=fontsize, lineheight=lineheight,
                width=rect.width, strip=strip, anchor=anchor, **kwargs)


def clean():
    global _surf_size_total
    memory_limit = MEMORY_LIMIT_MB * (1 << 20)
    if _surf_size_total < memory_limit:
        return
    memory_limit *= MEMORY_REDUCTION_FACTOR
    keys = sorted(_surf_cache, key=_surf_tick_usage.get)
    for key in keys:
        w, h = _surf_cache[key].get_size()
        del _surf_cache[key]
        del _surf_tick_usage[key]
        _surf_size_total -= 4 * w * h
        if _surf_size_total < memory_limit:
            break

