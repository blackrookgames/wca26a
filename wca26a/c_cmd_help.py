__all__ = ['cmd_help']

import cli

class cmd_help(cli.CLICommand):

    #region cli

    @property
    def _desc(self) -> None|str:
        return "Displays help"

    #endregion

    #region fields

    commands:dict[str, type] = {}

    #endregion

    #region methods

    def _main(self):
        print("World's Crappiest Atari 2600 Assembler")
        print("Putting the PU in Video ComPUter System")
        print("by Zach Combs")
        for command_name, command_type in self.commands.items():
            if command_name == 'test': continue
            command = command_type()
            print()
            command._print_command(command_name)
            if command._desc is not None: print(command._desc)

        return 0

    #endregion