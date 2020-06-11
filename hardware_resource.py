import datetime
import time


class HardwareResource:
    def __init__(self, resource_num):
        self.free_time = datetime.datetime.now() + datetime.timedelta(days=365)
        self.free_resource = resource_num  # Resource number
        self.resource_num = resource_num
        self.running_queue = []

    def insert(self, pid, time_sec):
        starting_time = datetime.datetime.now()
        free_time = datetime.datetime.now() + datetime.timedelta(seconds=time_sec)
        self.running_queue.append([pid, starting_time, free_time, 0])
        self.free_resource -= 1

    def print_info(self):
        if self.free_resource == 0:
            self.free_time = datetime.datetime.now() + datetime.timedelta(days=365)
            for info in self.running_queue:
                self.free_time = min(self.free_time, info[2])
            recent_free_time = self.free_time.strftime("%Y-%m-%d %H:%M:%S")
            print('%d Printer is using,the recent free time is %s' % (len(self.running_queue), recent_free_time))
        elif self.free_resource == self.resource_num:
            print('No Printer is using,there are %d Printer is free' % self.free_resource)
        else:
            print("%d Printer is free,%d Printer is using," % (self.free_resource, len(self.running_queue)))
        for num, info in enumerate(self.running_queue):
            starting_time = info[1].strftime("%Y-%m-%d %H:%M:%S")
            free_time = info[2].strftime("%Y-%m-%d %H:%M:%S")
            print("[Printer #%d] pid: #%-5d starting_time: %s   used time: %-3d   expect_free_time: %s" % (
                num, info[0], starting_time, info[3], free_time))

    # def work(self, time_sec):
    # self.free_time = datetime.datetime.now() + datetime.timedelta(seconds=time_sec)

# class CPU(HardwareResource):
#     def __init__(self):
#         super(CPU, self).__init__()


# class Printer(HardwareResource):
#     def __init__(self):
#         super(Printer, self).__init__()
