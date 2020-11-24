import configparser
import contextlib
import datetime
import subprocess
import time
import os

@contextlib.contextmanager
def open_parser(filename, *, write=True):
    parser = configparser.ConfigParser()
    parser.clear()
    parser.read(filename)
    yield parser
    if write:
        with open(filename, "w") as file:
            parser.write(file)

def get_tasks(filename):
    tasks = {}
    with open_parser(filename, write=False) as parser:
        for name in parser.sections():
            if name == "Config":
                continue
            section = parser[name]
            if section.setdefault("processed", "False") == "True":
                continue
            tasks[name] = {
                "check": section["check"],
                "run": section["run"],
                "processed": section.getboolean("processed"),
            }
    return tasks

def should_run_task(task):
    return eval(task["check"], {"now": datetime.datetime.now()})

def run_task(name, task):
    print(f"[{name}] {task['run']}")
    try:
        return os.system(task["run"]) == 0
    except Exception as e:
        import traceback
        traceback.print_exc()
        return True  # Processed (and failed)

def set_task_processed(name, task, filename):
    # Update task state (set processed=True)
    with open_parser(filename) as parser:
        if name in parser:  # Make sure the task still exists
            parser[name]["processed"] = str(True)

def get_interval(filename):
    # Ensure interval exists in the config file
    with open_parser(filename) as parser:
        parser.setdefault("Config", {})
        parser["Config"].setdefault("interval", str(10))
        return int(parser["Config"]["interval"])

def run_one_cycle(filename):
    for name, task in get_tasks(filename).items():
        if should_run_task(task):
            if run_task(name, task):  # If successfully processed
                set_task_processed(name, task, filename)

def main(filename="tasks.ini"):
    while True:
        run_one_cycle(filename)
        time.sleep(get_interval(filename))

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        print("Usage: python runner.py <filename>")
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
