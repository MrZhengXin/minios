from shell import Shell
from file_manager import FileManager
from memory_manager import MemoryManager
from process_manager import ProcessManager
from config import *
import os
import threading

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

    def report_error(self, cmd, err_msg=''):
        print('[error %s] %s' % (cmd, err_msg))
        if err_msg == '':
            self.display_command_description(cmd_list=[cmd])

    # command: man [cmd1] [cmd2] ...
    def display_command_description(self, cmd_list):
        command_to_description = {
            'man': 'manual page, format: man [command1] [command2] ...',
            'ls': 'list directory contents, format: ls [path]',
            'cd': 'change current working directory, format: cd [path]',
            'rm': 'remove file or directory recursively, format: rm [-r] path',
            'mkdir': 'make directory, format: mkdir path',
            #'mkf': 'make file, format: mkf path',
            'dss': 'display storage status, format: dss',
            'dms': 'display memory status, format: dms',
            'exec': 'create process, format: exec path',
            'ps': 'display process status, format: ps',
            'rs': 'display resource status, format: rs',
            'kill': 'kill process, format: kill pid'
        }
        if len(cmd_list) == 0:
            cmd_list = command_to_description.keys()
        for cmd in cmd_list:
            print(cmd, '-', command_to_description[cmd])

    def run(self):

        # start process manager
        my_process_manager_run_thread = threading.Thread(target=self.my_process_manager.run)
        my_process_manager_run_thread.start()

        while True:
            # a list of commands split by space
            command_split = self.my_shell.get_split_command(cwd=self.my_file_manager.current_working_path)

            # tool name, e.g. ls, cd, ...
            if command_split != []:
                tool = command_split[0]
            else:
                tool = 'space'

            # argument count
            argc = len(command_split)
            if tool == 'space':
                pass
            elif tool == 'man':
                self.display_command_description(cmd_list=command_split[1:])
            elif tool == 'ls':
                if argc >= 2:
                    self.my_file_manager.ls(dir_path=command_split[1])
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
                self.my_memory_manager.display_memory_status()
            elif tool == 'exec':
                if argc >= 2:
                    my_file = self.my_file_manager.get_file(file_path=command_split[1])
                    if my_file:
                        my_pid = self.my_process_manager.create_process(file=my_file)
                        my_aid = self.my_memory_manager.alloc(pid=my_pid, size=int(my_file['size']))
                        self.pid_to_aid[my_pid] = my_aid
                else:
                    self.report_error(cmd=tool)
            elif tool == 'ps':
                self.my_process_manager.process_status()
            elif tool == 'rs':
                self.my_process_manager.resource_status()
            elif tool == 'kill':
                pid_to_kill = int(command_split[1])
                if argc >= 2:
                    # result of process killing
                    kill_res = self.my_process_manager.kill_process(pid=pid_to_kill)
                    if kill_res:
                        self.my_memory_manager.free(pid=pid_to_kill, aid=self.pid_to_aid[pid_to_kill])
                else:
                    self.report_error(cmd=tool)
            else:
                self.report_error(cmd=tool, err_msg='no such command')

if __name__ == '__main__':
    my_kernel = Kernel()
    my_kernel.run()
