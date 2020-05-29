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

        my_process_manager_run_thread = threading.Thread(target=self.my_process_manager.run)
        my_process_manager_run_thread.start()

        self.pid_to_aid = {}

    def report_error(self, cmd, err_content):
        print('[error %s] %s' % (cmd, err_content))

    # command: man [cmd1] [cmd2] ...
    def display_command_description(self, cmd_list):
        command_to_description = {
            'man': 'manual page, format: man [command1] [command2] ...',
            'ls': 'list directory contents, format: ls [path]',
            'cd': 'change current working directory, format: cd [path]',
            'rm': 'remove file or directory recursively, format: rm [path]',
            'mkdir': 'make directory, format: mkdir [path]',
            #'mkf': 'make file, format: mkf [path]',
            'dss': 'display storage status, format: dss',
            'dms': 'display memory status, format: dms',
            'exec': 'create process, format: exec [path]',
            'ps': 'display process status, format: ps',
            'rs': 'display resource status, format: rs',
            'kill': 'kill process, format:kill [pid]' 
        }
        if cmd_list is None:
            cmd_list = command_to_description.keys()
        for cmd in cmd_list:
            print(cmd, '-', command_to_description[cmd])

    def run(self):
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
                if argc >= 2:
                    self.display_command_description(cmd_list=command_split[1:])
                else:
                    self.display_command_description(cmd_list=None)
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
                    self.my_file_manager.rm(file_path=command_split[1])
                else:
                    self.report_error(cmd='rm',
                                      err_content='please input path of file or directory to remove, format: rm [path]')
            elif tool == 'mkdir':
                if argc >= 2:
                    self.my_file_manager.mkdir(dir_path=command_split[1])
                else:
                    self.report_error(cmd='mkdir',
                                      err_content='please input path of directory to create, format: mkdir [path]')
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
                    self.report_error(cmd='exec',
                                      err_content='please input pid you want to kill, format: kill [pid]')
            elif tool == 'ps':
                self.my_process_manager.process_status()
            elif tool == 'rs':
                self.my_process_manager.resource_status()
            elif tool == 'kill':
                if argc >= 2:
                    self.my_process_manager.kill_process(int(command_split[1]))
                else:
                    self.report_error(cmd='kill',
                                      err_content='please input path of executive file, format: exec [path]')
            else:
                self.report_error(cmd=command_split[0], err_content='no such command')

if __name__ == '__main__':
    my_kernel = Kernel()
    my_kernel.run()
