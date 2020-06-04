import datetime
import os
from time import sleep


class Shell:
    def __init__(self):
        self.print_system_info()
        self.block_flag = False

    def print_system_info(self):
        print('MiniOS 1.0', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # cwd: current working directory
    def get_split_command(self, cwd):
        try:
            commands = input(cwd + '$ ').split(';')
        except:
            commands = []
        for i in range(len(commands)):
            commands[i] = commands[i].split()
        return commands

    def deblock(self, *args):
        self.block_flag = False

    def block(self, func, interval=1):
        self.block_flag = True
        while self.block_flag:
            os.system("cls")
            func()
            sleep(interval)
