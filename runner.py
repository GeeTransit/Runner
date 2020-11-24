import configparser
import contextlib
import datetime
import subprocess
import time
import os

parser = configparser.ConfigParser(interpolation=None)

class TaskException(Exception):
    def __init__(self, key, original):
        super().__init__(key, original)
        self.key = key
        self.original = original

@contextlib.contextmanager
def open_parser(filename, *, write=True):
    parser.clear()
    parser.read(filename)
    yield parser
    if write:
        with open(filename, "w") as file:
            parser.write(file)

def get_processable_tasks(filename):
    with open_parser(filename, write=False) as parser:
        tasks = {}
        for name in parser.sections():
            if name == "Config":
                continue
            section = parser[name]
            # Tasks with errors should be checked and have the value removed
            if section.get("error"):
                continue
            tasks[name] = {
                "check": section["check"],
                "run": section["run"],
                "processed": section.get("processed") == "True",
                "successful": section.get("successful") == "True",
            }
        return tasks

def should_run_task(task):
    now = datetime.datetime.now()
    names = "year month day hour minute second".split()
    variables = {name: getattr(now, name) for name in names}
    variables["now"] = now
    try:
        return eval(task["check"], variables)
    except Exception as e:
        raise TaskException("check", e) from None

def run_task(name, task):
    print(f"[{name}] {task['run']}")
    try:
        return os.system(task["run"]) == 0
    except Exception as e:
        raise TaskException("run", e) from None

def set_task_processed(name, task, processed, filename):
    with open_parser(filename) as parser:
        if name in parser:  # Make sure the task still exists
            parser[name]["processed"] = str(processed)

def set_task_successful(name, task, successful, filename):
    with open_parser(filename) as parser:
        if name in parser:
            parser[name]["successful"] = str(successful)

def set_task_errored(name, task, exception, filename):
    with open_parser(filename) as parser:
        if name in parser:
            key, original = exception.key, exception.original
            parser[name]["error"] = f"{key}: {original!r}"

def get_sleep_interval(filename):
    # Ensure interval exists in the config file
    with open_parser(filename) as parser:
        parser.setdefault("Config", {})
        parser["Config"].setdefault("interval", str(10))
        return int(parser["Config"]["interval"])

def run_one_cycle(filename):
    tasks = get_processable_tasks(filename)
    for name, task in tasks.items():
        task_processed = task["processed"]
        task_successful = task["successful"]
        try:
            if task_processed and task_successful:
                # Set it back to not processed when check is False
                if not should_run_task(task):
                    set_task_processed(name, task, False, filename)

            if not task_processed:
                should_run = should_run_task(task)
                # Note that the task wasn't processed so that the user can know
                # that the program is still running.
                set_task_processed(name, task, should_run, filename)
                if should_run:
                    successful = run_task(name, task)
                    set_task_successful(name, task, successful, filename)

        except TaskException as exception:
            set_task_errored(name, task, exception, filename)

def main(filename="tasks.ini"):
    while True:
        run_one_cycle(filename)
        time.sleep(get_sleep_interval(filename))

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
    try:
        main(filename)
    except KeyboardInterrupt:
        pass
    except BaseException:
        import traceback
        traceback.print_exc()
    finally:
        input("Press enter to close the program...")
