
# oakley

A small collection of lightweight, opinionated utilities for printing "fancy" console output in Python: colored strings, pretty messages, simple progress bars, task context managers, and tiny system/status helpers.

This package is designed for developer convenience when running short scripts or CLI-style tasks. It provides a few cooperating classes that make it easy to print colored, indented, and optionally muted output, plus a couple of helpers for memory and time display.

## Features

- Colored strings with convenient format specifiers (`cstr`) — easy ANSI coloring and simple format shortcuts.
- `Message` class for categorized, pretty messages (info, warning, error, success).
- `Task` context manager to wrap and time operations, with neat completion/abort output.
- `ProgressBar` iterator wrapper with estimated remaining time and non-intrusive whisper messages.
- `MutableClass` base with global mute/tab behavior so multiple components coordinate console output.
- Small status helpers: `MemoryView` and `DateTime` for quick runtime info.

## Installation

You can downlaod the package with this command:
```bash
pip install oakley
```
Alternatively, you can download the most up-to-date version from my github repository:
```bash
pip install git+https://github.com/ProfesseurShadoko/oakley.git
```

## Quick examples

Colored strings

```python
from oakley import cstr
print(cstr('hello world').green().bold())
print(f"Progress: {cstr('ok'):g}")  # short color spec
print(f"{cstr('Done'):gb}")  # in green and bold
```

Pretty messages

```python
from oakley import Message
Message("Build succeeded", "#")       # green success prefix
Message("Something might be wrong", "?")
```

Tasks and timing

```python
from oakley import Task
import time

with Task("Compute something heavy"):
	time.sleep(1.2)

```

Progress bar

```python
from oakley import ProgressBar
import time

for i in ProgressBar(range(50), size=50):
	time.sleep(0.02)
	if i == 25:
		ProgressBar.whisper("Halfway there!")
```

Status helpers

```python
from oakley import MemoryView, DateTime()
MemoryView()              # prints a short memory usage line (requires psutil)
DateTime()
```

Mute and indentation

```python
from oakley import MutableClass, Message

MutableClass.mute()       # globally mute printing
MutableClass.unmute()

with Message.mute():
	Message.print("This won't be printed")
Message.print("This will be printed again!")

with Message("The following messages will be indented"):   # increase indentation for nested prints
	Message.print("This will be indented")
    MemoryView() # also indented
Message("This won't be indented")
```

## Examples

Take a look at [this notebook](https://github.com/ProfesseurShadoko/oakley/blob/main/example.ipynb) for the most detailed and up to date examples.

Alternatively, run the command:
```bash
python -m oakley.<filename_without_dot_py>
```
to see examples for each object.


## Development notes

- The package is intentionally tiny and uses ANSI escape sequences for coloring; compatibility is best on UNIX-like terminals.
- `MemoryView` depends on `psutil` — the package runs fine even when `psutil` is not available, but the `MemoryView` object cannot be used.
- There are simple demo blocks in each module under `if __name__ == '__main__'` for manual testing.
