from __future__ import annotations

import configparser
import contextlib
import dataclasses
import datetime
import subprocess
import time
import os

parser = configparser.ConfigParser(interpolation=None)

@dataclasses.dataclass
class Config:
    """Config file of tasks."""
    filename: str

    @contextlib.contextmanager
    def open_parser(self, *, write=True):
        # Uses global parser
        parser.clear()
        parser.read(self.filename)
        yield parser
        if write:
            self._set_last_updated(parser)
            with open(self.filename, "w") as file:
                parser.write(file)

    def get_tasks(self):
        with self.open_parser(write=False) as parser:
            tasks = []
            for name in parser.sections():
                if name == "Config":
                    continue
                tasks.append(Task(
                    name,
                    self,
                    parser.get(name, "check"),
                    parser.get(name, "run"),
                    parser.getboolean(name, "processed", fallback=None),
                    parser.getboolean(name, "successful", fallback=None),
                    parser.get(name, "error", fallback=None),
                ))
            return tasks

    def run_one_cycle(self):
        for task in self.get_tasks():
            # Tasks with errors should be checked and have the value removed
            if task.error:
                continue

            try:
                if task.processed and task.successful:
                    # Set it back to not processed when check is False
                    if not task.should_run():
                        task.set_processed(False)

                if not task.processed:
                    should_run = task.should_run()
                    # Note whether the task was processed or not so that the
                    # user can know if the program is still running.
                    task.set_processed(should_run)
                    if should_run:
                        successful = task.run_command()
                        task.set_successful(successful)

            # Only catch errors from the user
            except TaskException as exception:
                task.set_error(exception)

    def get_sleep_interval(self):
        # Ensure interval exists in the config file
        with self.open_parser() as parser:
            parser.setdefault("Config", {})
            parser["Config"].setdefault("interval", str(10))
            return int(parser["Config"]["interval"])

    def _set_last_updated(self, parser):
        now = datetime.datetime.now()
        last_updated = now.strftime("%m/%d/%Y %H:%M:%S")
        parser.setdefault("Config", {})
        parser["Config"]["last-updated"] = last_updated
        return last_updated

@dataclasses.dataclass
class Task:
    """Task info."""
    name: str
    config: Config
    check: str
    run: str
    processed: Optional[bool]
    successful: Optional[bool]
    error: Optional[str]

    def should_run(self):
        now = datetime.datetime.now()
        names = "year month day hour minute second".split()
        variables = {name: getattr(now, name) for name in names}
        variables["now"] = now
        try:
            return eval(self.check, variables)
        except Exception as e:
            raise TaskException("check", e) from None

    def run_command(self):
        print(f"[{self.name}] {self.run}")
        try:
            return os.system(self.run) == 0
        except Exception as e:
            raise TaskException("run", e) from None

    def set_processed(self, processed):
        self.processed = processed
        self.update(self.config)

    def set_successful(self, successful):
        self.successful = successful
        self.update(self.config)
        with self.config.open_parser() as parser:
            if self.name in parser:
                parser[self.name]["successful"] = str(successful)

    def set_error(self, error):
        self.successful = self.format_error(error)
        self.update(self.config)

    @staticmethod
    def format_error(error):
        if isinstance(error, str):
            return error  # No need to reformat
        assert isinstance(error, BaseException)
        if isinstance(error, TaskException):
            return f"{error.key}: {error.original!r}"
        return f"{type(error).__name__}: {', '.join(map(repr, error.args))}"

    def update(self, config, force=False):
        with config.open_parser(write=True) as parser:
            if force or self.name in parser:
                if not parser.has_section(self.name):
                    parser.add_section(self.name)
                parser.set(self.name, "check", self.check)
                parser.set(self.name, "run", self.run)
                if self.processed is not None:
                    parser.set(self.name, "processed", str(self.processed))
                if self.successful is not None:
                    parser.set(self.name, "successful", str(self.successful))
                if self.error:
                    parser.set(self.name, "error", self.error)

class TaskException(Exception):
    def __init__(self, key, original):
        super().__init__(key, original)
        self.key = key
        self.original = original

def main(config):
    while True:
        config.run_one_cycle()
        time.sleep(config.get_sleep_interval())

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        print("Usage: python runner.py [filename=tasks.ini]")
        sys.exit(1)
    elif len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        filename = "tasks.ini"

    print(f"Starting runner.py: {filename}")
    config = Config(filename)
    try:
        main(config)
    except KeyboardInterrupt:
        pass
    except BaseException:
        import traceback
        traceback.print_exc()
    finally:
        input("Press enter to close the program...")
