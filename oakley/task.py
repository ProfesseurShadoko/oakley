
from .mutable_class import MutableClass
from .fancy_string import cstr
from .fancy_context_manager import FancyCM   
from typing import Literal
import time
from .print_stack import in_notebook, _notebook_is_unknown
from .message import Message
import traceback

class Task(MutableClass):
    """
    A context manager for timing and displaying the execution of a task.

    `Task` prints a header indicating that the task has started, executes the
    enclosed code block, and then prints either a completion message or an
    "aborted" message depending on whether an exception occurred.

    Timing information is automatically appended when the task completes:
    
        [~] Compute stuff (2.003s)

    Like `ProgressBar`, this class uses a `Spirit` to guard partial-line output
    ensuring that other printing in the meantime does not
    corrupt the task’s output formatting.

    Parameters
    ----------
    msg : str
        The descriptive message for the task.

    
    Notes
    -----
    - `Task` must be used as a context manager using ``with Task(...):``.
    - If an exception occurs inside the ``with`` block, the task is marked
      as aborted and the exception is re-raised after printing diagnostics.
    
    Examples
    --------
    Basic usage:

    >>> with Task("Compute something heavy"):
    ...     expensive_function()

    """
    
    running_tasks = []
    last_task_runtime = None
    
    def __init__(self, msg:str, notify:bool = False, meta:bool = False) -> None:
        """
        Initialize a new task wrapper.

        Parameters
        ----------
        msg : str
            The message describing the task being executed.
        notify : bool, optional
            Whether to send a notification to the discord server when the task completes or is aborted. Default is False.
            Send the documentation of the `Message.send` method for more information on how to setup `oakley` to enable
            notifications.
        meta : bool, optional
            Whether to include metadata (hostname, command, directory) in the notification message. Default is False.
            Unused if `notify` is False.
        """
        self.msg = msg
        self.spirit = self.create_spirit("") # placeholder spirit
        self.notify = notify
        self.meta = meta

    def _complete(self) -> None:
        Task.last_task_runtime = time.time() - self.start_time
        
        if not self.spirit.is_alive():
            self.print(
                cstr('[~]').blue(), "Task completed after:", cstr(self.time(Task.last_task_runtime)).blue()
            )
        else:
            self.spirit.kill()
            self.print(
                f" ({cstr(self.time(time.time()-self.start_time)).blue()})", ignore_tabs=True
            )
        
        if self.notify:
            Message.send(
                "\n".join([
                    f'task: {self.msg}',
                    'status: completed',
                    f'runtime: {self.time(Task.last_task_runtime)}'
                ]),
                meta=self.meta
            )
    
    def _abort(self, exc_type, exc_value, exc_tb) -> None:        
        if self.spirit.is_alive():
            Task.print(self.spirit.kill(), end='', ignore_tabs=True) # go to new line immediately

        self.print(
            cstr('[!]').red(), "Task aborted after:", cstr(self.time(time.time()-self.start_time)).red()
        )

        if self.notify:
            Message.send(
                "\n".join([
                    f'task: {self.msg}',
                    'status: aborted',
                    f'runtime: {self.time(time.time()-self.start_time)}',
                    f'exception: {exc_type.__name__}: {exc_value}'
                ]),
                meta=self.meta
            )
            # convert traceback to string
            tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
            Message.send(
                tb_str, meta=False
            )
        
        # assert self.__class__.running_tasks.pop() == self, "The task was not removed from the list of running tasks. This should not happen."
    
    
    #######################
    ### Context Manager ###
    #######################
    
    def __enter__(self):
        self.__class__.running_tasks.append(self)
        self.print(
            cstr('[~]').blue(), self.msg, end=''
        )
        self.spirit = self.create_spirit("\n")
        
        # if we are in an unknown environment, always go to new_line
        if in_notebook and _notebook_is_unknown:
            Task.print(self.spirit.kill(), end='', ignore_tabs=True) # go to new line immediately
        
        self.start_time = time.time()
        super().__enter__() # add to the indentation level

        # notification for task start
        if self.notify:
            Message.send(
                "\n".join([
                    f'task: {self.msg}',
                    'status: started'
                ]), meta=self.meta
            )
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self._complete()
        else:
            self._abort(exc_type, exc_value, traceback)
        super().__exit__(exc_type, exc_value, traceback) # rmeoves the indentation level and handles the exception if any
        
    
    
        


if __name__ == '__main__':
    
    from .message import Message
    Message("Testing task class.")
    
    with Task("Computing something heavy"):
        time.sleep(1)
        Message.print("Halfway there...")
        time.sleep(1)
    
    with Task("Computing many things"):
        for i in range(3):               
            with Task(f"Computing thing {i+1}"):
                time.sleep(1)
            Message(f"Computation {i+1}/3 successful", "#")

    with Task("Heavy computing but successful", notify=True):
        time.sleep(1)
    with Task("Heavy computing but broken", notify=True):
        time.sleep(1)
        x = 1/0
