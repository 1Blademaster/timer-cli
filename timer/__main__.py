# -*- coding: utf-8 -*-

import os
import math
import re
import sys
import time
from typing import List, Optional, Tuple, Union
from datetime import datetime, timedelta

IS_WINDOWS = os.name == "nt"
ENABLE_INPUT = not IS_WINDOWS

if ENABLE_INPUT:
    import termios
    import tty
    import select
from contextlib import contextmanager

import click
from art import text2art  # type: ignore
from art import FONT_NAMES
from collections import defaultdict
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.measure import Measurement

DEFAULT_FONT: str = os.environ.get("TIMER_FONT", "c1")
TEXT_COLOUR_HIGH_PERCENT: str = "green"
TEXT_COLOUR_MID_PERCENT: str = "yellow"
TEXT_COLOUR_LOW_PERCENT: str = "red"
TIMER_HIGH_PERCENT: float = 0.5
TIMER_LOW_PERCENT: float = 0.2
CONTEXT_SETTINGS: dict = dict(help_option_names=["-h", "--help"])

Number = Union[int, float]

if ENABLE_INPUT:
    @contextmanager
    def raw_stdin():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def read_key_nonblocking() -> str | None:
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None
else:
    @contextmanager
    def raw_stdin():
        yield

    def read_key_nonblocking() -> None:
        return None

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

def createDateString(hrs: Number, mins: Number, secs: Number) -> str:
    total_seconds = hrs * 3600 + mins * 60 + secs
    days = total_seconds / 86400  # 24 * 60 * 60
    return f"{days:.2f} Days"

def try_parse_target_datetime(s: str) -> datetime | None:
    now = datetime.now()

    # Case 1: full ISO datetime
    try:
        dt = datetime.fromisoformat(s)
        return dt
    except ValueError:
        pass

    # Case 2: only time -> next occurrence today or tomorrow
    if s.startswith("T"):
        try:
            t = datetime.strptime(s[1:], "%H:%M").time()
            candidate = datetime.combine(now.date(), t)

            if candidate <= now:
                candidate += timedelta(days=1)

            return candidate
        except ValueError:
            pass

    return None

def datetime_to_hms(target_dt: datetime) -> tuple[int, int, int]:
    delta = target_dt - datetime.now()
    total_seconds = int(delta.total_seconds())

    if total_seconds <= 0:
        raise ValueError("Target datetime is in the past")

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return hours, minutes, seconds

def parseDurationString(
    duration_str: str,
) -> Tuple[bool, Union[List[Optional[str]], str]]:
    duration_regex = re.compile(r"([0-9]{1,2}h)?([0-9]{1,2}m)?([0-9]{1,2}s)?")
    match = duration_regex.match(duration_str)
    if match and any(match.groups()):
        return True, list(match.groups())

    return (
        False,
        f"Invalid duration string: {duration_str} \n\nPlease use the available formats (__h__m__s, YYYY-MM-DDTHH:MM, THH:MM) or view the help for example usage.",
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
@click.option(
    "--auto-close",
    default=False,
    is_flag=True,
    help="Auto-close on timer finish",
)
@click.option(
    "--days",
    default=False,
    is_flag=True,
    help="To show the timer in days",
)
@click.option(
    "--font",
    type=str,
    default=DEFAULT_FONT,
    show_default=True,
    help="Font used to render the timer (overrides TIMER_FONT env var)",
)
@click.option(
    "--list-fonts",
    is_flag=True,
    help="List available fonts and exit",
)
def main(duration: Optional[str], no_bell: bool, auto_close: bool, message: str, font: str, list_fonts: bool, days: bool) -> None:
    """
    \b
    DURATION is the duration of your timer. It can be either:
        - A duration string (__h__m__s)
        - An absolute datetime (YYYY-MM-DDTHH:MM:SS)
        - A time only, meaning the next occurrence (THH:MM:SS)

    \b
    Example usage:
        $ timer 1h30m
        $ timer 25m
        $ timer 15m30s
        $ timer 2026-01-25T14:00
        $ timer T14:00

    Obs: You can customize the font used to render the timer with:
    
    \b
    timer 25m --font fraktur
    timer --list-fonts

    """
    console = Console()

    if list_fonts:
        def font_height(font: str, sample: str = "0") -> int:
            art = text2art(sample, font=font)
            return len(art.splitlines())

        groups = defaultdict(list)
        for font in FONT_NAMES:
            try:
                h = font_height(font)
            except Exception:
                continue
            if h == 1:
                groups["normal"].append(font)
            elif h <= 2:
                groups["tiny"].append(font)    
            elif h <= 4:
                groups["small"].append(font)
            elif h <= 7:
                groups["medium"].append(font)
            elif h <= 9:
                groups["large"].append(font)
            else:
                groups["huge"].append(font)

        console.print("[bold]Available fonts:[/bold]\n")
        for label in ("normal", "tiny", "small", "medium", "large", "huge"):
            fonts = groups.get(label, [])
            if not fonts:
                continue

            console.print(f"\n[bold][red]{label.upper()} FONTS ({len(fonts)})[/red][/bold]")
            for f in sorted(fonts):
                console.print(f"  {f}")
                print(text2art("12:34:56", font=f))
        sys.exit(0)

    if font not in FONT_NAMES:
        console.print(f"[red]Invalid font '{font}'. Use --list-fonts to list available fonts.[/red]")
        sys.exit(1)

    if not duration or not duration.strip():
        console.print(
            f"[red]Please specify a timer duration. \n\nPlease use the available formats (__h__m__s, YYYY-MM-DDTHH:MM, THH:MM) or view the help for example usage.[/red]"
        )
        sys.exit(1)

    target_dt = try_parse_target_datetime(duration.strip())
    if target_dt is not None:
        try:
            hours, minutes, seconds = datetime_to_hms(target_dt)
        except ValueError as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)
    else:
        success, res = parseDurationString(duration.strip())
        if not success:
            console.print(f"[red]{res}[/red]")
            sys.exit(1)

        hours = int(res[0][:-1]) if res[0] else 0
        minutes = int(res[1][:-1]) if res[1] else 0
        seconds = int(res[2][:-1]) if res[2] else 0

    if hours == 0 and minutes == 0 and seconds == 0:
        console.print(f"[red]The timer duration cannot be zero.[/red]")
        sys.exit(1)

    start_time = time.time()

    target_time = start_time + (hours * 3600) + (minutes * 60) + seconds
    initial_duration = target_time - start_time

    paused = False
    in_days = days
    paused_at = None
    last_remaining_time = None

    initial_display = Align.center(Text(" "), vertical="middle", height=console.height + 1)
    try:
        with raw_stdin(), Live(initial_display, screen=True) as live:
            while True:
                now = time.time()
                
                if ENABLE_INPUT:
                    key = read_key_nonblocking()
                    if key == " ":
                        if not paused:
                            paused = True
                            paused_at = now
                        else:
                            paused = False
                            target_time += now - paused_at
                    elif key == "d":
                        in_days = not in_days

                if paused:
                    remaining_time = max(0, math.ceil(target_time - paused_at))
                else:
                    remaining_time = max(0, math.ceil(target_time - now))

                if in_days:
                    days = remaining_time/86400 # 24 * 60 * 60
                    label = "Day" if round(days, 2) == 1 else "Days"
                    remaining_time_string = f"{days:.2f} {label}"
                else:
                    remaining_time_string = createTimeString(
                        remaining_time // 3600,
                        (remaining_time // 60) % 60,
                        remaining_time % 60,
                    )
                remaining_time_text = Text(text2art(remaining_time_string, font=font).rstrip("\n"))

                time_difference_percentage = remaining_time / initial_duration

                if TIMER_HIGH_PERCENT < time_difference_percentage <= 1:
                    remaining_time_text.stylize(TEXT_COLOUR_HIGH_PERCENT)
                elif (
                    TIMER_LOW_PERCENT < time_difference_percentage <= TIMER_HIGH_PERCENT
                ):
                    remaining_time_text.stylize(TEXT_COLOUR_MID_PERCENT)
                else:
                    remaining_time_text.stylize(TEXT_COLOUR_LOW_PERCENT)

                if paused:
                    remaining_time_text.append("\n[PAUSED — press SPACE to continue]", style="bold yellow")

                message_text = Text(message, style="cyan")
                message_text.align(
                    "center",
                    Measurement.get(console, console.options, remaining_time_text)
                    .normalize()
                    .maximum,
                )

                display_text = Text.assemble(remaining_time_text, Text("\n"), message_text)

                display = Align.center(
                    display_text, vertical="middle", height=console.height + 1
                )

                live.update(display)
                
                if remaining_time <= 0:
                    break
                time.sleep(1)

        with console.screen(style="bold white on red") as screen:
            while not auto_close:
                if not no_bell:
                    console.bell()

                timer_over_text = Text(text2art("00:00:00", font=font), style="blink")
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
