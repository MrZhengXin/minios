# coding=utf-8

import datetime
import os
import re
import platform
from time import sleep


class Shell:
    def __init__(self):
        self.block_flag = False
        platform_to_clear_cmd = {'Windows': 'cls', 'Linux': 'clear'}
        self.clear_cmd_str = platform_to_clear_cmd[platform.system()]
        self.print_system_info()
               
    def print_system_info(self):
        os.system(self.clear_cmd_str)
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
            re_flag = False
            cur_cmd = raw_command[0]
            if cur_cmd == 're':
                re_flag = True
                raw_command = raw_command[1:]
            commands[i] = [raw_command[0]]
            for arg in raw_command[1:]:
                match_flag = False
                if re_flag:
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
            os.system(self.clear_cmd_str)
            func()
            sleep(interval)
