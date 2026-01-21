
from .fancy_string import cstr
from .mutable_class import MutableClass
import time
from .task import Task
from .message import Message
from .status import MemoryView
from .xconfig import oakley_config
from typing import Literal
from .print_stack import in_notebook


class ProgressBar(MutableClass):
    """
    Lightweight iterator wrapper that prints a dynamic progress bar with
    estimated remaining time.

    `ProgressBar` is designed to be used directly in iteration loops:

    >>> for x in ProgressBar(range(100)):
    ...     ...

    The bar updates in-place by printing partial lines (using ``end='\\r'``),
    meaning that the current line is overwritten continuously instead of
    producing new lines. To avoid interference from other printing functions
    during the update, the progress bar registers a `Spirit` that ensures
    the terminal state is kept consistent (see the documentation of
    :meth:`MutableClass.create_spirit` for details).

    Parameters
    ----------
    lst : iterable
        The iterable or iterator over which to loop.
    size : int, optional
        Length of the iterable. Only required when ``lst`` does not
        implement ``__len__`` (e.g., when it is a generator). If omitted,
        the progress bar will attempt to convert the iterable to a list.

    Notes
    -----
    - The progress bar prints at most every 0.05 seconds to avoid excessive
      terminal updates.
    - Printing occurs on a single line using carriage returns (``'\\r'``).
    - A `Spirit` is always active during iteration to prevent unrelated
      printing from corrupting the progress bar display.

    Examples
    --------
    Basic usage:

    >>> for _ in ProgressBar(range(50)):
    ...     time.sleep(0.01)

    Using `whisper` to print a message without breaking the bar:

    >>> for i in ProgressBar(range(100)):
    ...     if i == 50:
    ...         ProgressBar.whisper("Halfway there!")
    """
    
    
    current_instance = None

    
    def __init__(self, lst, size:int=None) -> None:
        """
        Initialize a new progress bar over the given iterable.

        Parameters
        ----------
        lst : iterable
            The iterable or iterator object (e.g., list, range, enumerate,
            zip, numpy array).
        size : int, optional
            Length of the iterable. Required only if `lst` does not implement
            ``__len__``. If omitted and length cannot be determined, the
            iterable is converted to a list, which may be expensive.

        Raises
        ------
        AssertionError
            If the provided object is not iterable.
        """
        super().__init__()
        ProgressBar.current_instance = self
        
        if size is None:
            if not hasattr(lst,'__len__'):
                ProgressBar.print(cstr("[!]").red(),"Warning: unable to iterate over the object of type {type(lst)}. This may be because it is an iterator without a __len__ magic method. In this case, you can provide an argument 'size'.")
                ProgressBar.print(cstr("[!]").red(),"Trying to convert to list (which might be time and memory consuming)...")
                lst = list(lst)
                
            self.max = len(lst)
        else:
            self.max = size
        
            
        assert hasattr(lst,'__iter__'), "The object provided is not iterable."
        self.list = lst.__iter__()
        
        self.count = 0
        self.start_time = time.time()
        
        self.previous_print = ""
        self.previous_print_time = -999 # we want to avoid printing too often!
        self.spirit = self.create_spirit("") # always create default spirit
        
        # keep track of the time of the last 10 steps
        self.time_of_steps = []
        
        # keep track of this for the spinners
        self.print_count = 0
        self.previous_spinner_time = -999
        
        
    # ------------------------- #
    # !-- Iterator Protocol --! #
    # ------------------------- #
        
    
    def __iter__(self) -> 'ProgressBar':
        return self
    
    def __next__(self):
        if self.max==0:
            raise StopIteration()
        
        self.time_of_steps.append(time.time())
        # keep only last 20 steps
        if len(self.time_of_steps)>20:
            self.time_of_steps.pop(0)
        
        self.show()
        self.count += 1 # update the progress
        
        try:
            return next(self.list)
        except StopIteration:
            self.spirit.kill() # remove the spirit from the print stack
            ProgressBar.current_instance = None # delete the progressbar, as the loop has ended
            self.print(ignore_tabs=True) # go to next line
            raise(StopIteration())
        
    
    # -------------- #
    # !-- Header --! #
    # -------------- #
    
    def _get_header(self, terminal_width:int) -> str:
        """
        Returns the header part of the progress bar, which can be either
        a percentage or a spinner if the max is unknown.
        """
        if len(oakley_config["spinner"]) == 0 or self.count == self.max:
            progress_percent = f"{(int(self.count/self.max*100)):02d}%" if self.max>0 and self.count < self.max else "%"
            header = cstr(f"[{progress_percent}]")
        else:
            header = cstr(f"[{oakley_config['spinner'][self.print_count % len(oakley_config['spinner'])]}]")
        return header.red() if self.count < self.max else header.green()
    
    def _get_bar(self, terminal_width:int) -> str:
        
        if self.count == self.max:
            return ""
        
        # we assume that header + stats take 50 characters at most
        bar_width = terminal_width - 50
        
        if bar_width < 5:
            return ""
        
        bar_width = min(25, bar_width)
        bar_car = "━"
        n_bars_completed = int(bar_width * self.count / self.max)
        n_bars_remaining = bar_width - n_bars_completed
        if n_bars_completed == 0 or n_bars_remaining == 0:
            sep_char = ""
        else:
            sep_char = " "
            if n_bars_completed == 0:
                n_bars_remaining += 1
            if n_bars_remaining == 0:
                n_bars_completed += 1
            
        bar = cstr(bar_car*n_bars_completed).green() + sep_char + cstr(bar_car*n_bars_remaining).red()
        return bar
    
    def _get_stats(self, terminal_width:int) -> str:
        
        # 1. Compute elapsed time
        if self.time_of_steps == []:
            elapsed_time = time.time() - self.start_time # should not happen if you do for i in ProgressBar(...) because next is called right away.
        else:
            elapsed_time = self.time_of_steps[-1] - self.start_time # self.time_of_steps can never be empty here
        
        elapsed_time_str = ProgressBar.time(elapsed_time)
        
        # 2. Compute the average it/s (as average over last steps)
        if self.count == 0:
            it_per_s = "?"
        else:
            n_steps = len(self.time_of_steps)-1
            delta_time = self.time_of_steps[-1] - self.time_of_steps[0]
            it_per_s = it_per_time = n_steps/delta_time
            
            # choose units
            it_per_time_unit = "it/s"
            if it_per_time < 2:
                it_per_time = it_per_time * 60 # it per minute
                it_per_time_unit = "it/min"
            if it_per_time < 2:
                it_per_time = it_per_time * 60 # it per hour
                it_per_time_unit = "it/h"
            it_per_time_str = ProgressBar.number(it_per_time) + f" {it_per_time_unit}"
        
        # 3. Compute remaining time
        if self.count==0 or self.max==0:
            remaining_time_str = "?"
        else:
            n_steps_remaining = self.max - self.count
            remaining_time_sec = n_steps_remaining / it_per_s
            remaining_time_str = ProgressBar.time(remaining_time_sec)
        
        # 4. Get progress count/max
        progress_count_str = f"{ProgressBar.number(self.count)}/{ProgressBar.number(self.max)}" if self.max>0 else "?"
        
        # 5. Combine all stats
        if self.count == 0:
            return ""
        
        if terminal_width < 40:
            return f"[{elapsed_time_str} > {remaining_time_str}]" # len = 23 (including header)
        if terminal_width < 50:
            return f"[{elapsed_time_str} > {remaining_time_str}, {it_per_time_str}]" # len = 34 (including header)
        return f"[{elapsed_time_str} > {remaining_time_str}, {it_per_time_str}, {progress_count_str}]" # len = 42 (including header)
        
    
    
    # ---------------------------- #
    # !-- Progress Bar Display --! #
    # ---------------------------- #
    
    def show(self) -> None:
        """
        Displays the current progress. The progress shall be displayed as
        the combination of three parts:
         - a header ([%] for instance or [23%]) or spinner
         - a bar showing progress
         - numbers [23/100, elapsed time > remaining time, it/s]
        
        At the beginning of each call of the show function, some space 
        is allowated to each part, so that the progress bar does not
        exceed the terminal width. This space is re-evaluated at each call
        of the show function, so that if the terminal is resized, the progress
        bar still fits in the terminal.
        """
        
        # 1. Check if we should print something
        
        current_time = time.time()
        # if we have printed something less than 0.05s ago, we skip this print
        # unless this is the very last print!
        delta_time = current_time - self.previous_print_time
        if delta_time < 0.05 and self.count < self.max:
            return
        if self.count == self.max:
            time.sleep(0.05) # wait a bit to ensure the last print is after 0.05s from previous one
        
        # 2. Prepare the next print
        terminal_width = self._get_terminal_width() # between 30 and 75
        
        header = self._get_header(terminal_width)
        bar = self._get_bar(terminal_width)
        numbers = self._get_stats(terminal_width) # all separated by " "
        
        next_print = " ".join([item for item in [header, bar, numbers] if item])
        self.previous_print_time = time.time()
        
        # we are printing comething with "\r", therefore we need a spirit so that someone else doesn't interrupt us
        self.spirit.kill()  # remove the spirit from the print stack
        self._print_pb(
            next_print,
            newline=False
        )
        self.spirit = self.create_spirit("\n")
            
    
    def _print_pb(self, msg:str, newline:bool = True) -> None:
        """
        Prints if and only if the message is different from the previous one.
        Prints enough white spaces to fill the line (and erase previous content).
        
        If not newline, then the print ends with '\r' instead of '\n'.
        """
        if msg != self.previous_print:
            n_to_erase = cstr(self.previous_print).length()
            n_to_erase = min(self._get_terminal_width(min_value=0, margin=5, _ignore_config=True), n_to_erase)
            self.print("\r", end="", ignore_tabs=True) # go back to the beginning of the line
            n_spaces = max(0, n_to_erase - cstr(msg).length())
            self.print(msg + n_spaces*" ", end="\n" if newline else "") # go back to the beginning of the line and erase previous content
            
            # 3. Update previous print
            self.previous_print = msg
            self.previous_print_time = time.time()
            
            # 4. Check wether we wan't to update the spinner (at most 10 times per second)
            if self.previous_print_time - self.previous_spinner_time > 0.1:
                self.previous_spinner_time = self.previous_print_time
                self.print_count += 1
            
            
    def _get_terminal_width(self, margin:int = 5, min_value:int=25, _ignore_config:bool = False) -> int:
        """
        Returns the current terminal width in number of characters.
        """
        import shutil
        terminal_size = shutil.get_terminal_size((999, 20)).columns
        
        # account for provided terminal_size in config
        if oakley_config["terminal_width"] > 0 and not _ignore_config:
            terminal_size = min(terminal_size, oakley_config["terminal_width"]) # if terminal size lower than provided, keep the low one

        n_tab_chars = ProgressBar.indent + 2 if ProgressBar.indent > 0 else 0
        # Also, if the terminal size is lower than 30, we set is to 30. And let's keep an additional 5 characters of margin.
        return max(min_value, terminal_size - n_tab_chars - margin)
            
        
        
    # ------------- #
    # !-- Utils --! #
    # ------------- #   
        
    @staticmethod
    def whisper(msg:str):
        """
        Print a short message without disrupting the progress bar display.

        A whisper temporarily clears the displayed progress bar, prints the
        message aligned to the same width, and then restores the bar.

        Parameters
        ----------
        msg : str
            The message to display.

        Notes
        -----
        Whispered messages are intended for transient feedback (“Halfway
        there!”, “Loading…”, etc.) that does not break the flow of the bar.

        Examples
        --------
        >>> for i in ProgressBar(range(100)):
        ...     if i == 50:
        ...         ProgressBar.whisper("Halfway there!")
        """
        if ProgressBar.current_instance is None: # should not happen, I guess whisper is always inside a progressbar loop
            header = cstr("[%]").green()
            return ProgressBar.print(header + " " + msg)

        # 1. Erase the current progress bar
        ProgressBar.current_instance.spirit.kill()  # remove the spirit from the print stack
        header = cstr("[%]").red()
        to_print = header + " " + msg
        ProgressBar.current_instance._print_pb(to_print)
        ProgressBar.current_instance.previous_print_time = -999 # so that it prints again right away
        ProgressBar.current_instance.show()
        
        
    # --------------- #
    # !-- Configs --! #
    # --------------- #
        
    @staticmethod
    def set_size(progressbar_size: Literal["minimal", "small", "medium", "large", "default"] = "default"):
        """
        Changes the display of progressbar, from simplest (minimal) to most
        detailed (default). Only default has an actual progress bar. 
        
        The actual terminal width is used anyway, and the bar still adapts to it 
        if the terminal size is too small for the chosen size.
        
        Parameters
        ----------
        progressbar_size : {'minimal', 'small', 'medium', 'large', 'default'}, optional
            The desired size of the progress bar display.
            - 'minimal': `[03%] [0.061s > 1.974s]`
            - 'small': `[03%] [0.061s > 1.956s, 49.6 it/s]`
            - 'medium': `[12%] [0.244s > 1.790s, 49.2 it/s, 12/100]`
            - 'large': `[10%] ━ ━━━━━━━━━ [0.202s > 1.817s, 4.95 it/s, 1/10]` (10% is exactly one subdivision of the bar)
            - 'default': `[10%] ━━ ━━━━━━━━━━━━━━━━━━━━━━━ [0.201s > 1.808s, 4.98 it/s, 1/10`
            
        Notes
        -----
        Different version of Jupyter Notebook may behave differently due to a different way
        of counting caracters. If so, import `config` from `oakley.config` and change the 
        `"terminal_width"` argument (try different positive integers, representing the 
        maximal number of caracters displayed by the colorbar). Negative integer means
        `default`.
        """
        assert progressbar_size in ["minimal", "small", "medium", "large", "default"], "Invalid progressbar size. Choose among 'minimal', 'small', 'medium', 'large', 'default'."
        
        # 1. translate argument to terminal width
        oakley_config["terminal_width"] = {
            "minimal": 30,
            "small": 50,
            "medium": 60,
            "large": 68,
            "default": -1
        }[progressbar_size]

    @staticmethod
    def set_spinner(spinner_list:list|int|str = 0):
        """
        Sets the spinner characters used in progress bars.

        Parameters
        ----------
        spinner_list : list of str or str or int, optional
            A list of strings representing the spinner characters to cycle
            through during progress updates. If an integer is provided, it
            selects a predefined spinner preset. If a string, the spinner
            is defined by the lsit fo characters.

        Notes
        -----
        The spinner will cycle through the provided characters during
        progress updates.   
        
        Using non standard characters may lead to display issues in some
        terminals (for instance for spinner_list = 2, 3, 4, 5).    
        """
        if isinstance(spinner_list, int):
            spinner_lists = {
                0: [],
                1: ['|', '/', '-', '\\'],
                2: ['◐', '◓', '◑', '◒'],
                3: ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"],
                4: ["◴","◷","◶","◵"],
                5: ["◜", "◝", "◞", "◟"]
            }
            assert spinner_list in spinner_lists, f"Invalid spinner preset index {spinner_list}. Choose among {list(spinner_lists.keys())}."
            spinner_list = spinner_lists[spinner_list]
        
        if isinstance(spinner_list, str):
            spinner_list = list(spinner_list)
        assert all(isinstance(s, str) for s in spinner_list), "All spinner elements must be strings."
        oakley_config["spinner"] = spinner_list
        
        
    def update(self):
        """
        Manually updates the progress bar display.

        This method can be called to refresh the progress bar display
        outside of the standard iteration flow.

        Examples
        --------
        >>> pb = ProgressBar(range(100))
        >>> for i in range(50):
        ...     pd.upate() # shows progress
        ... for i in range(50):
        ...     pb.update()
        """
        try:
            out = next(self)
        except StopIteration:
            return
        return out
        

if __name__ == '__main__':
    
    
    # 1. Test in normal conditions    
    with Message("Computing something heavy"):
        for i in ProgressBar(range(100)):
            time.sleep(0.05)
    
    # 2. Test when super fast
    with Message("Computing something super fast"):
        for i in ProgressBar(range(10_000)):
            time.sleep(5e-4)
            
    Message.par()
    
    # 3. Test whisper
    with Message("Testing whisper"):
        for i in ProgressBar(range(100)):
            time.sleep(0.03)
            if i==50:
                ProgressBar.whisper("Halfway there!")
            if i==70:
                Message("Messages work as well")
            if i==90:
                print("And the standard 'print' as well")
                
    # 4. Testing other prints
    with Message("Testing normal prints"):
        for i in ProgressBar(range(100)):
            time.sleep(0.03)
            if i==50:
                print("This is a normal print.")
    
    Message.par()
    
    # 5. Testing various termial widths
    class LengthMeasuringPB(ProgressBar):
        
        
        
        def __init__(self, terminal_width:int, *args, **kwargs):
            self.terminal_width = terminal_width
            super().__init__(*args, **kwargs)
            self.print_of_max_length = ""
            
            
        def __next__(self):
            if cstr(self.previous_print).length() > cstr(self.print_of_max_length).length():
                self.print_of_max_length = self.previous_print
            
            try:
                return super().__next__()
            except StopIteration:
                with Message(f"Max print length was {cstr(cstr(self.print_of_max_length).length()):c} (max allowed {self.terminal_width})"):
                    Message.print(f"The print was: '{self.print_of_max_length}'")
                raise(StopIteration())
            
        def _get_terminal_width(self, *args, **kwargs):
            return self.terminal_width  
                
    
    for width in [30, 40, 50, 70, 80]:
        with Message(f"Testing terminal width = {width}"):
            for i in LengthMeasuringPB(width, range(100)):
                time.sleep(0.02)
        
        
    Message.par()
    with Message("Testing changing terminal size"):
        Message.print("During the following loop, please resize your terminal window to see how the progress bar adapts.")
        for i in ProgressBar(range(1000)):
            time.sleep(0.02)
            
            
    # 6. Real cas escenario
    n_iters = 5000
    time_per_iter = 600 / n_iters # 10 minutes total
    with Message("Processing data..."):
        time_start = time.time()
        for i in ProgressBar(range(n_iters)):
            time.sleep(time_per_iter)
            
            if time.time() - time_start > 20:
                Message("Let's not go any further and exit now!", "?")
                break
            
            
            
    
