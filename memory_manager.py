# coding=utf-8
import numpy as np
import pandas as pd


class PageTable:
    def __init__(self):
        # frame number represent the virtual page's location in physical memory
        # the table has a k_v as (page, [frame_number, validation])
        self.table = {}
        self.max_address = None

    def insert(self, page_num):  # allocated virtual page number
        self.table[page_num] = [None, -1]

    def delete(self, page_num):  # free virtual page number
        self.table.pop(page_num)

    def transform(self, address, page_size):
        """
        :param address: the visited relative address
        :param page_size: size of each page
        :return: if find valid,return the physical_page_number, else return -1
        """
        idx = address // page_size  # 页表偏移量
        if idx < len(self.table):
            index = self.table.keys()[idx]  # 虚页号
            return index
        else:
            return -1

    def modify(self, pnum, fnum, valid):  # when the virtual page being schedule in/out the physical memory
        """
        :param pnum: which virtual page to modify
        :param fnum: the frame number to add
        :param valid: if this virtual page in physical memory. = 1 in/ -1 not
        """
        if valid == 1:
            self.table[pnum] = [fnum, valid]
        else:
            self.table[pnum][1] = valid


class MemoryManager:
    def __init__(self, mode, page_size=1024, page_number=8, physical_page=3, schedule='LRU'):
        """
        :param mode: to define the way to allocate the memory
        :param page_size: the size of each page(useful when mode == 'p')
        :param page_number: the total page num of the virtual memory
        :param physical_page: the total page num of the physical memory
        """
        if mode == 'p':
            # record the virtual memory
            self.virtual_memory = np.array([[page_size, -1, 0] for i in range(page_number)])
            # record = np.zeros((physical_page, 2))
            self.physical_memory = [-1 for i in range(physical_page)]
            self.schedule_queue = []   # for LRU algorithm
            self.ps = page_size
            self.pn = page_number
            # record the page table of all the process, has a k_v as (pid: PageTable)
            self.page_tables = {}
            self.schedule = schedule
        elif mode == 'cb':
            '''cb: continuous best fit algorithm
                r: [start_address, size, pid, aid]
                hole: [start_address, size]
                    '''
            self.r = []  # record for memory status
            self.hole = [[0, page_size * page_number]]  # record for the empty memory
        self.mode = mode
        self.cur_aid = 0  # record every allocation
        self.total = page_number * page_size
        self.allocated = 0

    # load executable file into memory
    # if failed, report error and return -1
    def alloc(self, pid, size):
        if self.mode == 'p':
            return self.page_alloc(pid, size)
        elif self.mode == 'cb':
            return self.continue_alloc(pid, size)

    # pid and aid not all be None
    # return True or False, if failed, report error
    def free(self, pid, aid):
        if self.mode == 'p':
            return self.page_free(pid, aid)
        elif self.mode == 'cb':
            return self.continue_free(pid, aid)

    # command: dms
    # print status of all pages
    def display_memory_status(self):
        # e.g.
        if self.mode == 'p':
            self.page_show()
        elif self.mode == 'cb':
            self.continue_show()

    # if the memory has the page structure
    def page_alloc(self, pid, size):
        s = size
        aid = self.cur_aid
        self.cur_aid += 1
        for i in range(self.pn):
            if self.virtual_memory[i][1] == -1:  # the page is empty
                self.virtual_memory[i][1] = pid
                if pid in self.page_tables.keys():  # the process has a page table
                    ptable = self.page_tables[pid]
                else:  # the precess does not has a page table
                    ptable = PageTable() # create one
                    self.page_tables[pid] = ptable
                ptable.insert(i)  # add the virtual page
                if s >= self.ps:
                    self.virtual_memory[i][0] = self.ps
                    s -= self.ps
                else:
                    self.virtual_memory[i][0] = s
                    s -= s
                self.virtual_memory[i][2] = aid
            if s == 0:
                self.allocated += size
                break
        # if the file cannot be loaded into memory then free the above allocation
        if s > 0 and self.page_free(pid, aid):
            return -1
        # if the file be loaded successfully
        return aid

    # using best-fit algorithm
    def continue_alloc(self, pid, size):
        aid = self.cur_aid
        self.cur_aid += 1
        fit = 1e5  # record the minimum hole size to load the file
        besti = -1  # record the best hole to put the file
        # find the best hole
        for i in range(len(self.hole)):
            if size <= self.hole[i][1] < fit:
                besti = i
                fit = self.hole[i][1]
        # if found
        if besti != -1:
            # add the allocation to record
            self.allocated += size
            self.r.append([self.hole[besti][0], size, pid, aid])
            # if the file size == hole size
            if self.hole[besti][1] == size:
                self.hole.pop(besti)
            else:
                # modify the hole's start_address, size
                self.hole[besti][0] += size
                self.hole[besti][1] -= size
            return aid
        # if not found
        else:
            return -1

    # using best fit algorithm
    def continue_free(self, pid, aid):
        status = 0  # if the pid with aid were found in memory
        delete = []
        for i in range(len(self.r)):
            if (self.r[i][-1] == aid or aid == None) and self.r[i][-2] == pid:
                base_address = self.r[i][0]
                size = self.r[i][1]
                self.allocated -= size
                delete.append(i)
                status = 1
                '''base_meet: if the start address of the new free memory meet with the end of a hole
                                            base_meet = the index of the hole
                                end_meet: if the end address of the new free memory meet with the start of a hole
                                          end_meet = the index of the hole
                            '''
                base_meet = -1
                end_meet = -1
                for i in range(len(self.hole)):
                    if self.hole[i][0] + self.hole[i][1] == base_address:
                        base_meet = i
                    elif self.hole[i][0] == base_address + size:
                        end_meet = i
                # the new free in between of two hole
                if base_meet != -1 and end_meet != -1:
                    self.hole[base_meet][1] += size + self.hole[end_meet][1]
                    self.hole.pop(end_meet)
                # the new free after a hole
                elif base_meet != -1:
                    self.hole[base_meet][1] += size
                # the new free before a hole
                elif end_meet != -1:
                    self.hole[end_meet][1] += size
                    self.hole[end_meet][0] = base_address
                else:
                    self.hole.append([base_address, size])
        if status != 1:
            print("Error! the memory doesn't exist!")
            return False
        for i in range(len(delete) - 1, -1, -1):
            self.r.pop(delete[i])
        return True

    # find the aiming page and delete it from page table
    def page_free(self, pid, aid):
        status = 0
        for i in range(self.pn):
            if self.virtual_memory[i][1] == pid and (self.virtual_memory[i][2] == aid or aid is None):
                status = 1
                self.allocated -= self.virtual_memory[i][0]
                self.virtual_memory[i][0] = self.ps
                self.virtual_memory[i][1] = -1
                self.virtual_memory[i][2] = 0
                ptable = self.page_tables[pid]  # to delete the process's page item
                if i in self.physical_memory:   # if the page in physical memory, free it too.
                    self.physical_memory[self.physical_memory.index(i)] = -1
                    self.schedule_queue.remove(i)
                ptable.delete(i)

        if status == 0:
            print("error! That memory not Found.")
            return False
        return True

    def access(self, pid, address):
        page_offset = address % self.ps
        ptable = self.page_tables[pid]   # get the page table to be visited
        virtual_pageID = ptable.transform(address, self.ps)  # calculate the exact page to be visited
        if virtual_pageID == -1 or self.virtual_memory[virtual_pageID][0] < page_offset:   # if not existed
            print("ERROR ADDRESS !!!!")
            return
        if self.schedule == 'LRU':
            self.LRU(virtual_pageID, ptable)
        pass  # more algorithm to be continued

    def LRU(self, pnum, ptable):
        """
        :param pnum: the virtual page to be switched in physical memory
        :param ptable: the ptable records the virtual page
        """
        print(pnum)
        if pnum in self.physical_memory:
            self.schedule_queue.remove(pnum)
            self.schedule_queue.append(pnum)
        elif -1 in self.physical_memory:
            self.physical_memory[self.physical_memory.index(-1)] = pnum
            self.schedule_queue.append(pnum)
            ptable.modify(pnum, self.physical_memory.index(pnum), 1)
        else:
            index = self.physical_memory.index(self.schedule_queue[0])
            self.physical_memory[index] = pnum
            pid = self.virtual_memory[self.schedule_queue[0]][2]
            p1 = self.page_tables[pid]
            p1.modify(self.schedule_queue[0], 0, -1)
            self.schedule_queue.pop(0)
            self.schedule_queue.append(pnum)
            ptable.modify(pnum, index, 1)
        print('physical cache:', self.physical_memory)
        pass

    def page_show(self):
        print('total: %-dB allocated: %-dB free: %-dB' % (self.total, self.allocated,
                                                          self.total - self.allocated))
        for i in range(self.pn):
            if self.virtual_memory[i][1] != -1 and self.virtual_memory[i][2] != -1:
                print(
                        "block #%d  %-4d/%-4d Byte(s)  pid =%-3d  aid =%-3d" % (i, self.virtual_memory[i][0], self.ps,
                                                                                self.virtual_memory[i][1],
                                                                                self.virtual_memory[i][2]))

    def continue_show(self):
        print('total: %-dB allocated: %-dB free: %-dB' % (self.total, self.allocated,
                                                          self.total - self.allocated))
        for i in range(len(self.r)):
            print('# [base address]: 0x%-5x  [end address]: 0x%-5x pid = %-3d aid = %-3d' % (self.r[i][0],
                                                                                             self.r[i][0] + self.r[i][
                                                                                                 1],
                                                                                             self.r[i][2],
                                                                                             self.r[i][3]))


if __name__ == '__main__':
    mm = MemoryManager(mode='p')
    t = mm.alloc(0, 200)
    mm.display_memory_status()
    mm.alloc(1, 2000)
    mm.display_memory_status()
    t1 = mm.alloc(1, 1094)
    mm.access(1, 1024)
    mm.access(0, 234)
    mm.access(1, 890)
    mm.access(1, 769)
    mm.access(1, 2345)
    mm.display_memory_status()
    mm.free(1, t1)
    mm.alloc(2, 2456)
    mm.access(2, 250)
    mm.access(2, 1300)
    mm.access(0, 1800)
    mm.display_memory_status()
    t2 = mm.alloc(1, 120)
    mm.display_memory_status()
    mm.alloc(1, 200)
    mm.free(1, t2)
    mm.display_memory_status()
