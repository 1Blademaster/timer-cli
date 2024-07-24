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

Syntax for a duration is `__h__m__s` where the hour, minute and second values are all optional.

#### Duration examples

- 2mins 30secs - `2m30s`
- 10hrs 5secs - `10h5s`
- 1hr 25mins 45secs - `1h25m45s`

### Options

#### --no-bell

Supplying the `--no-bell` flag will stop the terminal from "ringing the bell" (making a sound) once the timer has finished.

#### -m, --message

Use this flag to specify a message to display under the timer. Make sure to surround your string with quotation marks.

```bash
$ timer 1h30m -m "Review the pull requests"
```

### Logs

Every timer you start will be logged and inserted in a DB (SQLite).
Feel free to access this file with any DB management app.
File's location: `$HOME/timer_cli_personal_logs.db`

## Contributing

Contributions are always welcome!

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

- Fork the Project
- Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
- Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
- Push to the Branch (`git push origin feature/AmazingFeature`)
- Open a Pull Request

## Development

#### How to start locally:
- Build the project with your changes - `poetry build`
- Install deps - `poetry install`
- Run the project `poetry run timer -m "%message here%" 1m`
- Repeat each time you make changes

###### more traditional way to start:
- (optional) Init your venv - `python -m venv venv`
- (optional) Activate your venv - `source venv/bin/activate`
- Run timer with the flags - `python timer/__main__.py -m 'test message for local dev' 1h38m`

## License

This code is distributed under the [Apache-2.0](https://choosealicense.com/licenses/apache-2.0/) license. See `LICENSE` for more information.

```

```
