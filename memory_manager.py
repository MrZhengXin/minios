class MemoryManager:
    def __init__(self, mode, page_size=1024, page_number=8):
        """
        :param mode: to define the way to allocate the memory
        :param page_size: the size of each page(useful when mode == 'p')
        :param page_number: the total page num of the memory
        """
        if mode == 'p':
            '''record has the structure [available page size, pid, aid ]
               page is empty when pid == -1'''

            self.record = [[page_size, -1, 0] for i in range(page_number)]  # record the memory status
            self.ps = page_size
            self.pn = page_number
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
            if self.record[i][1] == -1:  # the page is empty
                self.record[i][1] = pid
                if s >= self.ps:
                    self.record[i][0] -= self.ps
                    s -= self.ps
                else:
                    self.record[i][0] = self.ps - s
                    s -= s
                self.record[i][2] = aid
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
        for i in range(len(self.r)):
            if self.r[i][-1] == aid and self.r[i][-2] == pid:
                base_address = self.r[i][0]
                size = self.r[i][1]
                self.allocated -= size
                self.r.pop(i)
                status = 1
                break
        if status == 1:
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
            return True
        # cannot find the record
        else:
            print("Error! the memory doesn't exist!")
            return False

    # find the aiming page and delete it from page table
    def page_free(self, pid, aid):
        status = 0
        for i in range(self.pn):
            if self.record[i][1] == pid and self.record[i][2] == aid:
                status = 1
                self.allocated -= self.record[i][0]
                self.record[i][0] = self.ps
                self.record[i][1] = -1
                self.record[i][2] = 0
        if status == 0:
            print("error! That memory not Found.")
            return False
        return True

    def page_show(self):
        print(f'total: {self.total:.0f}B allocated: {self.allocated:.0f}B free: {self.total - self.allocated:.0f}B')
        for i in range(self.pn):
            print(
                f'# [page #{i:.0f}] {self.record[i][0]:.0f}/{self.ps} Byte(s) pid = {self.record[i][1]} '
                f'aid = {self.record[i][2]}')

    def continue_show(self):
        print('total: {:.0f}B allocated: {:.0f}B free: {:.0f}B'.format(self.total, self.allocated,
                                                                       self.total - self.allocated))
        for i in range(len(self.r)):
            print('# [base address]: {:#x}, [end address]: {:#x}, pid = {} aid = {}'.format(self.r[i][0],
                                                                                            self.r[i][0] + self.r[i][1],
                                                                                            self.r[i][2], self.r[i][3]))


if __name__ == '__main__':
    mm = MemoryManager(mode='p')
    t = mm.alloc(0, 200)
    mm.display_memory_status()
    mm.alloc(1, 2000)
    mm.display_memory_status()
    t1 = mm.alloc(1, 1094)
    mm.display_memory_status()
    mm.free(0, t)
    mm.display_memory_status()
    mm.alloc(2, 120)
    mm.display_memory_status()
    mm.free(1, t1)
    mm.display_memory_status()
