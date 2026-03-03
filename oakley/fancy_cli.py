
import inspect
import argparse
from .fancy_string import cstr
from .message import Message
from typing import Literal, get_args, get_origin
import sys


def _fancy_cli(func):
    """
    A function to turn a function into a command line interface (CLI). This is how it will work:

    1. The arguments description (shown by the --help flag) will be generated from the 
    function's name and docstring.
    2. The function's parameters (retrieved using the inspect module) will be turned into command line arguments.
     - Positional parameters will be turned into required arguments.
     - Parameters with default values will be turned into optional arguments.
     - The type of the parameters will be inferred from the type annotation, if provided, or from the default value, if provided.
     The code must provide type annotations.

    There are however some limitations that one needs to be aware of. First of all, each parameter can have only one type.
    Each parameter must have either exactly one type, or no type but a default value. An argument can never be None (instead,
    use -9999 for integer, "None" for strings, etc. and be ready to handle them in your function). Booleans must have a 
    default value, either True or False, and will be turned into flags (e.g. --flag to set the value to its default).
    """


    # -------------------------- #
    # !-- Function Docstring --! #
    # -------------------------- #
    
    # 1. Define the default description (independant of the functions docstring).
    default_description = f"\n\t{cstr('def '):b}{cstr(func.__name__):yb}{cstr('(').bold()}"
    # let's add the parameters, with types in green, default values in white
    sig = inspect.signature(func)
    for i, (param_name, param) in enumerate(sig.parameters.items()):
        default_description += "\n\t\t"
        default_description += f"{cstr(param_name):c}"
        if param.annotation != inspect.Parameter.empty:
            default_description += f":{cstr(param.annotation.__name__):g}"
        if param.default != inspect.Parameter.empty:
            
            # if Literal, add the possible values
            if get_origin(param.annotation) is Literal:
                choices = list(get_args(param.annotation))
                default_description += f"{cstr(choices):w}"
            # if string, add quotes around it
            if isinstance(param.default, str):
                default_description += f" = {cstr(repr(param.default)):w}"
            else:
                default_description += f" = {cstr(param.default):w}"
        if i < len(sig.parameters) - 1:
            default_description += ","
    default_description += "\n\t"
    default_description += cstr(')').bold() + f" -> {cstr('None'):b}:\n"
    if func.__doc__:
        docstring = func.__doc__
        # remove leading \n and trailing \n
        docstring = docstring.strip('\n')
        # replace \n by \n\t to add indentation to the docstring
        docstring = docstring.replace("\n", "\n\t\t")


        docstring = '\t\t"""\n\t\t' + docstring
        docstring += '\n\t\t"""\n'
        docstring = cstr(docstring).red()
        docstring += "\t\t...\n\n"

    default_description += docstring
    

    tutorial = f"""
    The function signature and docstring are shown below. The CLI is generated from this information,
    following the rules described below.

    The CLI is generated as follows. The --help flag will show this message, as well as the function signature and docstring.
    All the information necessary for the CLI must be present in the signature and docstring. {cstr('No additional information can be provided'):rb}.

    Allowed types for parameters are {cstr('int, float, str, bool and Literal'):r}. For more complex types, you can use str and handle
    the parsing yourself in the function. Each parameter must have either exactly one type, or no type but a default value.
    {cstr('An argument can never be None'):rb} (instead, use -9999 for integer, "None" for strings, etc. and be ready to handle them in
    your function). {cstr('An argument cannot have multiple types'):rb}. {cstr('Booleans must have a default value'):rb}, either True of False, and
    will be turned into flags (e.g. --flag to set the value, leave out to set it to its default).
    """
    while "  " in tutorial:
        tutorial = tutorial.replace("  ", " ")


    # --------------------- #
    # !-- Automatic CLI --! #
    # --------------------- #


    parser = argparse.ArgumentParser(
        description=f"Automatically generated CLI for function {func.__name__}.",
        add_help=False
    )

    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show this help message and exit"
    )
    sig = inspect.signature(func)
    # add arguments one by one
    for param_name, param in sig.parameters.items():
        # 1. Determine whether positional (required) or optional (flag)
        if param.default is inspect._empty:
            # required positional argument
            arg_name = param_name
            is_option = False
        else:
            # optional argument (use --name)
            arg_name = f"--{param_name}"
            is_option = True

        # 2. Determine the type of the argument. If there is a type annotation, use it.
        #    Otherwise, if there is a default value, infer the type from it. Otherwise, raise.
        annotation = param.annotation
        choices = None

        if annotation is not inspect._empty:
            origin = get_origin(annotation)
            if origin is Literal:
                choices = list(get_args(annotation))
                # infer a sensible converter from the first literal value
                arg_type = type(choices[0]) if choices else str
            else:
                arg_type = annotation
        elif param.default is not inspect._empty:
            arg_type = type(param.default)
        else:
            raise Exception(f"Parameter {param_name} must have either a type annotation or a default value.")

        # 3. If the type is bool, set action to store_true/store_false depending on the default value.
        #    Booleans must be optional flags (i.e. have a default).
        if arg_type == bool:
            assert param.default is not inspect._empty, f"Boolean parameter {param_name} must have a default value."
            if not is_option:
                raise Exception(f"Boolean positional parameter {param_name} is not supported; make it optional with a default to become a flag.")
            action = "store_false" if param.default else "store_true"
            parser.add_argument(
                arg_name,
                action=action,
                default=param.default,
                help=f"Optional flag. Default is {param.default}. Use --{param_name} to set it to {not param.default}."
            )
        else:
            # build kwargs for add_argument
            help_parts = []
            if is_option:
                kwargs = {"type": arg_type}
                if choices is not None:
                    kwargs["choices"] = choices
                # provide explicit default for options
                kwargs["default"] = param.default
                # do not pass `required` for optional args (defaults to False)
                help_parts.append(f"Optional argument of type {getattr(arg_type, '__name__', str(arg_type))}")
                if choices:
                    help_parts.append(f"with choices {choices}")
                if param.default is not inspect._empty:
                    help_parts.append(f"Default is {param.default}")
                help_text = ". ".join(help_parts) + "."
                parser.add_argument(
                    arg_name,
                    **kwargs,
                    help=help_text
                )
            else:
                # positional required argument: don't pass `default` or `required`
                help_parts.append(f"Required argument of type {getattr(arg_type, '__name__', str(arg_type))}")
                if choices:
                    help_parts.append(f"with choices {choices}")
                help_text = ". ".join(help_parts) + "."
                parser.add_argument(
                    arg_name,
                    type=arg_type,
                    help=help_text
                )            
    # --------------- #
    # !-- Actions --! #
    # --------------- #

    if "-h" in sys.argv or "--help" in sys.argv:
        Message("Oakley automatic CLI tutorial").par(tutorial)
            
        Message.print(ignore_tabs=True)
        Message("Function signature and docstring")
        Message.print(default_description, ignore_tabs=True)
        Message.print()
        
        Message("Arguments")
        parser.print_help()
        exit(0)
    
    args = parser.parse_args()
    kwargs = vars(args)

    # remove keys that do not correspond to the function parameters (e.g. help)
    sig = inspect.signature(func)
    kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

    # finally run the function
    func(**kwargs)



# ----------------- #
# !-- Decorator --! #
# ----------------- #

def cli(func):
    """
    Decorator to register a function as a CLI.

    Example
    -------
    ```
    @cli
    def my_function(arg1: int, arg2: str = "default", flag: bool = False):
        ...
    # python script.py --arg1 42 --arg2 "hello" --flag
    ```
    """
    _fancy_cli(func)
    return func
    
    



def test_func(N:int, name:str="John", verbose:bool=False, choice:Literal['option1', 'option2']='option1'):
    """
    Some function that has a very long docstring and does a lot of stuff. Since the docstring is too
    long I need to introduce an line break, and it will appear exactly this way in the terminal. If 
    the width of the temrinal is too small, issues might come up. Anyway.

    And this is a new paragraph. That should appear as such.

    Parameters
    ----------
    N : int
        The number of iterations to perform. Must be a positive integer.
    name : str, optional
        The name of the user. Default is "John".
    verbose : bool, optional
        Whether to print verbose output. Default is False.
    choice : Literal['option1', 'option2'], optional
        The choice of the user. Default is 'option1'. Must be either 'option1' or 'option2'.
    """
    pass

if __name__ == '__main__':
    _fancy_cli(test_func)
