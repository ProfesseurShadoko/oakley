import subprocess
from oakley import *

# ---------------------- #
# !-- Run CLI script --! #
# ---------------------- #

with Task("Running example CLI with subprocess..."):
    Message.subprocess("cli_example.py", ["37", "0.27"], mute=True)
with Message("Subprocess output (accessed with `cli.out`)"):
    Message.print(cli.out)
