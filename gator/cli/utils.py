from datetime import datetime
from typing import Any, Optional

import typer
from yaspin import Spinner, yaspin
from yaspin.spinners import Spinners


class SpinnerProgressBar:
    def __init__(self, text: str, total: Optional[int] = None, timer: bool = False):
        self._text = text
        self._total = total
        self._current = 0

        if timer:
            self._start = datetime.now()
        else:
            self._start = None

    def step(self, processed: int = 1):
        self._current += processed

    def __str__(self):
        if self._start is None:
            time_elapsed = ''
        else:
            now = datetime.now()
            delta = now - self._start
            time_elapsed = f'{delta.total_seconds():.1f}s'

        if self._total is None:
            progress = ''
        else:
            progress = f'({self._current}/{self._total})'

        return ' '.join([
            self._text,
            time_elapsed,
            progress
        ])


def format_spinner_frames(spinner: Spinner, format: str):
    """Format the spinner's frames. Return a copy of the spinner with the frames
    formatted.

    Args:
        spinner: The spinner to format.
        format: The format string. Use {0} to refer to the frame.
    """
    return Spinner(
        [format.format(frame) for frame in spinner.frames],
        spinner.interval
    )


def section_spinner(text: str, **kwargs: Any) -> Spinner:
    """Return a spinner that will be used to show a section of work.

    NOTE: Sets the text attribute of the spinner to an instance of SpinnerProgressBar.
    Use `sp.text.step()` to increment the progress, where `sp` is the return value.

    Args:
        text: The text to show in the spinner.
        total: The total number of steps. Use None to indicate that the total
            number of steps is unknown.
        timer: If True, show the time elapsed since the spinner was started.
        spinner: The spinner to use. If None, use star2.
        frame_format: The format string for the frames. Use {0} to refer to the
            frame.
        spinner_kwargs: Additional keyword arguments to pass to the yaspin function.
    """
    # Print divider line
    typer.echo('─' * 80)

    pbar = SpinnerProgressBar(
        text,
        total=kwargs.get('total', None),
        timer=kwargs.get('timer', False)
    )
    spinner = yaspin(format_spinner_frames(
        kwargs.get('spinner', Spinners.star2),
        kwargs.get('frame_format', '[{0}]')
    ), text=pbar, **kwargs.get('spinner_kwargs', {}))

    return spinner
