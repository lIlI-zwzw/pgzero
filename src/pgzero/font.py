# Import the default font name constant from the sibling module 'ptext'
# (Relative import specific to pgzero's internal module structure)
from .ptext import DEFAULT_FONT_NAME

# Font Class: A configuration container for text rendering in Pygame Zero (pgzero)
# This class encapsulates all visual styling properties required to render text
# on the screen in pgzero, centralizing text appearance configuration
class Font:
    # Re-import core default constants from the 'ptext' module for internal class usage
    # These constants establish the baseline styling defaults for pgzero text rendering
    from .ptext import (DEFAULT_FONT_NAME, DEFAULT_FONT_SIZE,
                        DEFAULT_BACKGROUND, DEFAULT_ANCHOR,
                        DEFAULT_ALIGN, DEFAULT_COLOR,
                        DEFAULT_SHADOW_COLOR, DEFAULT_OUTLINE_COLOR,
                        DEFAULT_STRIP, DEFAULT_LINE_HEIGHT)

    # Initialize a Font instance with customizable text styling properties
    # All parameters include default values that match pgzero's standard text behavior
    # Raises ValueError if conflicting font source parameters are provided
    def __init__(self, 
                 name=None,               # Custom font file path/name (e.g., "arial.ttf")
                 size=DEFAULT_FONT_SIZE,  # Font size in pixels (integer values only)
                 sysname=None,            # System font name (alternative to file-based 'name')
                 antialias=True,          # Enable anti-aliasing for smooth text edges
                 bold=False,              # Render text with bold weight
                 italic=False,            # Render text in italic style
                 underline=False,         # Add underline decoration to the text
                 color=DEFAULT_COLOR,     # Text foreground color (RGB/RGBA tuple, e.g., (255,255,255))
                 background=DEFAULT_BACKGROUND,  # Background color behind rendered text
                 center=False,            # DEPRECATED: Use 'anchor'/'align' instead (legacy compatibility flag)
                 width=None,              # Maximum width (pixels) for automatic text wrapping
                 widthem=None,            # Horizontal scaling factor for text width adjustment
                 lineheight=DEFAULT_LINE_HEIGHT,  # Vertical spacing between text lines (multiplier)
                 strip=DEFAULT_STRIP,     # Remove leading/trailing whitespace from text content
                 align=DEFAULT_ALIGN,     # Horizontal text alignment (options: left/center/right)
                 owidth=None,             # Thickness of text outline (pixels; None = no outline)
                 ocolor=DEFAULT_OUTLINE_COLOR,    # Color of the text outline (RGB/RGBA tuple)
                 shadow=None,             # (x,y) pixel offset tuple for text shadow (None = disabled)
                 scolor=DEFAULT_SHADOW_COLOR,     # Color of the text shadow (RGB/RGBA tuple)
                 gcolor=None,             # Gradient end color (None = gradient disabled)
                 alpha=1.0,               # Text transparency (0.0 = fully transparent, 1.0 = fully opaque)
                 anchor=DEFAULT_ANCHOR,   # (x,y) anchor point for text positioning (e.g., (0.5,0.5) = center)
                 angle=0):                # Text rotation angle (degrees; 0 = no rotation)

        # Validation: Prevent conflicting font source definitions
        # Users cannot specify both a file-based font ('name') and system font ('sysname')
        if name is not None and sysname is not None:
            raise ValueError("Cannot specify both 'name' (font file) and 'sysname' (system font)")

        # Assign parameters to instance variables (persist styling configuration)
        # Use default values if parameters are not explicitly provided
        self.size = size
        self.antialias = antialias
        self.underline = underline
        self.center = center
        self.lineheight = lineheight
        self.owidth = owidth
        self.scolor = scolor
        self.anchor = anchor
        # Fallback to default font name if no custom font file is specified
        self.name = name if name is not None else DEFAULT_FONT_NAME
        self.sysname = sysname
        self.bold = bold
        self.italic = italic
        self.color = color
        self.background = background
        self.width = width
        self.widthem = widthem
        self.strip = strip
        self.align = align
        self.ocolor = ocolor
        self.shadow = shadow
        self.gcolor = gcolor
        self.alpha = alpha
        self.angle = angle
