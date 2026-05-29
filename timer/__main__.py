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
from rich.columns import Columns
from rich.console import Group
import subprocess

DEFAULT_FONT: str = os.environ.get("TIMER_FONT", "c1")
TEXT_COLOUR_HIGH_PERCENT: str = "green"
TEXT_COLOUR_MID_PERCENT: str = "yellow"
TEXT_COLOUR_LOW_PERCENT: str = "red"
TIMER_HIGH_PERCENT: float = 0.5
TIMER_LOW_PERCENT: float = 0.2
CONTEXT_SETTINGS: dict = dict(help_option_names=["-h", "--help"], ignore_unknown_options=True)
TIME_MODES = [
    ("HMS", 1), 
    ("Days", 86400), 
    ("Weeks", 604800), 
    ("Months", 2592000), # 30 days
    ("Years", 31536000)  # 365 days
]

Number = Union[int, float]

class TimerState:
    def __init__(self, initial_duration, target_time, message, bip=-1, no_bell=False, display_mode=1):
        self.initial_duration = initial_duration
        self.target_time = target_time
        self.message = message
        self.bip = bip
        self.no_bell = no_bell
        self.paused = False
        self.paused_at = None
        self.done = False
        self.display_mode = display_mode
        self.last_bip = initial_duration
        self.step = 0
        self.text = Text()

def play_linux_alarm(step):
    if step == 0:
        sound_path = "/usr/share/sounds/freedesktop/stereo/complete.oga"
    elif step == 1:
        sound_path = "/usr/share/sounds/freedesktop/stereo/service-logout.oga"
    elif step == -1:
        sound_path = "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga"
    else:
        sound_path = "/usr/share/sounds/freedesktop/stereo/suspend-error.oga"
    if os.path.exists(sound_path):
        return subprocess.Popen(
            ["ffplay", sound_path, "-nodisp", "-loglevel", "error", "-autoexit"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    return None

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
        fd = sys.stdin.fileno()
        if select.select([fd], [], [], 0)[0]:
            ch_bytes = os.read(fd, 1)
            if not ch_bytes:
                return None
            ch = ch_bytes.decode('utf-8', errors='ignore')
            if ch == '\x1b':
                if select.select([fd], [], [], 0.05)[0]:
                    ch += os.read(fd, 1).decode('utf-8', errors='ignore')
                    if select.select([fd], [], [], 0.05)[0]:
                        ch += os.read(fd, 1).decode('utf-8', errors='ignore')
            return ch
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

    try:
        dt = datetime.fromisoformat(s)
        return dt
    except ValueError:
        pass

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

def update_timer(timer, now, font, main: bool):
    if timer.paused:
        remaining_time = max(0, math.ceil(timer.target_time - timer.paused_at))
    else:
        remaining_time = max(0, math.ceil(timer.target_time - now))

    if timer.bip > 0 and not IS_WINDOWS and not timer.no_bell and timer.last_bip != remaining_time and (remaining_time+timer.initial_duration)%timer.bip == 0:
        timer.last_bip = remaining_time
        play_linux_alarm(-1)

    if timer.display_mode > 0:
        mode_name, divisor = TIME_MODES[timer.display_mode]
        converted_time = remaining_time/divisor
        remaining_time_string = f"{converted_time:.2f}"
        label = " "+ (mode_name[:-1] if round(converted_time, 2) == 1 else mode_name)
    else:
        remaining_time_string = createTimeString(
            remaining_time // 3600,
            (remaining_time // 60) % 60,
            remaining_time % 60,
        )
        label = ""
    short_msg = f"\n{timer.message[:10]}" if timer.message else ""
    timer.text = Text(f"{remaining_time_string+label[:2]}{short_msg}", style="frame", justify="center")
    if main:
        timer.text.stylize("bold")
        main_text = Text(text2art(remaining_time_string+label, font=font).rstrip("\n"), style="frame")
    
    time_difference_percentage = remaining_time / timer.initial_duration

    if time_difference_percentage <= 0:
        if timer.done == False:
            timer.done = True
            if not IS_WINDOWS and not timer.no_bell:
                play_linux_alarm(2)
        timer.text.stylize("white on red blink")
        if main:
            main_text.stylize("bold white on red blink")
    elif TIMER_HIGH_PERCENT < time_difference_percentage:
        timer.text.stylize(TEXT_COLOUR_HIGH_PERCENT)
        if main:
            main_text.stylize(TEXT_COLOUR_HIGH_PERCENT)
    elif (TIMER_LOW_PERCENT < time_difference_percentage <= TIMER_HIGH_PERCENT):
        if timer.step == 0 and not IS_WINDOWS and not timer.no_bell:
            play_linux_alarm(0)
            timer.step = 1
        timer.text.stylize(TEXT_COLOUR_MID_PERCENT)
        if main:
            main_text.stylize(TEXT_COLOUR_MID_PERCENT)
    else:
        if timer.step == 1 and not IS_WINDOWS and not timer.no_bell:
            play_linux_alarm(1)
            timer.step = 2
        timer.text.stylize(TEXT_COLOUR_LOW_PERCENT)
        if main:
            main_text.stylize(TEXT_COLOUR_LOW_PERCENT)

    if timer.paused:
        timer.text.stylize("strike")
        main_text.stylize("strike")

    if main:
        return main_text

@click.command(context_settings=CONTEXT_SETTINGS)
@click.version_option(prog_name="timer-cli", package_name="timer-cli")
@click.argument("args", type=str, nargs=-1)
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
def main(args: Tuple[str], no_bell: bool, auto_close: bool, font: str, list_fonts: bool) -> None:
    """
    \b
    DURATION is the duration of your timer. It can be either:
        - A duration string (__h__m__s)
        - An absolute datetime (YYYY-MM-DDTHH:MM:SS)
        - A time only, meaning the next occurrence (THH:MM:SS)

    \b
    Example usage (Single Timer):
        $ timer 1h30m
        $ timer 25m -m "Focus" --bip 300

    \b
    Example usage (Multiple Timers):
        $ timer 25m -m "Pomodoro" 5m -m "Break"
        $ timer T14:00 -m "Meeting" 2026-05-13 -m "Exam" -d

    \b
    Interactive Controls:
        [Space]       Pause/Resume current timer
        [Left/Right]  Cycle through active timers
        [d]           Cycle time display (HMS, Days, Weeks, Months, Years)
        [q]           Close/Delete current timer
        [z] or [b]    Undo close (restore last deleted timer)

    \b
    Obs: You can customize the font globally:
        $ timer 25m --font fraktur
        $ timer --list-fonts
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

    if not args or not args[0].strip():
        console.print(
            f"[red]Please specify a timer duration. \n\nPlease use the available formats (__h__m__s, YYYY-MM-DDTHH:MM, THH:MM) or view the help for example usage.[/red]"
        )
        sys.exit(1)

    parsed_timers = []
    i = 0
    while i < len(args):
        duration_str = args[i]
        i += 1
        
        t_msg = ""
        t_bip = -1
        t_mode = 0

        while i < len(args) and args[i].startswith("-"):
            if args[i] in ("-m", "--message"):
                if i + 1 < len(args):
                    t_msg = args[i+1]
                    i += 2
                else:
                    console.print(f"[red]Value of {args[i]} not found[/red]")
                    sys.exit(1)
            elif args[i] == "--bip":
                if i + 1 < len(args):
                    t_bip = int(args[i+1])
                    i += 2
                else:
                    console.print(f"[red]Value of {args[i]} not found[/red]")
                    sys.exit(1)
            elif args[i] in ("--days", "-d"):
                t_mode = 1
                i+=1
            elif args[i] in ("--months", "-M"):
                t_mode = 2
                i+=1
            elif args[i] in ("--weeks", "-w"):
                t_mode = 3
                i+=1
            elif args[i] in ("--years", "-y"):
                t_mode = 4
                i+=1
            else:
                console.print(f"[red]Invalid arg: {args[i]}[/red]")
                sys.exit(1)
                
        # Guarda o pacote de configuração
        parsed_timers.append({
            "duration": duration_str,
            "message": t_msg,
            "bip": t_bip,
            "mode": t_mode
        })

    timers = []
    start_time = time.time()
    for t_config in parsed_timers:
        duration = t_config["duration"]
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

        target_time = start_time + (hours * 3600) + (minutes * 60) + seconds
        initial_duration = target_time - start_time
        timers.append(TimerState(
            initial_duration=initial_duration, 
            target_time=target_time, 
            message=t_config["message"], 
            bip=t_config["bip"], 
            no_bell=no_bell,
            display_mode=t_config["mode"]
        ))

    current_timer_id = 0
    timer = timers[current_timer_id]
    deleted_timers = []

    initial_display = Align.center(Text(" "), vertical="middle", height=console.height + 1)
    try:
        with raw_stdin(), Live(initial_display, screen=True) as live:
            while True:
                now = time.time()
                
                if ENABLE_INPUT:
                    key = read_key_nonblocking()
                    if key == " ":
                        if not timer.paused:
                            timer.paused = True
                            timer.paused_at = now
                        else:
                            timer.paused = False
                            timer.target_time += now - timer.paused_at
                    elif key == "d":
                        timer.display_mode = (timer.display_mode + 1) % len(TIME_MODES)
                    elif key == "q":
                        deleted_timers.append(timers.pop(current_timer_id))
                        if len(timers) == 0:
                            return 
                        current_timer_id = (current_timer_id) % len(timers)
                    elif key in ("z", "b"):
                        if deleted_timers:
                            timers.append(deleted_timers.pop())
                            current_timer_id = len(timers)-1
                    elif key in ("\x1b[C", "\x1bOC"):
                        current_timer_id = (current_timer_id + 1) % len(timers)
                        timer = timers[current_timer_id]
                    elif key in ('\x1b[D', '\x1bOD'):
                        current_timer_id = (current_timer_id - 1) % len(timers)
                        timer = timers[current_timer_id]
                
                for i, _timer in enumerate(timers):
                    if i == current_timer_id:
                        main_timer_text = update_timer(_timer, now, font=font, main = True)
                    elif not _timer.done:
                        update_timer(_timer, now, font=font, main = False)                    

                tabs = Columns([t.text for t in timers], expand=True)

                message_text = Text(timer.message, style="cyan")
                message_text.align(
                    "center",
                    Measurement.get(console, console.options, main_timer_text)
                    .normalize()
                    .maximum,
                )

                main_text = Align.center(Text.assemble(main_timer_text, Text("\n"), message_text), vertical="middle", height=console.height)
                if len(timers) > 1:
                    display = Group(tabs, main_text)
                else:
                    display = main_text

                live.update(display)

                if auto_close and not any(not t.done for t in timers):
                    break

                if ENABLE_INPUT:
                    select.select([sys.stdin], [], [], 1.0)
                else:
                    time.sleep(1)
    except KeyboardInterrupt:
        console.print("[red]Aborting...[/red]")
        sys.exit()


if __name__ == "__main__":
    main()
