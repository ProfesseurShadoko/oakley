

from .fancy_string import cstr
from .mutable_class import MutableClass
from typing import Literal
import os




class Message(MutableClass):
    """
    A lightweight, styled console message utility.


    The ``Message`` class provides formatted console output with optional
    color coded prefixes indicating importance levels (info, success,
    warning, error). It inherits global indentation and muting behavior from
    :class:`MutableClass`, ensuring consistent formatting when used alongside
    other Oakley utilities.


    Messages are printed immediately upon instantiation unless their type is
    currently muted via :meth:`Message.listen`.


    Parameters
    ----------
    msg : str
        The message text to display.
    type : {'#', '?', '!', 'i'}, optional
        A one‑character tag defining the message category:


            - ``'#'`` — success (green)
            - ``'i'`` — info (cyan)
            - ``'?'`` — warning (yellow)
            - ``'!'`` — error (red)


        Default is ``'i'``.


    Notes
    -----
    Instantiating a ``Message`` automatically prints it. To avoid printing,
    adjust levels using :meth:`Message.listen` or temporarily mute all
    messages with the context manager ``Message.mute()``.
    
    
    Examples
        --------
        Basic usage:

        >>> from oakley import Message
        >>> Message("Build succeeded", "#")
        [#] Build succeeded

        Message levels:

        >>> Message("Informational note.")
        [i] Informational note.
        >>> Message("Careful: something looks odd.", "?")
        [?] Careful: something looks odd.
        >>> Message("Fatal error encountered.", "!")
        [!] Fatal error encountered.

        Indentation:
        
        >>> with Message("Tab will be handled automatically"):
                Message("Another indented info message.")
        ...     Message.print("Another indented info message.") # using Message.print rather than print allows indentation and muting
            [i] Tab will be handled automatically
             > [i] Another indented info message.
             > Another indented info message.

        Listing collections:

        >>> Message("My list:", "i").list([3, 1, 4])
        [i] My list:
            > 00: 3
            > 01: 1
            > 02: 4

        Muting:

        >>> with Message.mute():
        ...     Message("This will be hidden.")
        ...     Message.print("This will also be hidden.")
        
        Paragraph:
        >>> Message.par() # equivalent to print() (but does nothing if muted)
    """
    
    _active = ['i', '#', '?', '!']
    
    def __init__(self, msg:str, type:Literal['#', '?', '!', 'i'] = 'i') -> None:
        """
        Construct and display a formatted message.


        Parameters
        ----------
        msg : str
            The message string to display.
        type : {'#', '?', '!', 'i'}, optional
            The category of message, determining prefix color and
            whether it is currently active. Default is ``'i'``.


        Raises
        ------
        AssertionError
            If ``msg`` is not a string or ``type`` is invalid.
            
        Examples
        --------
        Basic usage:

        >>> from oakley import Message
        >>> Message("Build succeeded", "#")
        [#] Build succeeded

        Message levels:

        >>> Message("Informational note.")
        [i] Informational note.
        >>> Message("Careful: something looks odd.", "?")
        [?] Careful: something looks odd.
        >>> Message("Fatal error encountered.", "!")
        [!] Fatal error encountered.

        Indentation:

        >>> with Message.tab():
        ...     Message("Indented warning", "?")
            > [?] Indented warning
        
        >>> with Message("Tab will be handled automatically"):
                Message("Another indented info message.")
        ...     Message.print("Another indented info message.") # using Message.print rather than print allows indentation and muting
            [i] Tab will be handled automatically
             > [i] Another indented info message.
             > Another indented info message.

        Listing collections:

        >>> Message("My list:", "i").list([3, 1, 4])
        [i] My list:
            > 00: 3
            > 01: 1
            > 02: 4

        Muting:

        >>> with Message.mute():
        ...     Message("This will be hidden.")
        ...     Message.print("This will also be hidden.")
        
        Paragraph:
        >>> Message.par() # equivalent to print() (but does nothing if muted)
        
        
        """
        
        assert isinstance(msg, str), f"msg must be a string, not {msg.__class__}"
        assert type in ['#', '?', '!', 'i'], f"type must be one of '#', '?', '!', 'i', not {type}"
        self.msg = msg
        self.type = type
        
        self._display()
    
    
    def _display(self) -> None:
        """
        Display the message if its type is currently active.


        This method checks ``self.type`` against ``Message._active`` and, if
        allowed, prints the message with the correct indentation and color.
        """
        if not self.type in self._active:
            return
        
        self.print(
            self._get_prefix(), self.msg
        )
        
    def _get_prefix(self) -> str:
        """
        Return the ANSI colored prefix corresponding to the message type.


        Returns
        -------
        str
            A colored tag such as ``'[i]'`` or ``'[!]'``.
        """
        return {
            '#': cstr('[#]').green(),
            'i': cstr('[i]').cyan(),
            '?': cstr('[?]').yellow(),
            '!': cstr('[!]').red()
        }[self.type]
    
    @classmethod
    def listen(cls:type, lvl:int=0) -> None:
        """
        Set the verbosity level controlling which message types are printed.


        Parameters
        ----------
        lvl : int, optional
            Verbosity level:


                - ``0`` — print all messages (default)
                - ``1`` — print warnings and errors only
                - ``2`` — print errors only


        Notes
        -----
        This method updates ``Message._active`` to filter message types.
        """
        cls._active = {
            0: ['i', '#', '?', '!'],
            1: ['?', '!'],
            2: ['!']
        }[lvl]
        
        
    def list(self, collection:list|dict) -> None:
        """
        Display elements of a list or dictionary in an indented block.


        Parameters
        ----------
        collection : list or dict
            The collection to display. Lists and other iterables are converted
            to ``{index: value}`` form. Dictionaries are displayed as
            ``key: value`` pairs.


        Notes
        -----
        - Empty collections print ``"empty"``.
        - Keys are aligned for readability.
        - The formatting color depends on the message type.


        Examples
        --------
        >>> Message("Items:", "?").list([10, 20, 30])
        >>> Message("User info:").list({"name": "Alice", "age": 30})
        """
        
        color = {
            "#": "g",
            "?": "y",
            "i": "c",
            "!": "r"
        }[self.type]
        with Message.tab():
            
            n_digits = None
            if not isinstance(collection, dict):
                # check that colleciton is iterable
                try:
                    iter(collection)
                except TypeError:
                    Message.print(collection) # just print out the object
                
                # transform into a dictionary idx --> value
                collection = {i: value for i, value in enumerate(collection)}
                n_digits = len(str(len(collection)-1)) # optimized computation of log10 here
                
            if len(collection) == 0:
                Message.print(f"{cstr('empty'):ri}")
            
            # find the longest key in the collection
            max_key_length = max([len(str(key)) for key in collection]) if n_digits is None else n_digits
            
            for key, value in collection.items():
                
                if n_digits is None:
                    key = f"{cstr(key):{color}}:" + " " * (max_key_length - len(str(key)))
                else:
                    key = f"{cstr(key, f'0{n_digits}d'):{color}}:"
                
                Message.print(f"{key} {value}")
    
    def todo(self, collection:dict) -> None:
        """
        Display a TODO item or list of items.

        Parameters
        ----------
        collection : dict
            A dictionary where keys are TODO descriptions and values are
            booleans indicating completion status.


        Notes
        -----
        - Completed items are shown in the color of the message.
        - Incomplete items are shown in red.


        Examples
        --------
        >>> Message("My TODOs:").todo({
        ...     "Write unit tests": False,
        ...     "Update documentation": True
        ... })
        """
        color = {
            "#": "g",
            "?": "y",
            "i": "c",
            "!": "r"
        }[self.type]
        
        self.list([
            f"{cstr(task):{color}}" if complete else cstr(task).red()
            for task, complete in collection.items()
        ])
            



if __name__ == '__main__':
    Message("This is a success message", "#")
    Message("This is an info message", "i")
    Message("This is a warning message", "?")
    Message("This is an error message", "!")
    Message.par()
    Message.listen(1)
    Message("This is a success message. It should not be displayed.", "#")
    Message("This is a warning. It should be displayed.", "?")
    
    Message.listen()
    Message.par()
    
    with Message.tab():
        Message("This message should be indented.")
    Message("This message should not be indented.")
    Message.par()
    
    
    my_array = [1, 2, 0, 0, 89, 1]
    my_dict = {
        "name": "Bob",
        "age": 21
    }
    
    Message("My Array:", "?").list(my_array)
    Message("Information:").list(my_dict)
    
    # todo list
    Message("My TODOs:", "#").todo({
        "Write unit tests": False,
        "Update documentation": True
    })
    
    
    
    
    
    
    
