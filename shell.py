import datetime

class Shell:
    def __init__(self):
        self.print_system_info()

    def print_system_info(self):
        print('MiniOS 1.0', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # cwd: current working directory
    def get_split_command(self, cwd):
        return input(cwd + '$ ').split()
