# -*- coding: utf-8 -*-

import re
import sys
import time
from datetime import datetime

import click
from art import text2art
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

FONT = "c1"
TEXT_COLOUR_HIGH_PERCENT = "green"
TEXT_COLOUR_MID_PERCENT = "yellow"
TEXT_COLOUR_LOW_PERCENT = "red"
TIMER_HIGH_PERCENT = 0.5
TIMER_LOW_PERCENT = 0.2
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def standardize_time_str(num):
    num = round(num)
    if num <= 0:
        return "00"

    time_str = str(num)
    if len(time_str) == 1:
        time_str = f"0{time_str}"

    return time_str


def createTimeString(hrs, mins, secs):
    time_hrs = standardize_time_str(hrs)
    time_mins = standardize_time_str(mins)
    time_secs = standardize_time_str(secs)
    time_string = f"{time_hrs}:{time_mins}:{time_secs}"

    return time_string


def parseDurationString(duration_str):
    duration_regex = re.compile(r"([0-9]{1,2}h)?([0-9]{1,2}m)?([0-9]{1,2}s)?")
    match = duration_regex.match(duration_str)
    if any(match.groups()):
        return True, match.groups()

    return False, f"Invalid duration string: {duration_str} \n\nPlease use the format __h__m__s or view the help for example usage."


@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(prog_name="timer-cli", package_name="timer-cli")
@click.argument("duration", type=str, required=False)
def main(duration):
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
            f'[red]Please specify a timer duration. \n\nPlease use the format __h__m__s or view the help for example usage.[/red]')
        sys.exit(1)

    success, res = parseDurationString(duration.strip())
    if not success:
        console.print(f"[red]{res}[/red]")
        sys.exit(1)

    hours = int(res[0][:-1]) if res[0] else 0
    minutes = int(res[1][:-1]) if res[1] else 0
    seconds = int(res[2][:-1]) + 1 if res[2] else 0

    countdown_time_string = createTimeString(hours, minutes, seconds - 1)
    countdown_time_text = Text(
        text2art(countdown_time_string, font=FONT), style=TEXT_COLOUR_HIGH_PERCENT
    )

    display_time = Align.center(
        countdown_time_text, vertical="middle", height=console.height + 1
    )

    start_time = time.time()
    target_time = start_time + (hours * 3600) + (minutes * 60) + seconds

    time_difference_secs = target_time - start_time - 1

    try:
        with Live(display_time, screen=True) as live:
            while round(target_time) > round(time.time()):
                remaining_time = target_time - time.time() - 1
                remaining_time_string = createTimeString(
                    remaining_time // 3600,
                    (remaining_time // 60) % 60,
                    remaining_time % 60,
                )
                remaining_time_text = Text(
                    text2art(remaining_time_string, font=FONT))

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

                time.sleep(0.5)
                live.update(display_time)

        with console.screen(style="bold white on red") as screen:
            while True:
                console.bell()
                timer_over_text = Text(
                    text2art("00:00:00", font=FONT), style="blink")
                text = Align.center(timer_over_text, vertical="middle")
                screen.update(Panel(text))
                time.sleep(10)
    except KeyboardInterrupt:
        console.print("[red]Quitting...[/red]")
        sys.exit()


if __name__ == "__main__":
    main()
