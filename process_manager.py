# coding=UTF-8
import time
import json
import threading
import sys
import copy
from hardware_resource import HardwareResource
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd



# 5 status of process: running, waiting, ready,terminated, waiting(Printer)

# A large number means high priority

# PCB
class ProcessControlBlock:
    def __init__(self, pid, ppid, create_time, name, priority, content):
        self.pid = pid
        self.ppid = ppid
        self.name = name
        self.create_time = create_time
        self.priority = priority

        self.command_queue = []  # init
        for command in content:  # change "cpu 5" -> ["cpu",5]
            info = str.split(command)
            info[1] = int(info[1])
            self.command_queue.append(info)
        self.status = "ready"


class ProcessManager:
    def __init__(self, priority=True, preemptive=False, time_slot=1, printer_num=2):
        self.cur_pid = 0
        self.priority = priority
        self.preemptive = preemptive
        self.time_slot = time_slot
        self.ready_queue = [[], [], []]  # three priority (0,1,2)
        self.waiting_queue = []
        self.current_running = -1
        self.pcb_list = []
        self.printer = HardwareResource(printer_num)
        self.devices = ['cpu', 'printer']
        self.resources_history = {i:[] for i in self.devices}
        self.history_length = 10.0
        self.running = False
        # 2 queues, ready queue, waiting queue
        # at most 1 process is running

    def fork(self):
        self.pcb_list[self.current_running].command_queue.pop(0)  # command "fork" out
        child_pcb = copy.deepcopy(self.pcb_list[self.current_running])
        child_pcb.ppid = self.current_running  # parent pid is the current process pid
        child_pcb.pid = self.cur_pid
        child_pcb.create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        self.ready_queue[child_pcb.priority].append(self.cur_pid)
        self.pcb_list.append(child_pcb)
        sys.stdout.write('\033[2K\033[1G')  # avoid \$ [pid #1] finish!
        print("[pid %d] process forked successfully" % self.cur_pid)
        self.cur_pid += 1
        return self.cur_pid


    def create_process(self, file):
        self.pcb_list.append(ProcessControlBlock(self.cur_pid, 0, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                                                 file['name'], file['priority'], file['content']))  # ppid of process created by OS is 0
        self.ready_queue[file['priority']].append(self.cur_pid)
        print("[pid %d] process created successfully" % self.cur_pid)
        self.cur_pid += 1
        return self.cur_pid

        # create PCB
        # insert into ready queue
        # ...
        # e.g. output:
        # [pid #1] process created successfully

        # pass

    def Scheduler(self):
        for p in range(len(self.ready_queue) - 1, -1, -1):
            if len(self.ready_queue[p]) != 0:
                self.current_running = self.ready_queue[p][0]
                self.pcb_list[self.current_running].status = "running"
                self.ready_queue[p].remove(self.current_running)
                return 0
        self.current_running = -1
        return 0

    # simulate time_out
    def time_out(self):
        if self.current_running != -1:
            p = self.pcb_list[self.current_running].priority
            self.pcb_list[self.current_running].status = "ready"
            if self.pcb_list[self.current_running].command_queue != []:
                self.ready_queue[p].append(self.current_running)
        self.Scheduler()

    # simulate io_interrupt
    def io_interrupt(self):
        self.pcb_list[self.current_running].status = "waiting"
        self.waiting_queue.append(self.current_running)
        expect_time = self.pcb_list[self.current_running].command_queue[0][1] * 60
        if self.printer.free_resource > 0:
            self.printer.insert(self.current_running, expect_time)
            self.pcb_list[self.current_running].status = "waiting(Printer)"
        self.Scheduler()

    def release(self, pid):
        self.pcb_list[pid].command_queue.pop(0)
        self.waiting_queue.remove(pid)
        for info in self.printer.running_queue:
            if info[0] == pid:
                self.printer.running_queue.remove(info)
        self.printer.free_resource += 1
        for waiting_pid in self.waiting_queue:
            if self.pcb_list[waiting_pid].status != 'waiting(Printer)' and self.printer.free_resource > 0:
                expect_time = self.pcb_list[waiting_pid].command_queue[0][1] * 60
                self.printer.insert(waiting_pid, expect_time)
                self.pcb_list[waiting_pid].status = "waiting(Printer)"

    # command: kill [pid]
    # if failed, print err message
    def kill_process(self, pid):
        if pid in [pcb.pid for pcb in self.pcb_list]:
            status = self.pcb_list[pid].status
            self.pcb_list[pid].status = 'terminated'
            if status == 'terminated':
                print('kill: kill %d failed: the process is already terminiated' % pid)
            else:
                if status == 'ready':
                    p = self.pcb_list[pid].priority
                    self.ready_queue[p].remove(pid)
                elif status == 'running':
                    self.current_running = -1
                elif status == 'waiting':
                    self.waiting_queue.remove(pid)
                elif status == 'waiting(Printer)':
                    self.release(pid)
                print('kill: kill %d success' % pid)

        else:
            print('kill: kill %d failed: no such process' % pid)

    # command: ps
    def process_status(self):
        # pass
        is_running = False
        for info in self.pcb_list:
            if info.status != 'terminated':
                print("[pid #%5d] name: %-10s status: %-20s create_time: %s" % (
                    info.pid, info.name, info.status, info.create_time))
                is_running = True
        if is_running == False:
            print("No process is running currently")
            # print(info.command_queue)

        # e.g.
        # [pid #1] name: test   status: running(CPU)        time: 2020-05-20 21:29:16
        # [pid #7] name: foo    status: waiting(Printer)    time: 2020-05-20 21:27:26
        # [pid #3] name: bar    status: ready               time: 2020-05-20 21:27:15
        # [pid #4] name: abc    status: ready               time: 2020-05-20 21:27:15

    # command: rs
    def resource_status(self):
        self.printer.print_info()
        # e.g.
        #  1 Printer is free,1 Printer is using  or  1 Printer is using,the recent free time is 2020-05-25 19:05:17
        # [Printer #0] pid: #0     starting_time: 2020-05-25 18:55:17   used time: 2     expect_free_time: 2020-05-25 19:05:17

    def append_resources_history(self, type, pid):
        unix_time = time.time()
        last_unix_time = unix_time - self.history_length
        if len(self.resources_history[type]) != 0:
            last_unix_time = self.resources_history[type][-1][0]
        if unix_time - last_unix_time > 2.0:  # idle time
            self.resources_history[type].append([last_unix_time + 0.001, -1])
            self.resources_history[type].append([unix_time - 0.001, -1])
        self.resources_history[type].append([unix_time, pid])
        while len(self.resources_history[type]) > 0 and unix_time - self.resources_history[type][0][0] > self.history_length:
            self.resources_history[type] = self.resources_history[type][1:]

    # start scheduling
    def run(self):
        self.running = True
        while self.running:
            self.time_out()
            while self.current_running != -1 and self.pcb_list[self.current_running].command_queue[0][0] == "printer":
                self.io_interrupt()
            if self.current_running != -1 and self.pcb_list[self.current_running].command_queue[0][0] == "fork":
                self.fork()
                time.sleep(self.time_slot)
                self.append_resources_history('cpu', self.pcb_list[self.current_running].pid)

            time.sleep(self.time_slot)

            if self.current_running != -1:
                self.pcb_list[self.current_running].command_queue[0][1] -= 1  # update cpu-working time
                self.append_resources_history('cpu', self.pcb_list[self.current_running].pid)
                if self.pcb_list[self.current_running].command_queue[0][1] == 0:
                    self.pcb_list[self.current_running].command_queue.pop(0)
                if self.pcb_list[self.current_running].command_queue == []:
                    sys.stdout.write('\033[2K\033[1G')  # avoid \$ [pid #1] finish!
                    print("[pid #%d] finish!" % self.current_running)
                    self.pcb_list[self.current_running].status = 'terminated'
                    self.current_running = -1

            for info in self.printer.running_queue:
                pid = info[0]
                info[3] = info[3] + 1  # update used_time
                self.append_resources_history('printer', self.pcb_list[self.current_running].pid)
                self.pcb_list[pid].command_queue[0][1] -= 1
                if self.pcb_list[pid].command_queue[0][1] == 0:
                    p = self.pcb_list[pid].priority
                    if self.pcb_list[pid].command_queue != []:
                        self.ready_queue[p].append(pid)
                    else:
                        sys.stdout.write('\033[2K\033[1G')  # avoid \$ [pid #1] finish!
                        print("[pid #%d] finish!" % self.pid)
                        self.pcb_list[pid].status = 'terminated'
                    self.release(pid)

    def resource_monitor(self):
        plt.clf()
        n = len(self.resources_history.keys())
        f, ax = plt.subplots(figsize=(6, 10), nrows=2)
        ax[0].set_ylim(-0.1, 1.1)
        end_time = time.time()
        start_time = end_time - self.history_length
        for i in self.devices:
            x, y = [], []
            
            # remove too old records
            while len(self.resources_history[i]) > 0 and self.resources_history[i][0][0] < start_time:
                self.resources_history[i] =  self.resources_history[i][1:]

            for the_time, pid in self.resources_history[i]:
                x.append(the_time - start_time)
                y.append(0 if pid == -1 else 1)
            if len(x) == 0:
                x, y = [0, self.history_length], [0, 0]
            if x[-1] < self.history_length - 1.0:  # idle time at the end
                x.append(x[-1] + 0.001)
                y.append(0)
                x.append(self.history_length)
                y.append(0)
            ax[0].plot(x, y)
        ax[0].legend(self.devices)
        
        sns.heatmap(data=[
            [len(self.resources_history[v]) for v in self.resources_history.keys()]
        ], cbar=None, ax=ax[1], xticklabels=['cpu', 'printer'], annot=True, 
                linewidths=0.5, robust=True, cmap='YlGnBu', vmin = 0, vmax = 10)
        plt.tight_layout()            

        plt.savefig('resource_monitor.png')
        print('Figure saved at resource_monitor.png')


    def input(self):
        while True:
            s = input(">").split()
            if s == []:
                pass
            elif s[0] == 'c':
                print('程序退出！')
                sys.exit(0)
            elif s[0] == 'ps':
                self.process_status()
            elif s[0] == 'rs':
                self.resource_status()
            elif s[0] == 'kill':
                self.kill_process(int(s[1]))
            elif s[0][0] == '.':
                self.create_process(s[0])
            else:
                print('command not found: %s' % s[0])


if __name__ == '__main__':
    a = ProcessManager(printer_num=1)
    t1 = threading.Thread(target=a.input)
    t2 = threading.Thread(target=a.run)
    t1.start()
    t2.setDaemon(True)
    t2.start()
