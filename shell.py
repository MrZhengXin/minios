import datetime
import os
import re
from time import sleep


class Shell:
    def __init__(self):
        self.print_system_info()
        self.block_flag = False

    def print_system_info(self):
        print('MiniOS 1.0', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # current working directory
    def get_split_command(self, cwd, file_list):
        try:
            commands = input(cwd + '$ ').split(';')
        except:
            commands = []
        for i in range(len(commands)):
            raw_command = commands[i].split()
            if len(raw_command) == 0:
                continue
            commands[i] = [raw_command[0]]
            for arg in raw_command[1:]:
                match_flag = False
                for file_name in file_list:
                    match_res = re.match(arg + '$', file_name)
                    if match_res:
                        match_flag = True
                        commands[i].append(match_res.group(0))
                if match_flag is False:
                    commands[i].append(arg)
        # print(commands)
        return commands

    def deblock(self):
        self.block_flag = False

    def block(self, func, interval=1):
        self.block_flag = True
        while self.block_flag:
            os.system("cls")
            func()
            sleep(interval)
