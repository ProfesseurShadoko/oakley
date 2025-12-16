


from .mutable_class import MutableClass
from .message import Message
from .fancy_string import cstr

import os
import gc
import sys


class MemoryView(MutableClass):
    """
    Display a short summary of the current process and system memory usage.

    Upon instantiation, `MemoryView` prints one line containing:
    - current process memory usage in GB,
    - total system memory,
    - percentage of used memory (color-coded).

    The class also provides helper methods for querying memory usage and
    a diagnostic function (:meth:`show`) for listing the most memory-heavy
    Python object types currently alive in the interpreter.

    Notes
    -----
    - Requires the ``psutil`` package.
    - Uses color conventions: green (<50%), yellow (<80%), red (≥80%).
    - Inherits indentation/mute behavior from :class:`MutableClass`.

    Examples
    --------
    >>> MemoryView()
    [M] Current memory usage: 1.23 GB / 15.92 GB (10%)

    Show the most memory-consuming Python object types (quite useless actually):

    >>> MemoryView.show(top=10)
    """
    
    def __init__(self):
        """
        Print a one-line summary of memory usage.

        Displays:
        - process memory usage (GB),
        - total system RAM (GB),
        - percentage usage with a color-coded indicator.

        Color logic:
            green   < 50%
            yellow  < 80%
            red     > 80%
        """
        tot_ram = self.get_memory_available() + self.get_memory_usage()
        memory_usage = self.get_memory_usage()/tot_ram
        color_letter = 'g' if memory_usage < 0.5 else 'y' if memory_usage < 0.8 else 'r'
        memory_usage_percent = f"{cstr(f'{memory_usage:.0%}'):{color_letter}}"
        
        self.print(
            f"{cstr('[M]').blue()} Current memory usage: {self.get_memory_usage():.2f} GB / {tot_ram:.2f} GB ({memory_usage_percent})"
        )
    
    
    def get_memory_usage(self) -> float:
        """
        Returns the current memory usage of the process in MB.
        """
        import psutil
        process = psutil.Process(os.getpid())
        memory = process.memory_info().rss / (1024 ** 3)  # in GB
        return memory
    
    def get_memory(self) -> float:
        """
        Returns the available memory in GB.
        """
        import psutil
        memory = psutil.virtual_memory().total / (1024 ** 3)  # in GB
        return memory
    
    def get_memory_available(self) -> float:
        """
        Returns the available memory in GB.
        """
        import psutil
        memory = psutil.virtual_memory().available / (1024 ** 3)  # in GB
        return memory
    
    @staticmethod
    def show(top:int=5):
        """
        Display the largest memory-consuming Python object types.

        This diagnostic tool inspects all live Python objects using ``gc`` and
        aggregates their memory usage by type. The `top` heaviest types are
        printed in descending order.

        Parameters
        ----------
        top : int, optional
            Number of object types to display. Default is 5.

        Notes
        -----
        - The function measures object sizes using ``sys.getsizeof``.
        - Output is printed inside a temporary `MemoryView` context so that
        indentation and formatting remain consistent.
        - Only Python object heap usage is inspected; external memory (NumPy
        arrays, GPU buffers, C extensions) may not be included.

        Examples
        --------
        >>> MemoryView.show(top=3)
        1. Type: dict, Total Size: 42.50 MB
        2. Type: list, Total Size: 21.30 MB
        3. Type: str,  Total Size: 12.80 MB
        """
        gc.collect()
        all_objects = gc.get_objects()
        
        # get all individual types and their total memory usage
        type_memory = {}
        for obj in all_objects:
            obj_type = type(obj)
            try:
                obj_size = sys.getsizeof(obj)
            except TypeError:
                obj_size = 0
            type_memory[obj_type] = type_memory.get(obj_type, 0) + obj_size
        
        # sort by memory usage
        sorted_types = sorted(type_memory.items(), key=lambda x: x[1], reverse=True)
        
        # dispaly the N first
        if top > len(sorted_types):
            top = len(sorted_types)
            
        with MemoryView():
            for i, (obj_type, total_size) in enumerate(sorted_types[:top], 1):
                size_mb = total_size / (1024 ** 2)
                MemoryView.untab()
                MemoryView.print(f" {i}. Type: {cstr(obj_type.__name__):bb}, Total Size: {size_mb:.2f} MB")
                MemoryView.tab()
    
 
class DateTime(MutableClass):
    """
    Display the current date and time in a formatted style.

    When instantiated, prints a one-line timestamp of the form:

        [D] YYYY-MM-DD HH:MM:SS

    Examples
    --------
    >>> DateTime()
    [D] 2025-03-19 14:22:11
    """
    
    def __init__(self):
        """
        Print the current date and time.

        Uses :meth:`MutableClass.time_date` to format the timestamp as
        ``YYYY-MM-DD HH:MM:SS``.
        """
        self.print(f"{cstr('[D]').magenta()} {self.time_date()}")
        

if __name__ == "__main__":
    from .message import Message
    
    with Message("Displaying memory usage:"):
        MemoryView()
        
    Message.par()
    with Message("Displaying current date and time:"):
        DateTime()