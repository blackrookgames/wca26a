import sys
from pathlib import Path

SRC_FILE = Path(__file__).resolve()
SRC_DIR = SRC_FILE.parent
PRJ_DIR = SRC_DIR.parent
sys.path.insert(0, str(PRJ_DIR.joinpath("engine")))

import cli

from c_cmd_help import *
from c_cmd_test import *
from c_cmd_ass import *
from c_cmd_dis import *

if __name__ == '__main__':
    # Get commands
    commands:dict[str, type] = {}
    for _class in cli.CLICommand.__subclasses__():
        if not _class.__name__.startswith('cmd_'): continue
        _name = _class.__name__[4:]
        commands[_name] = _class
    cmd_help.commands = commands
    # Execute
    if len(sys.argv) <= 1:
        sys.exit(cmd_help().execute([ '', '', ]))
    else:
        command = sys.argv[1]
        if command == 'help':
            sys.exit(cmd_help().execute([ '', '', ]))
        elif command in commands:
            sys.exit(commands[command]().execute(sys.argv[1:]))
        else:
            print(f"ERROR: Unknown command: {command}", file = sys.stderr)
            sys.exit(1)