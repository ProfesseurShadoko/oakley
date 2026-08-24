
from .fancy_string import cstr
from .fancy_context_manager import FancyCM
from .print_stack import pStack, Spirit
from .xconfig import oakley_config
import os

import runpy
import sys
import shlex # to split a command string into list of arguments



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
    capture_output_count = 0
    current_capture = {} # dict capture level -> captured string
    
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
    

    # --------------- #
    # !-- Capture --! #
    # --------------- #

    @staticmethod
    def capture() -> FancyCM:
        """
        Records everything that gets printed by `MutableClass.print` into an internal string buffer, which can be retrieved with :meth:`pop`.
        If the class is muted, the capture won't record outputs.
        """
        MutableClass.capture_output_count += 1

        class CaptureContext(FancyCM):
            def __exit__(self, *args):
                MutableClass.stop_capture()
                super().__exit__(*args)

        return CaptureContext()
    
    @property
    def capture_output(self) -> bool:
        return MutableClass.capture_output_count > 0
    
    @staticmethod
    def _add_to_capture(message: str) -> None:
        """
        Adds a string to the correct capture buffer(s) based on the current capture level.
        """
        # remove ANSI color codes from message
        message = cstr(message).strip_ansi()
        if MutableClass.capture_output:
            level = MutableClass.capture_output_count
            for l in range(1, level + 1):
                if l not in MutableClass.current_capture:
                    MutableClass.current_capture[l] = ""
                MutableClass.current_capture[l] += message

    @staticmethod
    def stop_capture() -> None:
        """
        Stop capturing output. Does not clear the current capture buffer.
        """
        MutableClass.capture_output_count -= 1
    
    @staticmethod
    def pop() -> str:
        """
        Retrieves the current captured output. The capture must have been stopped to retrieve the output,
        otherwise the output will be empty.
        """
        captured = MutableClass.current_capture.get(MutableClass.capture_output_count + 1, "")
        # delete every key in the dict that is higher than the current capture level, to clear all nested captures as well
        for key in list(MutableClass.current_capture.keys()):
            if key > MutableClass.capture_output_count:
                del MutableClass.current_capture[key]
        return captured

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
            Keyword arguments forwarded to ``print``. Three special keys are:

            ignore_tabs : bool, optional
                If ``True``, indentation is not applied to this print call.

            ignore_mute : bool, optional
                If ``True``, the message is printed even when muted.
            
            ignore_capture : bool, optional
                If ``True``, the message is not recorded in the capture buffer even if capture mode is active. Usefull for progress bars.


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

        # 1. Handle special kwargs
        ignore_tabs = kwargs.get("ignore_tabs", len(args) == 0)
        ignore_mute = kwargs.get("ignore_mute", False)
        ignore_capture = kwargs.get("ignore_capture", False)
        end = kwargs.get("end", "\n")
        sep = kwargs.get("sep", " ")
        kwargs["flush"] = kwargs.get("flush", True)


        # delete the special keys from kwargs if they exist
        if "ignore_tabs" in kwargs:
            del kwargs["ignore_tabs"]
        if "ignore_mute" in kwargs:
            del kwargs["ignore_mute"]
        if "ignore_capture" in kwargs:
            del kwargs["ignore_capture"]

        # 2. Handle mute (just return)
        if MutableClass.muted() and not ignore_mute:
            return
        
        # 3. Simply print if without tabs
        if MutableClass.indent == 0 or ignore_tabs:
            if MutableClass.capture_output and not ignore_capture:
                MutableClass._add_to_capture(sep.join(str(arg) for arg in args) + end)
            print(*args, **kwargs)
            return
        
        # 4. Handle \n to keep indentation for multiline prints
        message = sep.join(str(arg) for arg in args)
        lines = message.split("\n") # this is of length at least 1

        if "sep" in kwargs:
            del kwargs["sep"] # we already used it!

        if not ignore_tabs:
            # build the output to print by adding tabs to each (non-empty) line
            for i in range(len(lines)):
                if lines[i].strip() != "" or len(args) == 1: # match par() function, but ir print("") still prints tabs (but print() doesn't)
                    lines[i] = " " + ">" * MutableClass.indent + " " + lines[i]

        if MutableClass.capture_output and not ignore_capture:
            MutableClass._add_to_capture("\n".join(lines) + end)
        
        print(*lines, **kwargs, sep="\n")

    
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


    def _get_terminal_width(self, margin:int = 5, min_value:int=25, _ignore_config:bool = False) -> int:
        """
        Returns the current terminal width in number of characters.
        """
        import shutil
        terminal_size = shutil.get_terminal_size((999, 20)).columns
        
        # account for provided terminal_size in config
        if oakley_config["terminal_width"] > 0 and not _ignore_config:
            terminal_size = min(terminal_size, oakley_config["terminal_width"]) # if terminal size lower than provided, keep the low one

        n_tab_chars = self.indent + 2 if self.indent > 0 else 0
        # Also, if the terminal size is lower than 30, we set is to 30. And let's keep an additional 5 characters of margin.
        return max(min_value, terminal_size - n_tab_chars - margin)
    
    
    # ------------------ #
    # !-- Subprocess --! #
    # ------------------ #
    
    @staticmethod
    def subprocess(python_file:str, args:list|str = "", mute:bool = False) -> None:
        """
        Run a Python script as a subprocess with `runpy` (avoids
        multpiple imports and allows access to `cli.out`).
        
        Parameters
        ----------
        python_file : str
            The path to the Python file to run as a subprocess.
        args : list | str, optional
            Arguments to pass to the subprocess. Can be a list of strings or a single
            string. Mustn't include the python file itself, nor the "python" command.
            If a list, will be made into a string by joining with spaces.
            Used to create `sys.argv` for the subprocess. Default is an empty string (no arguments).
        """
        
        # 1. Check arguments
        assert os.path.isfile(python_file), f"File '{python_file}' does not exist."
        assert python_file.endswith(".py"), f"File '{python_file}' is not a Python file."
        python_file = os.path.abspath(python_file)
        
        # 2. Prepare arguments
        if isinstance(args, list):
            args = " ".join(args)
        command = f"{python_file} {args}"
        command_args = shlex.split(command)
        
        # 3. Save sys.argv and set up new sys.argv for the subprocess
        original_argv = sys.argv
        original_cwd = os.getcwd()
        sys.argv = command_args
        
        # 4. Run the subprocess using runpy
        try:
            if mute:
                MutableClass.mute() # this mutes everyone
            
            try:
                runpy.run_path(python_file, run_name="__main__")
            except SystemExit as e:
                if not e.code in (0, None):
                    raise RuntimeError(f"Subprocess '{cstr(python_file):r}' exited with code {cstr(e.code):r}.")
            
            
        except Exception as e:
            raise RuntimeError(f"Error running subprocess '{cstr(python_file):r}'") from e
        finally:
            if mute:
                MutableClass.unmute()
            sys.argv = original_argv
            os.chdir(original_cwd)
        
        
        
        
        

        
    
    
    
    
    
    
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
    
    with MutableClass():
        MutableClass.print("This should be indented.")
        with MutableClass():
            MutableClass.print("This should be more indented.")
        MutableClass.print("This should be indented.")
        
    MutableClass.print("Testing time and date functions:")
    with MutableClass():
        MutableClass.print(f"Current date: {MutableClass.date()}")
        MutableClass.print(f"Current time and date: {MutableClass.time_date()}")
        MutableClass.print(f"123.456 seconds is {MutableClass.time(123.456)}")
    
    MutableClass.print("Testing capture:")
    with MutableClass.capture():
        MutableClass.print("This is captured is the base capture frame.")
        MutableClass.print("This is also captured in the base capture frame.")
        with MutableClass.tab():
            MutableClass.print(f"This is still capture in the base frame\nbut with tabs and {cstr('color'):y}.")
            with MutableClass.capture():
                MutableClass.print("This is captured in the first nested capture frame, and in the base frame as well.")
                MutableClass.print("This should not get caputred.\nNot at all.",1,2, ignore_capture=True)
            nested_capture = MutableClass.pop()
        MutableClass.print("Back to the base capture frame.", "Here is my favourite number", 17, sep = "\n")
        MutableClass.print("This should not be captured.", ignore_capture=True)
    MutableClass.print()
    MutableClass.print("Captured output from the base frame:")
    MutableClass.print(repr(MutableClass.pop()))
    MutableClass.print("Captured output from the nested frame:")
    MutableClass.print(repr(nested_capture))
        
    
    MutableClass.print("Done!")
    
    
    
        
        
        
    
