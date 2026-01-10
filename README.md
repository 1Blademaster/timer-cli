# Timer-CLI

A very simple Python CLI tool to start a countdown timer.

![Example sreenshot](https://raw.githubusercontent.com/1Blademaster/timer-cli/main/images/screenshot.png)

## Installation

Easily install timer-cli using pip:

```bash
  pip install timer-cli
```

## Usage

```bash
$ timer [options] duration
```

### How to specify a duration

The duration of your timer can be either:
  - A duration string (`__h__m__s`)
  - An absolute datetime (`YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM:SS`)
  - A time only, meaning the next occurrence (`THH:MM:SS`)

#### Duration examples

```bash
timer 1h30m #1hr 30mins
timer 25m #25mins
timer 15m30s #15mins 30secs
timer 2026-01-25T14:00
timer T14:00
```

### Updated examples

- 2min 40mins - `165m`
- 10hrs 50 mins - `650m`
- you can do 999h or 999s as well

### Options

#### --no-bell

Supplying the `--no-bell` flag will stop the terminal from "ringing the bell" (making a sound) once the timer has finished.

#### -m, --message

Use this flag to specify a message to display under the timer. Make sure to surround your string with quotation marks.

```bash
$ timer 1h30m -m "Review the pull requests"
```

#### --font
You can customize the font used to render the timer with 
```bash 
timer --font <font_name> duration
```
Check for available fonts with `timer --list-fonts`

## Contributing

Contributions are always welcome!

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

- Fork the Project
- Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
- Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
- Push to the Branch (`git push origin feature/AmazingFeature`)
- Open a Pull Request

## License

This code is distributed under the [Apache-2.0](https://choosealicense.com/licenses/apache-2.0/) license. See `LICENSE` for more information.

```

```
