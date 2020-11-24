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
            with open(self.filename, "w") as file:
                parser.write(file)

    def get_tasks(self):
        with self.open_parser(write=False) as parser:
            tasks = []
            for name in parser.sections():
                if name == "Config":
                    continue
                section = parser[name]
                tasks.append(Task(
                    name,
                    self,
                    section["check"],
                    section["run"],
                    section.get("processed") == "True",
                    section.get("successful") == "True",
                    section.get("error", None),
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

@dataclasses.dataclass
class Task:
    """Task info."""
    name: str
    config: Config
    check: str
    run: str
    processed: bool
    successful: bool
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
        with self.config.open_parser() as parser:
            if self.name in parser:  # Make sure the task still exists
                parser[self.name]["processed"] = str(processed)

    def set_successful(self, successful):
        with self.config.open_parser() as parser:
            if self.name in parser:
                parser[self.name]["successful"] = str(successful)

    def set_error(self, error):
        if isinstance(error, str):
            pass  # No need to reformat
        elif isinstance(error, TaskException):
            key, original = error.key, error.original
            error = f"{key}: {original!r}"
        else:
            name = type(error).__name__
            message = ", ".join(map(repr, error.args))
            error = f"{name}: {message}"
        with self.config.open_parser() as parser:
            if self.name in parser:
                parser[self.name]["error"] = str(error)

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
