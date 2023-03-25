# -*- coding: utf-8 -*-

import re
import sys
import time
from typing import List, Optional, Tuple, Union

import click
from art import text2art  # type: ignore
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.measure import Measurement

FONT: str = "c1"
TEXT_COLOUR_HIGH_PERCENT: str = "green"
TEXT_COLOUR_MID_PERCENT: str = "yellow"
TEXT_COLOUR_LOW_PERCENT: str = "red"
TIMER_HIGH_PERCENT: float = 0.5
TIMER_LOW_PERCENT: float = 0.2
CONTEXT_SETTINGS: dict = dict(help_option_names=["-h", "--help"])

Number = Union[int, float]


def standardize_time_str(num: Number) -> str:
    num = round(num)
    if num <= 0:
        return "00"

    time_str = str(num)
    if len(time_str) == 1:
        time_str = f"0{time_str}"

    return time_str


def createTimeString(hrs: Number, mins: Number, secs: Number) -> str:
    time_hrs = standardize_time_str(hrs)
    time_mins = standardize_time_str(mins)
    time_secs = standardize_time_str(secs)
    time_string = f"{time_hrs}:{time_mins}:{time_secs}"

    return time_string


def parseDurationString(
    duration_str: str,
) -> Tuple[bool, Union[List[Optional[str]], str]]:
    duration_regex = re.compile(r"([0-9]{1,2}h)?([0-9]{1,2}m)?([0-9]{1,2}s)?")
    match = duration_regex.match(duration_str)
    if match and any(match.groups()):
        return True, list(match.groups())

    return (
        False,
        f"Invalid duration string: {duration_str} \n\nPlease use the format __h__m__s or view the help for example usage.",
    )


@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(prog_name="timer-cli", package_name="timer-cli")
@click.argument("duration", type=str, required=False)
@click.option(
    "-m",
    "--message",
    type=str,
    required=False,
    default="",
    help="The message to display under the timer",
)
@click.option(
    "--no-bell",
    default=False,
    is_flag=True,
    help="Do not ring the terminal bell once the timer is over",
)
def main(duration: Optional[str], no_bell: bool, message: str) -> None:
    """
    DURATION is the duration of your timer, a number followed by h or m or s for hours, minutes or seconds

    \b
    Example usage:
        $ timer 1h30m
        $ timer 25m
        $ timer 15m30s
    """
    console = Console()

    if not duration or not duration.strip():
        console.print(
            f"[red]Please specify a timer duration. \n\nPlease use the format __h__m__s or view the help for example usage.[/red]"
        )
        sys.exit(1)

    success, res = parseDurationString(duration.strip())
    if not success:
        console.print(f"[red]{res}[/red]")
        sys.exit(1)

    hours = int(res[0][:-1]) if res[0] else 0
    minutes = int(res[1][:-1]) if res[1] else 0
    seconds = int(res[2][:-1]) + 1 if res[2] else 0

    if hours == 0 and minutes == 0 and seconds - 1 <= 0:
        console.print(f"[red]The timer duration cannot be zero.[/red]")
        sys.exit(1)

    countdown_time_string = createTimeString(hours, minutes, seconds - 1)
    countdown_time_text = Text(
        text2art(countdown_time_string, font=FONT), style=TEXT_COLOUR_HIGH_PERCENT
    )

    message_text = Text(message, style="cyan")
    message_text.align(
        "center",
        Measurement.get(console, console.options, countdown_time_text)
        .normalize()
        .maximum,
    )

    display_text = Text.assemble(countdown_time_text, message_text)

    display = Align.center(display_text, vertical="middle", height=console.height + 1)

    start_time = time.time()
    target_time = start_time + (hours * 3600) + (minutes * 60) + seconds

    time_difference_secs = target_time - start_time - 1

    try:
        with Live(display, screen=True) as live:
            while round(target_time) > round(time.time()):
                remaining_time = target_time - time.time() - 1
                remaining_time_string = createTimeString(
                    remaining_time // 3600,
                    (remaining_time // 60) % 60,
                    remaining_time % 60,
                )
                remaining_time_text = Text(text2art(remaining_time_string, font=FONT))

                time_difference_percentage = remaining_time / time_difference_secs

                if TIMER_HIGH_PERCENT < time_difference_percentage <= 1:
                    remaining_time_text.stylize(TEXT_COLOUR_HIGH_PERCENT)
                elif (
                    TIMER_LOW_PERCENT < time_difference_percentage <= TIMER_HIGH_PERCENT
                ):
                    remaining_time_text.stylize(TEXT_COLOUR_MID_PERCENT)
                else:
                    remaining_time_text.stylize(TEXT_COLOUR_LOW_PERCENT)

                display_time = Align.center(
                    remaining_time_text, vertical="middle", height=console.height + 1
                )

                message_text = Text(message, style="cyan")
                message_text.align(
                    "center",
                    Measurement.get(console, console.options, remaining_time_text)
                    .normalize()
                    .maximum,
                )

                display_text = Text.assemble(remaining_time_text, message_text)

                display = Align.center(
                    display_text, vertical="middle", height=console.height + 1
                )

                time.sleep(0.5)
                live.update(display)

        with console.screen(style="bold white on red") as screen:
            while True:
                if not no_bell:
                    console.bell()

                timer_over_text = Text(text2art("00:00:00", font=FONT), style="blink")
                message_text = Text(message, style="white")
                message_text.align(
                    "center",
                    Measurement.get(console, console.options, timer_over_text)
                    .normalize()
                    .maximum,
                )

                display_text = Text.assemble(timer_over_text, message_text)

                display = Align.center(
                    display_text, vertical="middle", height=console.height + 1
                )
                screen.update(Panel(display))
                time.sleep(10)
    except KeyboardInterrupt:
        console.print("[red]Quitting...[/red]")
        sys.exit()


if __name__ == "__main__":
    main()
