# -*- coding: utf-8 -*-

import sys
import time
from datetime import datetime

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


def standardize_time_str(num):
    num = round(num)
    if num <= 0:
        return '00'

    time_str = str(num)
    if len(time_str) == 1:
        time_str = f'0{time_str}'

    return time_str


def createTimeString(hrs, mins, secs):
    time_hrs = standardize_time_str(hrs)
    time_mins = standardize_time_str(mins)
    time_secs = standardize_time_str(secs)
    time_string = f"{time_hrs}:{time_mins}:{time_secs}"

    return time_string


console = Console()


def main():
    hours = 0
    minutes = 0
    seconds = 8 + 1

    countdown_time_string = createTimeString(hours, minutes, seconds - 1)
    countdown_time_text = Text(
        text2art(countdown_time_string, font=FONT), style="bold white")

    display_time = Align.center(countdown_time_text,
                                vertical="middle", height=console.height + 1)

    start_time = time.time()
    target_time = start_time + (hours * 60 * minutes) * 60 + seconds

    time_difference_secs = target_time - start_time - 1

    try:
        with Live(display_time, screen=True) as live:
            while round(target_time) > round(time.time()):
                remaining_time = target_time - time.time() - 1
                remaining_time_string = createTimeString(
                    remaining_time // 3600, remaining_time // 60, remaining_time % 60)
                remaining_time_text = Text(
                    text2art(remaining_time_string, font=FONT))

                time_difference_percentage = remaining_time / time_difference_secs

                if TIMER_HIGH_PERCENT < time_difference_percentage <= 1:
                    remaining_time_text.stylize(TEXT_COLOUR_HIGH_PERCENT)
                elif TIMER_LOW_PERCENT < time_difference_percentage <= TIMER_HIGH_PERCENT:
                    remaining_time_text.stylize(TEXT_COLOUR_MID_PERCENT)
                else:
                    remaining_time_text.stylize(TEXT_COLOUR_LOW_PERCENT)

                display_time = Align.center(remaining_time_text,
                                            vertical="middle", height=console.height + 1)

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
