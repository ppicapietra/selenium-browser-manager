import time
import random
import shutil
import sys
from typing import Optional

def r_sleep(min_time: int = None, max_time: int = None) -> None:
    """Generates a random value between min_value and max_value and do a time.sleep with that result on the execution"""
    if min_time is None and max_time is None:
        min_time = 1
        max_time = 3
    elif min_time is None:
        min_time = 1
    elif max_time is None:
        max_time = min_time
        min_time = 1
    sleep_time = random.randint(min_time, max_time)
    time.sleep(sleep_time)

def show_countdown(seconds: int, description_text: str = "Waiting"):
    terminal_width = shutil.get_terminal_size().columns
    while seconds >= 0:
        print(f"{description_text}. Time remaining: {seconds // 60:02d}:{seconds % 60:02d}", end="\r")
        time.sleep(1)
        seconds -= 1
    final_text = description_text + ". Time's up!"
    print(f"{final_text}{ ' ' * ( terminal_width - len( final_text ) ) }", end="\n")
    return

class TMesure:
    """
    A class for measuring the execution time of a task.

    Args:
        task (str): The name or description of the task.

    Attributes:
        _task (str): The name or description of the task.
        _init_time (float): The initial time when the instance is created.

    Methods:
        partial(self, extra: Optional[str] = None) -> None:
            logs the elapsed time of the task up to the moment.

        @staticmethod
        stop(instance, extra: Optional[str] = None) -> None:
            Static method that stops the measurement of the given instance and logs the elapsed time.
    """
    def __init__(self, task):
        """
        Initializes a PMesure instance.

        Args:
            task (str): The name or description of the task.
        """
        self._task = task
        self._init_time = time.perf_counter()

    def cleanup(self) -> None:
        """
        Removes references to instance properties.
        """
        self._init_time = None
        self._task = None

    def partial(self, extra: Optional[str] = None):
        """
        logs the elapsed time of the task up to the moment.

        Args:
            extra (str, optional): Additional information to include in the log.

        Returns:
            None
        """
        print(f"{self._task}.{(' ' + extra + '.') if extra else ''} Time: {time.perf_counter()-self._init_time:.2f} seconds")

def memory_used_by(object: any, name: str = None) -> None:
    """Prints the size in memory of the object passed as argument"""
    size_in_bytes = sys.getsizeof(object)
    size_in_mb = size_in_bytes / (1024 ** 2)
    print(f"The size of {name if name else 'the object'} in memory is: {size_in_mb} MB")
