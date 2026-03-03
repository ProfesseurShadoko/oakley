from oakley import *
from typing import Literal

@cli
def collatz(
    start: int,
    model: Literal['steps', 'sequence'] = 'steps',
    limit: int = -999,
    verbose: bool = False
):
    """
    Compute the Collatz sequence.

    Parameters
    ----------
    start : int
        The starting number for the Collatz sequence.
    model : Literal['steps', 'sequence'], optional
        The output format. If 'steps', saves the number of steps to reach 1.
        If 'sequence', saves the full Collatz sequence. Default is 'steps'.
    """
    seq = [start]
    n = start
    steps = 0

    while n != 1:
        if limit > 0 and steps >= limit:
            break
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        seq.append(n)
    
    if verbose:
        Message("Collatz sequence information").list({
            "Start": start,
            "Length": len(seq),
            "Max": max(seq),
            "Limit": limit,
        })
    
    if model == 'steps':
        Message("Saving collatz steps...", "#")
    else:
        Message("Saving collatz sequence...", "#")