
from typing import Literal
import re
ANSI_RE = re.compile(r'\033\[[0-9;]*m')
from .print_stack import in_notebook

class Cstr(str):
    """
    Class inheritting for type string, with a few additional methods for coloring the string when printed to the console.
    
    Methods:
        green: Returns the string in green color
        blue: Returns the string in blue color
        red: Returns the string in red color
        yellow: Returns the string in yellow color
        bold: Returns the string in bold font
        underline: Returns the string with underline
        italic: Returns the string in italic font
        strikethrough: Returns the string with strikethrough
        highlight: Returns the string with highlighted background
        
    Format:
        print(f'{ColoredString("This is a colored string"):green}') # prints the string in green color
        print(f'{ColoredString("This is a colored string"):g}') # prints the string in green color
    
    """
    
    _COLORS = {
        'green': '\033[92m',
        'blue': '\033[94m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'reset': '\033[0m',
        
        'bold': '\033[1m',
        'underline': '\033[4m',
        'italic': '\033[3m',
        'strikethrough': '\033[9m',
        'highlight': '\033[7m',
    }
    
    def __init__(self,string:str):
        """
        Args:
            string (str): The string to be printed in color (can also be anything that can be converted to a string using str() function)
        """
        super().__init__() # how the hell does this work???
        
    
    ##############
    ### COLORS ###
    ##############
    
    def green(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["green"] + self + self._COLORS["reset"]
        )
    
    def blue(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["blue"] + self + self._COLORS["reset"]
        )
    
    def red(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["red"] + self + self._COLORS["reset"]
        )
    
    def yellow(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["yellow"] + self + self._COLORS["reset"]
        )
    
    def magenta(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["magenta"] + self + self._COLORS["reset"]
        )
        
    def cyan(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["cyan"] + self + self._COLORS["reset"]
        )
        
    def white(self) -> 'Cstr':
        return self
    
    
    #############
    ### FONTS ###
    #############
    
    def bold(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["bold"] + self + self._COLORS["reset"]
        )
    
    def underline(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["underline"] + self + self._COLORS["reset"]
        )
    
    def italic(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["italic"] + self + self._COLORS["reset"]
        )
    
    def strikethrough(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["strikethrough"] + self + self._COLORS["reset"]
        )
    
    def highlight(self) -> 'Cstr':
        return self.__class__(
            self._COLORS["highlight"] + self + self._COLORS["reset"]
        )
    
    
    ##############
    ### FORMAT ###
    ##############
    
    def __format__(self, format_spec:str) -> 'Cstr':
        if not format_spec:
            return self
    
        colors = [
            'green', 'blue', 'red', 'yellow', 'magenta', 'cyan', 'white'
        ]
        fonts = [
            'bold', 'underline', 'italic', 'strikethrough', 'highlight'
        ]
        
        color_spec = format_spec[0]
        if len(format_spec) > 1:
            font_spec = format_spec[1:]
        else:
            font_spec = ''
        assert len(format_spec) <= 2, f"Invalid format specifier: {format_spec}. Must be one or two characters long."
        
        allowed_color_specs = [c[0] for c in colors]
        allowed_font_specs = [f[0] for f in fonts] + ['']
        
        assert color_spec in allowed_color_specs, f"Invalid format specifier: {format_spec}. Must be one of {allowed_color_specs}."
        assert font_spec in allowed_font_specs, f"Invalid format specifier: {format_spec}. Must be one of {allowed_font_specs}."
        
        out = self
        
        # 1. Add the color to the string
        color = [c for c in colors if c.startswith(color_spec)][0] # there is only one anyway
        out = getattr(out, color)()
        
        # 2. Add the font to the string
        if font_spec:
            font = [f for f in fonts if f.startswith(font_spec)][0]
            out = getattr(out, font)()
            
        return out
    
    # return string without color chars
    def strip_ansi(self) -> str:
        """
        Returns the string without ANSI escape codes.
        """
        return ANSI_RE.sub('', self)
    
    def length(self) -> int:
        """
        Returns the length of the string without ANSI escape codes.
        """
        if not in_notebook:
            return len(self.strip_ansi())
        else:
            return len(self)

    def strip(self) -> "str":
        """
        Returns the string without leading and trailing whitespace.
        """
        stripped = str.strip(self)        
        no_leading_ansi = re.sub(r'^\033\[[0-9;]*m', '', stripped) # remove leading ANSI
        no_ansi = re.sub(r'\033\[[0-9;]*m$', '', no_leading_ansi) # remove trailing ANSI

        no_ansi_stripped = no_ansi.strip()
        return self.replace(stripped, no_ansi_stripped)
        


def cstr(obj:object, format_spec:str='') -> 'Cstr':
    """
    Convert an object into a color-capable string (`Cstr`).

    This function formats `obj` using Python's built-in ``format`` machinery
    (e.g. for floats, integers, or custom ``__format__`` implementations),
    and then wraps the resulting text into a :class:`Cstr` object.  
    The returned `Cstr` instance supports ANSI colorization, text styles
    (bold, underline, italic, …), and compact format specifiers.

    Parameters
    ----------
    obj : object
        The object to convert to a colored string. Any object that can be
        formatted via ``format(obj, format_spec)`` is accepted.
    format_spec : str, optional
        Standard Python format specification applied *before*
        converting the output to a `Cstr`.
        For example: ``'.2f'``, ``'05d'``, ``'>10s'``, etc.

    Returns
    -------
    Cstr
        A colored-string wrapper that supports methods such as
        ``.green()``, ``.red()``, ``.bold()``, ``.underline()``,
        as well as compact format usage inside f-strings (e.g. ``:gb``).

    Notes
    -----
    - Color and style transformations are applied *after* formatting.
    - Inside f-strings, short format specifiers allow concise styling:
      ``g`` → green, ``r`` → red, ``b`` → blue,  
      combined with ``b`` for bold, ``u`` for underline, …
      Examples: ``:gb`` (green + bold), ``:ru`` (red + underline).

    Examples
    --------
    Basic usage:

    >>> print(cstr("Hello").green())
    Hello   # in green

    With numeric formatting:

    >>> x = 3.14159
    >>> print(cstr(x, '.2f').cyan())
    3.14    # in cyan

    Using short form styling inside an f-string:

    >>> print(f"Value: {cstr('OK'):gb}")
    Value: OK   # green + bold
    """
    return Cstr(format(obj, format_spec))



if __name__ == '__main__':
    x = 3.1416
    print(cstr(x, '.2f').green().bold())
    print(f"This was the number PI in {cstr('green'):g} color.")
    
    # testing the length method
    s = "Hello, World!"
    colored_s = cstr(s).red().bold().underline()
    print(f"Original length: {len(s)}, Colored length: {colored_s.length()}, len(colored_s): {len(colored_s)}")
    
