

import sys


class Spirit:
    """
    A Spirit is a messenger who contains a string to be printed later. 
    In order to prevent multiple prints, the Spirit must be killed
    in order to retrieve the message.
    """
    
    def __init__(self, message: str):
        """
        Initializes the Spirit with a message.
        """
        self.message = message
        self.alive = True
    
    def kill(self) -> str:
        """
        Kill the spirit, and return its message. The next time the Spirit is killed, he will return ""
        """
        out_msg = self.message
        self.message = ""
        self.alive = False
        return out_msg
    
    def is_alive(self) -> bool:
        """
        Checks whether the spirit is still alive.
        """
        return self.alive
    
    

# ------------------------------------- #
# !-- Handle Notebook compatibility --! #
# ------------------------------------- #    

Base = type(sys.stdout)

try:
    from IPython import get_ipython
    shell = get_ipython()
    in_notebook = (shell is not None)
    _notebook_is_unknown = (shell.__class__.__name__ != "ZMQInteractiveShell")
except Exception:
    in_notebook = False
    _notebook_is_unknown = False

        


class PrintListener(Base):
    """
    The PrintListener collects the spirits that are pushed onto it, and prints them in chronological order.
    Each time the standard `print` function is called, the messages of the spirits are printed first, and 
    the spirits are killed.
    """
    
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.secret_commonwealth:list[Spirit] = [] # we put spirits inside
        
        # copy all the attributes of the original stdout to pStack, in case it has any special behavior
        for k, v in original_stdout.__dict__.items():
            if not hasattr(self, k):
                setattr(self, k, v)
        
    def write(self, message):
        """
        Simply prints the message as 'print' would have done, but first displays anything that the Spirits have to say.
        """
        # display anything that is in the stack first
        while not self.empty():
            msg = self.pop()
            self.original_stdout.write(msg)
        self.original_stdout.write(message)
    
    def flush(self):
        """
        Just some necessary boilerplate for sys.stdout replacement.
        """
        self.original_stdout.flush()
        
    
    # -------------------- #
    # !-- Spirit Logic --! #
    # -------------------- #
        
    def push(self, spirit:Spirit):
        """
        Push a spirit onto the PrintListener's stack.
        """
        assert isinstance(spirit, Spirit), "Can only push Spirit instances onto the PrintStack."
        self.secret_commonwealth.append(spirit)
    
    def pop(self) -> str:
        """
        Get te next spirit and kills it. Returns its message. The dead spirit is removed from the stack.
        """
        first_spirit = self.secret_commonwealth.pop(0)
        return first_spirit.kill()
    
    def empty(self) -> bool:
        """
        Check whether any spirit is still in the Stack.
        """
        return len(self.secret_commonwealth) == 0
    
    # ----------------- #
    # !-- TTY Logic --! #
    # ----------------- #
    
    def isatty(self):
        return self.original_stdout.isatty()

    @property
    def encoding(self):
        return self.original_stdout.encoding
    
    def fileno(self):
        return self.original_stdout.fileno()
    
    
    


    
 
pStack = PrintListener(sys.stdout)

if not (in_notebook and _notebook_is_unknown):
    sys.stdout = pStack # I know it works for Jupyter and normal python. However, it does not work in collab. So we disable it there.







if __name__ == "__main__":
    
    class PrintInTwoParts:
        
        def __init__(self):
            self.message1 = "Computing... "
            self.message2 = "Done!"
        
        def print1(self):
            print(self.message1, end="")
        
        def print2(self):
            print(self.message2)
    
    
    # This works fine
    p = PrintInTwoParts()
    p.print1()
    p.print2()
    
    # But if there is a print statement inbetween, it messes up the output
    p = PrintInTwoParts()
    p.print1()
    print("Hello world!")
    p.print2()
    print()
    
    class PrintInTwoParts2(PrintInTwoParts):
        
        def __init__(self):
            super().__init__()
            self.stack_id = None
        
        def print1(self):
            print(self.message1, end="")
            # add to stack "\n"
            self.spirit = Spirit("\n")
            pStack.push(self.spirit)
        
        def print2(self):
            # if not interrupted, remove from stack
            if self.spirit.is_alive():
                self.spirit.kill()
            super().print2()
    
    # now this gets printed correctly
    p = PrintInTwoParts2()
    p.print1()
    p.print2()
    
    p = PrintInTwoParts2()
    p.print1()
    print("Hello world!")
    p.print2()
            
        
            