# runner.py

Automate your tasks.

## Quickstart

Go to the [latest release](https://github.com/GeeTransit/Runner/releases) and download *runner.exe*. Drag a configuration file onto it to open the program. Double clicking it will make it default to using a *tasks.ini* file.

If you are downloading the source folder, you can run it using `python runner.py <filename>`.

## Setup

Make sure [Python 3.9](https://www.python.org/downloads/release/python-390/) and [Git](https://git-scm.com/downloads) is installed. We'll start by opening a command prompt and cloning the repository.

```cmd
> cd C:\Users\<username>\Documents
> git clone https://github.com/GeeTransit/Runner
> cd Runner
```

## Usage

Double click *runner.py* to find and use *tasks.ini* in the current folder. To use a different file, drag it onto *runner.py*.

You can also run the following in case the program window closes immediately.

```cmd
> python runner.py <filename>
```

## Config

The *tasks.ini* file contains information for *runner.py* and for the tasks that should be run.

Under the `[Config]` section, there is a `interval` variable that stores the amount of seconds to sleep between checks.

All other sections represent tasks. The name of the task is the section name `[<task.name>]`. When *runner.py* finishes sleeping, it will loop over all tasks. Only those whose `check` variable evaluates to True will have the command stored in `run` run (using `os.system`).

More info on task variables is provided in the table below.

| Variable     | Description                             |
|--------------|-----------------------------------------|
| `check`      | Expression to evaluate                  |
| `run`        | Command to run                          |
| `processed`  | True if `eval(check)` is truthy         |
| `successful` | True if `run`'s exit code is 0          |
| `error`      | Error while evaluating `check` or `run` |

To support repeating tasks, *runner.py* can set a task's `processed` to False to mark it available to be run. This happens when a task is `processed`, is `successful`, and `check` is evaluated to be truthy. The task's `successful` will also be left untouched (True).
