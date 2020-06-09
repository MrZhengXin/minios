import signal

from shell import Shell
from file_manager import FileManager
from memory_manager import MemoryManager
from process_manager import ProcessManager
from config import *
import os
import threading
import getopt


class Kernel:
    def __init__(self):
        self.my_shell = Shell()
        self.my_file_manager = FileManager()
        self.my_memory_manager = MemoryManager(mode=memory_management_mode,
                                               page_size=memory_page_size,
                                               page_number=memory_page_number)
        self.my_process_manager = ProcessManager(priority=True,
                                                 preemptive=False,
                                                 time_slot=1,
                                                 printer_num=1)

        self.pid_to_aid = {}

        # start process manager
        self.my_process_manager_run_thread = threading.Thread(target=self.my_process_manager.run)
        self.my_process_manager_run_thread.start()

        # 设置 ctrl + c 安全退出，指向函数 exit_safely
        signal.signal(signal.SIGINT, self.my_shell.deblock)

    def report_error(self, cmd, err_msg=''):
        print('[error %s] %s' % (cmd, err_msg))
        if err_msg == '':
            self.display_command_description(cmd_list=[cmd])

    # command: man [cmd1] [cmd2] ...
    def display_command_description(self, cmd_list):
        command_to_description = {
            'man': 'manual page, format: man [command1] [command2] ...',
            'ls': 'list directory contents, format: ls [-a|-l|-al][path]',
            'cd': 'change current working directory, format: cd [path]',
            'rm': 'remove file or directory recursively, format: rm [-r|-f|-rf] path',
            'mkdir': 'make directory, format: mkdir path',
            # 'mkf': 'make file, format: mkf path',
            'dss': 'display storage status, format: dss',
            'dms': 'display memory status, format: dms',
            'exec': 'execute file, format: exec path',
            'ps': 'display process status, format: ps',
            'rs': 'display resource status, format: rs',
            'kill': 'kill process, format: kill pid',
            'exit': 'exit MiniOS'
        }
        if len(cmd_list) == 0:
            cmd_list = command_to_description.keys()
        for cmd in cmd_list:
            print(cmd, '-', command_to_description[cmd])

    def run(self):
        while True:
            # a list of commands split by space
            command_split_list = self.my_shell.get_split_command(cwd=self.my_file_manager.current_working_path)

            # this indicates user push Enter directly, then nothing to happen
            if len(command_split_list) == 0:
                continue

            for command_split in command_split_list:
                tool = command_split[0]  # tool name, e.g. ls, cd, ...

                argc = len(command_split)  # argument count

                if tool == 'man':
                    self.display_command_description(cmd_list=command_split[1:])

                elif tool == 'ls':
                    if argc >= 2:
                        if argc == 2:
                            if command_split[1][0] == '-':
                                self.my_file_manager.ls(mode=command_split[1])
                            else:
                                self.my_file_manager.ls(dir_path=command_split[1])
                        else:
                            self.my_file_manager.ls(dir_path=command_split[2], mode=command_split[1])
                    else:
                        self.my_file_manager.ls()

                elif tool == 'cd':
                    if argc >= 2:
                        self.my_file_manager.cd(dir_path=command_split[1])
                    else:
                        self.my_file_manager.cd(dir_path=os.sep)

                elif tool == 'rm':
                    if argc >= 2:
                        if argc == 2:
                            self.my_file_manager.rm(file_path=command_split[1])
                        else:
                            self.my_file_manager.rm(mode=command_split[1], file_path=command_split[2])
                    else:
                        self.report_error(cmd=tool)

                elif tool == 'chmod':
                    if argc >= 3:
                        self.my_file_manager.chmod(file_path=command_split[1], file_type=command_split[2])
                    else:
                        self.report_error(cmd=tool)

                elif tool == 'mkdir':
                    if argc >= 2:
                        self.my_file_manager.mkdir(dir_path=command_split[1])
                    else:
                        self.report_error(cmd=tool)

                elif tool == 'dss':
                    self.my_file_manager.display_storage_status()

                elif tool == 'dms':
                    self.my_shell.block(func=self.my_memory_manager.display_memory_status)

                elif tool == 'exec':
                    if argc >= 2:
                        if argc == 2:
                            my_file = self.my_file_manager.get_file(file_path=command_split[1])
                            if my_file:
                                my_pid = self.my_process_manager.create_process(file=my_file)
                                my_aid = self.my_memory_manager.alloc(pid=my_pid, size=int(my_file['size']))
                                self.pid_to_aid[my_pid] = my_aid
                        #elif command_split[1] == '-d':


                    else:
                        self.report_error(cmd=tool)

                elif tool == 'ps':
                    self.my_shell.block(func=self.my_process_manager.process_status)

                elif tool == 'rs':
                    self.my_shell.block(func=self.my_process_manager.resource_status)

                elif tool == 'kill':
                    pid_to_kill = int(command_split[1])
                    if argc >= 2:
                        # result of process killing
                        kill_res = self.my_process_manager.kill_process(pid=pid_to_kill)
                        if kill_res:
                            self.my_memory_manager.free(pid=pid_to_kill)
                    else:
                        self.report_error(cmd=tool)

                elif tool == 'exit':
                    self.my_process_manager.running = False
                    exit(0)

                else:
                    self.report_error(cmd=tool, err_msg='no such command')


if __name__ == '__main__':
    my_kernel = Kernel()
    my_kernel.run()
