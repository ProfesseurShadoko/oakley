
from .fancy_string import cstr
from .fancy_context_manager import FancyCM
from .print_stack import pStack, Spirit
from .xconfig import oakley_config
import os



class MutableClass(FancyCM):
    """
    Base class providing global muting, indentation, and formatted printing utilities.

    `MutableClass` is a foundational component used by Oakley's higher-level
    display helpers such as `Message`, `Task`, and `ProgressBar`. It centralizes
    logic for:

    - muting all output
    - managing indentation depth
    - providing a unified printing method with automatic indentation
    - offering context managers for temporary mute and indentation blocks
    - formatting time and date strings

    Any class inheriting from `MutableClass` automatically gains these behaviors,
    ensuring consistent display formatting across the package.

    Notes
    -----
    All muting and indentation state is *global* at the class level, not per
    instance. This means that nested utilities (e.g., `Message` inside a `Task`)
    remain synchronized.

    Indentation contexts increment the indentation level on entry and decrement on
    exit. Muting contexts suppress all printing except when explicitly overridden
    through keyword arguments in :meth:`print`.

    Examples
    --------
    Basic printing:

    >>> from oakley import MutableClass
    >>> MutableClass.print("Hello")
    Hello

    Indentation:

    >>> with MutableClass.tab():
    ...     MutableClass.print("Indented once")
        > Indented once
    >>> with MutableClass.tab():
    ...     with MutableClass.tab():
    ...         MutableClass.print("Indented twice")
        >> Indented twice

    Muting:

    >>> MutableClass.mute()
    >>> MutableClass.print("This will not be printed")
    >>> MutableClass.unmute()
    >>> MutableClass.print("Printing restored")
    Printing restored

    Temporary mute:

    >>> with MutableClass.mute():
    ...     MutableClass.print("Hidden")
    >>> MutableClass.print("Visible again")
    Visible again

    Using the class as a context manager (automatic indentation):

    >>> with MutableClass():
    ...     MutableClass.print("Indented by context manager")
        > Indented by context manager

    Time and date helpers:

    >>> MutableClass.time(123.4)
    '00:02:03'
    >>> MutableClass.date()
    '2025-03-19'
    >>> MutableClass.time_date()
    '2025-03-19 15:42:10'
"""
    
    mute_count = 0
    idx = 0
    indent = 0
    
    _initial_directory = None
    
    
    # -------------- #
    # !-- Muting --! #
    # -------------- #
    
    @staticmethod
    def muted() -> bool:
        """
        Check whether printing is currently muted.

        Returns
        -------
        bool
            ``True`` if the global mute counter is greater than zero,
            indicating that all output should be suppressed.
        """
        return MutableClass.mute_count > 0
    
    @staticmethod
    def mute() -> FancyCM:
        """
        Mute all printing globally.

        Each call increases the global mute counter. Printing is re-enabled
        only when the counter returns to zero, either manually via
        :meth:`unmute` or by exiting the context manager returned by this
        method.

        Returns
        -------
        FancyCM
            A context manager that automatically un-mutes on exit.

        Examples
        --------
        >>> with MutableClass.mute():
        ...     MutableClass.print("Hidden")
        >>> MutableClass.print("Visible")
        """
        MutableClass.mute_count += 1
        
        class MuteContext(FancyCM):
            def __exit__(self, *args):
                MutableClass.unmute()
                super().__exit__(*args)
        
        return MuteContext()
    
    @staticmethod
    def unmute() -> None:
        """
        Decrease the global mute counter.

        When the counter reaches zero, printing is no longer suppressed.
        """
        MutableClass.mute_count -= 1
        
    
    # ------------------- #    
    # !-- Indentation --! #
    # ------------------- #
    
    @staticmethod
    def tab() -> FancyCM:
        """
        Increase the global indentation level.

        Each call increments the indentation depth, affecting all future
        printed lines until indentation is decreased via :meth:`untab`
        or by leaving the context manager returned by this method.

        Returns
        -------
        FancyCM
            A context manager that automatically decreases the indentation
            level upon exit.

        Examples
        --------
        >>> with MutableClass.tab():
        ...     MutableClass.print("Indented")
            > Indented
        """
        MutableClass.indent += 1
        
        class TabContext(FancyCM):
            def __exit__(self, *args):
                MutableClass.untab()
                super().__exit__(*args)
        
        return TabContext()

    @staticmethod
    def untab() -> None:
        """
        Decrease the global indentation level by one.

        Indentation cannot go below zero. Used internally by the
        indentation context manager.
        """
        MutableClass.indent -= 1
    
    def __enter__(self):
        """
        Enter a context block that automatically increases indentation.

        Returns
        -------
        MutableClass
            The instance itself.

        Notes
        -----
        This makes the class usable as a context manager:

        >>> with MutableClass():
        ...     MutableClass.print("Indented")
            > Indented
        """
        MutableClass.tab()
        super().__enter__()
    
    def __exit__(self, *args):
        """
        Exit the indentation context started by :meth:`__enter__`.

        Decreases the global indentation level and finalizes cleanup for the
        inherited context manager.
        """
        MutableClass.untab()
        super().__exit__(*args)
    
    
    # ------------- #
    # !-- Print --! #
    # ------------- #
    
    @staticmethod
    def print(*args, **kwargs) -> None:
        """
        Print a message with optional indentation and mute control.

        Parameters
        ----------
        *args :
            Positional arguments forwarded to Python's built-in ``print``.
        **kwargs :
            Keyword arguments forwarded to ``print``. Two special keys are:

            ignore_tabs : bool, optional
                If ``True``, indentation is not applied to this print call.

            ignore_mute : bool, optional
                If ``True``, the message is printed even when muted.

        Notes
        -----
        Printing is suppressed when the class is muted, unless
        ``ignore_mute=True`` is provided.

        Examples
        --------
        >>> MutableClass.print("Hello")
        Hello

        >>> with MutableClass.tab():
        ...     MutableClass.print("Indented")
            > Indented
        """
        
        if "ignore_tabs" in kwargs:
            ignore_tabs = kwargs["ignore_tabs"]
            del kwargs["ignore_tabs"]
        else:
            ignore_tabs = False
            
        if "ignore_mute" in kwargs:
            ignore_mute = kwargs["ignore_mute"]
            del kwargs["ignore_mute"]
        else:
            ignore_mute = False
            
        if not 'flush' in kwargs:
            kwargs['flush'] = True
            
        if MutableClass.muted() and not ignore_mute:
            return
        
        if MutableClass.indent > 0 and not ignore_tabs:
            print(" " + ">" * MutableClass.indent, end=" ")
        print(*args, **kwargs)
        
    
    @staticmethod
    def par() -> None:
        """
        Print a blank line respecting mute settings.

        Equivalent to calling :meth:`print` with no arguments.
        """
        MutableClass.print(ignore_tabs = True)
    
    @staticmethod
    def create_spirit(spirit_message:str) -> Spirit:
        """
        Create and register a `Spirit` in the global print stack.

        This method solves a subtle output-formatting problem that occurs when
        certain classes (e.g., `Task`, `ProgressBar`) print *partial lines*
        without a trailing newline.

        For example, a `Task` prints:

            [~] Compute Stuff

        but intentionally does *not* add a newline yet, because it will later
        append timing information on the same line:

            [~] Compute Stuff (2.00s)

        The problem arises if something else calls ``print()`` during the Task.
        That print would continue on the same unfinished line:

            [~] Compute StuffDone

        which corrupts the intended display.

        To prevent this, classes that print partial lines register a `Spirit`.
        A `Spirit` represents “I have an unfinished line; before anything else
        prints, you must first flush me.” The global print stack (`pStack`)
        keeps track of all active spirits. Before each actual print, the
        stack emits whatever each spirit needs (usually a newline), ensuring
        that external prints do not collide with partial lines.

        Parameters
        ----------
        spirit_message : str
            The message associated with the spirit. This is typically what the
            spirit returns if it is queried or “killed”.

        Returns
        -------
        Spirit
            The created spirit instance. Classes that register the spirit may
            use this object to check later whether the spirit is still alive.

        Notes
        -----
        Spirits are not pushed to the stack when output is muted.
        """
        spirit = Spirit(spirit_message)
        if not MutableClass.muted():
            pStack.push(spirit)
        return spirit
        
    
    # ------------- #
    # !-- Utils --! #
    # ------------- #
    
    @staticmethod
    def go_root(file_in_root:str = None) -> str:
        """
        Change the current working directory to the root of the project. 
        This is determined by searching downwards for a specified file.
        """
        if file_in_root is None:
            file_in_root = oakley_config["root_file"]
        
        if MutableClass._initial_directory is None:
            MutableClass._initial_directory = os.getcwd()
            
        previous_dir = os.getcwd()
        while not os.path.exists(file_in_root):
            os.chdir('..')
            if previous_dir == os.getcwd():
                raise FileNotFoundError(f"Could not find root file '{file_in_root}' in any parent directory.")
            previous_dir = os.getcwd()
        MutableClass.cwd()
    
    @staticmethod
    def cwd() -> None:
        """
        Print the current working directory as a success style message.

        Notes
        -----
        Equivalent to calling ``Message(f"Current working directory: ...", '#')``.
        """
        MutableClass.print(f"{cstr('[#]').green()} Current working directory: {cstr(os.getcwd()):g}")
        
    
    @staticmethod
    def number(value:float) -> str:
        """
        A smart number formatter that adapts based on the size of the number.
        
        Examples
        --------
        >>> MutableClass.number(1234567)
        '1.23M'
        >>> MutableClass.number(1234)
        '1.23K'
        >>> MutableClass.number(12.3456)
        '12.3'
        >>> MutableClass.number(12) # if class is int
        '12'
        >>> MutableClass.number(-0.123456)
        '-0.123'
        >>> MutableClass.number(0.00123456)
        '1.23e-3'
        """
        # 1. Check wether integer by checking if number is equal to its int conversion
        if value == 0:
            return "0"
            
        abs_value = abs(value)
        
        if abs_value >= 1e15:
            return f"{value:.2e}"
        if abs_value >= 1e9:
            return f"{value/1e9:.2f}B"
        if abs_value >= 1e6:
            return f"{value/1e6:.2f}M"
        elif abs_value >= 1e3:
            return f"{value/1e3:.2f}k"
        elif abs_value >= 100:
            return f"{value:.0f}"
        elif abs_value >= 10:
            if isinstance(value, int):
                return f"{value:.0f}"
            return f"{value:.1f}"
        elif abs_value >= 1:
            if isinstance(value, int):
                return f"{value:.0f}"
            return f"{value:.2f}"
        elif abs_value >= 1e-2:
            return f"{value:.3f}"
        else:
            return f"{value:.2e}"
        
    
        
    
    @staticmethod
    def time(seconds:float) -> str:
        """
        Convert a duration in seconds into a formatted string.

        Parameters
        ----------
        seconds : float
            Duration in seconds.

        Returns
        -------
        str
            Formatted string of the form ``'hh:mm:ss'`` if the duration is
            at least one minute, else ``'X.XXXs'``.

        Examples
        --------
        >>> MutableClass.time(65)
        '00:01:05'
        >>> MutableClass.time(0.1234)
        '0.123s'
        """
        if seconds >= 60:
            seconds = int(seconds)
            hrs = seconds // 3600
            seconds %= 3600
            mins = seconds // 60
            seconds %= 60
            return f"{hrs:02d}:{mins:02d}:{seconds:02d}"
        else:
            return f"{seconds:.3f}s"
    
    @staticmethod
    def date() -> str:
        """
        Return the current date formatted as ``'YYYY-MM-DD'``.

        Returns
        -------
        str
            Current local date.
        """
        from datetime import datetime
        now = datetime.now()
        return now.strftime("%Y-%m-%d")
    
    @staticmethod
    def time_date() -> str:
        """
        Return the current local date and time formatted as
        ``'YYYY-MM-DD HH:MM:SS'``.

        Returns
        -------
        str
            Current timestamp.
        """
        from datetime import datetime
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def hi() -> None:
        """
        Prints a friendly greeting.
        """
        MutableClass.print("The Secret Commonwealth greets you!")

        
    
    
    
    
    
    
    # --------------- #
    # !-- Jupyter --! #
    # --------------- #
    
    def __repr__(self) -> str:
        """
        Return an empty representation.

        Notes
        -----
        This prevents objects from being displayed in Jupyter Notebook output
        cells, avoiding clutter.
        """
        return "" # avoid displaying in Notebooks, if a message is at the end of the cell
    
    

if __name__ == "__main__":
    # run these tests with python -m fancy_package.mutable_class
    MutableClass.print("This message will be printed.")
    MutableClass.mute()
    MutableClass.print("This message will not be printed.")
    MutableClass.unmute()
    MutableClass.print("This should be the second message.")
    
    with MutableClass.mute():
        MutableClass.print("This message will not be printed.")
        with MutableClass.mute():
            MutableClass.print("This message will not be printed.")
        MutableClass.print("This message will not be printed.")
    
    MutableClass.print("This should be the third message. Now, we test tabs.")
    MutableClass.tab()
    MutableClass.print("This should be indented.")
    MutableClass.untab()
    MutableClass.print("This should not be indented.")
    
    with MutableClass.tab():
        MutableClass.print("This should be indented.")
        with MutableClass.tab():
            MutableClass.print("This should be more indented.")
        MutableClass.print("This should be indented.")
    MutableClass.print("This should not be indented.")
    
    MutableClass.par()
    with MutableClass():
        MutableClass.print("This should be indented.")
        with MutableClass():
            MutableClass.print("This should be more indented.")
        MutableClass.print("This should be indented.")
        
    MutableClass.par()
    MutableClass.print("Testing time and date functions:")
    with MutableClass():
        MutableClass.print(f"Current date: {MutableClass.date()}")
        MutableClass.print(f"Current time and date: {MutableClass.time_date()}")
        MutableClass.print(f"123.456 seconds is {MutableClass.time(123.456)}")
    
    MutableClass.print("Done!")
    
    
    
        
        
        
    
