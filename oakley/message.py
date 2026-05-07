

from .fancy_string import cstr
from .mutable_class import MutableClass
from typing import Literal
import os
import requests
from .xconfig import oakley_config
import sys
import socket


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


    # ------------------- #
    # !-- Collections --! #
    # ------------------- #
        
        
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
                return # otherwise bug in next line
            
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
    

    # ------------------ #
    # !-- Paragraphs --! #
    # ------------------ #
    
    def par(self, paragraph:str="", max_width:int = 150) -> None:
        """
        Print a paragraph of text, respecting muting and identation.
        If the message is too long, it will be split into multiple lines.

        Parameters
        ----------
        paragraph : str
            The text to print as a paragraph. Can include line breaks for readability in the code, but these will be reflowed in the output.
        max_width : int, optional
            Maximum width of the paragraph in characters. If the terminal is narrower, it will adapt to the terminal width. Default is 150.
        """
        with Message.tab():
            # 1. Get terminal width
            terminal_width = self._get_terminal_width()
            if max_width is not None:
                terminal_width = min(terminal_width, max_width)
            
            # 2. Reformat the paragraph: a line break becomes a space, and empty line becomes a line break, double spaces are removed
            while "  " in paragraph or "\t" in paragraph:
                paragraph = paragraph.replace("  ", " ")
                paragraph = paragraph.replace("\t", " ")
            while "\n " in paragraph or " \n" in paragraph:
                paragraph = paragraph.replace("\n ", "\n")
                paragraph = paragraph.replace(" \n", "\n")

            paragraph = paragraph.replace("\n\n", "<oakley_linebreak>").replace("\n", " ").replace("<oakley_linebreak>", "\n")

            # 3. Split paragraph into lines
            lines = paragraph.split("\n")

            # 4. Further split lines that are too long (split on the previous space)
            formatted_lines = []
            line_is_end_of_paragraph = []
            for line in lines:
                while cstr(line).length() > terminal_width: # we use cstr.length to count the length without ANSI escape codes
                    # find the last space within the terminal width
                    split_idx = line.rfind(" ", 0, terminal_width)
                    if split_idx == -1:  # no space found, force split
                        split_idx = terminal_width
                    formatted_lines.append(line[:split_idx].replace("  ", " ").strip())
                    line_is_end_of_paragraph.append(False)
                    line = line[split_idx:].lstrip()  # remove leading spaces for the next line
                formatted_lines.append(line.replace("  ", " ").strip())
                line_is_end_of_paragraph.append(True)
            formatted_lines = [line for line in formatted_lines if line.strip()]

            # 5. Justify the lines (expect the ones that are at the end of a paragraph)
            # by inserting additional spaces until we reach the target length
            justified_lines = []

            if len(formatted_lines) == 0:
                return # nothing to print, otherwise bug in next line
            justification_target_length = max([cstr(line).length() for line in formatted_lines])
            for line, is_end_of_paragraph in zip(formatted_lines, line_is_end_of_paragraph):
                if not is_end_of_paragraph:
                    while cstr(line).length() < justification_target_length:
                        for caracter in [".", ":", ";", ",", " "]: # insert additional spaces after these characters first
                            # find all occurrences of the caracter in the line
                            indices = [i for i, c in enumerate(line) if c == caracter and not (i==len(line)-1 or (line[i+1] != " " and c != " "))] # only add spaces if a space already exists. do not add spaces if there wasn't a space in the first place
                            # for each occurence, insert an additional space after it, but stop if we reach the target length
                            index_offset = 0
                            for idx in indices:
                                idx += index_offset
                                if cstr(line).length() < justification_target_length:
                                    line = line[:idx+1] + " " + line[idx+1:]
                                    index_offset += 1
                                else:
                                    break
                justified_lines.append(line)
            # 5. Print each line with the correct indentation and muting
            for line in justified_lines:
                # I have one final issue. If the line starts with an ANSI escape code, then a space, then a word, 
                # the space won't be removed. I need to take care of this edge case by removing spaces that are right after an ANSI escape code at the beginning of the line
                # find the first space occurence
                first_space_idx = line.find(" ")
                # check the string until the first space, and check wether it is an ANSI escape code (and nothing more)
                if first_space_idx != -1 and cstr(line[:first_space_idx]).length() == 0:
                    line = line[:first_space_idx] + line[first_space_idx+1:]
                self.print(line)
    
    @staticmethod
    def title(title:str, type:Literal["#", "?", "!", "i"] = "i") -> None:
        """
        A function to print a title with a specific format and color 
        depending on the type of the message, ass shown below.

        Parameters
        ----------
        title : str
            The title to print
        type : Literal["#", "?", "!", "i"], optional
            The type of the message, by default "i". Fixes the color of the title as well.


        Examples
        --------
        >>> Message.title("Error", "!")
        -------------
        !-- Error --!
        -------------
        >>> Message.title("Info", "i")
        ------------
        I-- Info --I
        ------------
        >>> Message.title("Success", "#")
        ---------------
        #-- Success --#
        ---------------
        >>> Message.title("Warning", "?")
        ---------------
        ?-- Warning --?
        ---------------
        """
        assert type in ["i", "#", "?", "!"], f"Invalid type: {type}. Must be one of ['i', '#', '?', '!']"
        
        color = {
            "i": "cyan",
            "#": "green",
            "?": "yellow",
            "!": "red"
        }[type]

        # 1. Count the number of letters in the title (without ANSI escape codes)
        n_letters = cstr(title).length()

        # 2. Create the title string with the correct format
        dot_str = "-" * (n_letters + 8)
        title_str = f"{type.upper()}-- {title} --{type.upper()}"
        dot_str = f"{cstr(dot_str):{color[0]}}"
        title_str = f"{cstr(title_str):{color[0]}}"

        # 3. Print ignoring tabs but adding correct amount of spaces for identation
        n_spaces = Message.indent + 2 if Message.indent > 0 else 0

        Message.print()
        Message.print(
            " " * n_spaces + dot_str, ignore_tabs=True
        )
        Message.print(
            " " * n_spaces + title_str, ignore_tabs=True
        )
        Message.print(
            " " * n_spaces + dot_str, ignore_tabs=True
        )
        Message.print()
    

    # -------------------- #
    # !-- Notification --! #
    # -------------------- #

    @staticmethod
    def send(
        message:str,
        filepath:str = None,
        meta:bool = True
    ):
        """
        Sends a message to a predefined webhook URL for Discord.

        Parameters
        ----------
        message : str
            The message to send. Doesn't support color codes.
        filepath : str, optional
            If provided, the content of the file at this path will be included in the message.
            The name of the file will also be included.
        meta : bool, optional
            Wether to include metadata (current working directory, system arguments)
            in the message. Default is True.

        Notes
        -----
        If you haven't specified a webhook URL in the config file, this function will silently fail, and
        print a warning message. This function is meant for Discord, as it is the easiest to set up and use.
        On discord, select a server and open its settings. Open the “Integrations” tab, click “Webhooks”, “New Webhook.”
        Copy the URL and add it to the configuration file the following way:
        ```python
        from oakley import oakley_config
        oakley_config["webhook_url"] = "https://discord.com/api/webhooks/..."
        ```
        You only need to do this once.
        """

        # 1. Check config
        if oakley_config["webhook_url"] == "NONE":
            Message("Unable to send notification: no webhook URL provided in config.", "!").par(
                f"""
                To send notifications, please provide a webhook URL in the config file. See the documentation
                of the `{cstr("Message").green()}.{cstr("send").yellow()}` method for more details.
                """
            )
            return
        
        # 2. Check filepath if provided
        if filepath is not None:
            assert os.path.isfile(filepath), f"Provided filepath is not a file: {filepath}"
        
        # 3. Create message
        cmd = sys.executable + " " + " ".join(sys.argv)
        cwd = os.getcwd()
        hostname = socket.gethostname().upper()
        
        content = f"@{hostname}\n{len(hostname)*'-'}-\n\nCommand: {cmd}\nDirectory: {cwd}\n\n@MESSAGE\n{'-'*7}\n\n{message}"
        if not meta:
            content = message
        content = "```\n" + content + "\n```\n"

        # 4. Send
        try:
            if filepath is None:
                requests.post(
                    oakley_config["webhook_url"],
                    json={
                        "content": content
                    }
                )
            else:
                with open(filepath, "rb") as f:
                    requests.post(
                        oakley_config["webhook_url"],
                        files={
                            "file": f
                        },
                        data={
                            "content": content
                        }
                    )

        except Exception as e:
            with Message("Failed to send notification:", "!"):
                Message.print(str(e))


        

        

        

                



if __name__ == '__main__':
    Message("This is a success message", "#")
    Message("This is an info message", "i")
    Message("This is a warning message", "?")
    Message("This is an error message", "!")
    Message.print()
    Message.listen(1)
    Message("This is a success message. It should not be displayed.", "#")
    Message("This is a warning. It should be displayed.", "?")
    
    Message.listen()
    Message.print()
    
    with Message.tab():
        Message("This message should be indented.")
    Message("This message should not be indented.")
    Message.print()
    
    
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

    Message.title("A nice paragraph", "#")
    
    Message("A nice little paragraph to test the par method.").par(
        cstr(f"""
        This is a long paragraph, and here is what should happen. First of all,
        this string is indented, and therefore aditionnal spaces exist between
        words. These will be removed. Second of all, I have line breaks
        in this paragraph to improve readability inside the code. But
        these line breaks should not be visible in the final output, and the
        text should be reflowed as if it was a single line.

        Finally, when I leave an empty line in the paragraph, this should be interpreted
        as a new paragraph (a line break). So in the final output, there should be two 
        paragraphs.

        The {cstr("paragraphs"):b} will be (or should be) cleverly justified, meaning that additional spaces will be inserted between words until the line
        reaches a certain target length (which is the length of the longest line, or the terminal width if the terminal is narrow). The additional
        spaces will be inserted after dots, commas, colons, semicolons and spaces first, and then after other characters if necessary. Lines at the
        end of a paragraph (before a line break) will not be justified, and will keep a normal spacing.
        """).italic()
    )

    Message.title("Testing with identation", "?")
    Message.print("Let's add identation!")
    with Message.tab():
        with Message.tab():
            Message.title("Fail", "!")
            Message.print("Bla bla bla")
            Message.title("Info", "i")
            Message.print("Bla bla bla")
    
    
    #Message.title("Testing notification system", "!") # let's not :) but it works this way
    #Message.send("Oakley notification system is being tested.")
    # let's send a file
    #Message.send("Oakley current configuration file.", filepath="oakley/config.json", meta=False)
    
    
    
    
    
