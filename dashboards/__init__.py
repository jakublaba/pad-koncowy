import os
import sys


def fix_util_import():
    sys.path.append(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
    )
