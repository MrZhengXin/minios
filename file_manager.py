import json
import os
import copy

class Block:
    def __init__(self, total_space):

        self.total_space = total_space

        self.free_space = total_space

        self.fp = None

    def is_free(self):
        if self.total_space == self.free_space:
            return True
        else:
            return False

    def set_free_space(self, fs):
        self.free_space = fs

    def get_free_space(self):
        return self.free_space

    def set_fp(self, fp):
        self.fp = fp

    def get_fp(self):
        return self.fp


class FileManager:

    file_separator = os.sep
    root_path = os.getcwd() + file_separator + 'MiniOS_files'  # Win下为\, linux下需要修改!

    def __init__(self, block_size=512, block_number=12):  # block_size的单位:Byte
        self.current_working_path = self.file_separator  # 当前工作目录相对路径, 可以与root_path一起构成绝对路径

        self.block_size = block_size

        self.block_number = block_number

        self.all_blocks = self._init_blocks()

        self.block_dir = {}

        self.file_system_tree = self._init_file_system_tree(self.root_path)

    # load file into disk if success, return first block(linked list), else
    # report err
    def load(self, file):
        pass

    # return file, if failed, report error and return None.
    # file_path支持绝对路径, mode格式与函数open()约定的相同
    def get_file(self, file_path, mode='r'):
        # 由于open()能完成绝大多数工作, 该函数的主要功能体现在排除异常:
        (upper_path, basename) = self.path_split(file_path)
        current_working_dict = self.path2dict(upper_path)
        # 异常1.当路径文件夹不存在时, 报错,报错在 path2dict() 中进行
        if current_working_dict == -1:
            pass
        else:
            # 异常2.文件不存在
            if basename in current_working_dict:
                # 异常3.是文件夹
                if not isinstance(current_working_dict[basename], dict):
                    # 相对路径
                    if file_path[0] != self.file_separator:
                        gf_path = self.root_path + self.current_working_path + file_path
                    # 绝对路径
                    else:
                        gf_path = self.root_path + file_path
                    # 未解决异常! 直接把形参mode丢到open()了.
                    f = open(gf_path, mode)
                    print("get_file success")
                    return json.load(f)
                else:
                    print(
                        "get_file: cannot get file'" +
                        basename +
                        "': dir not a common file")
            else:
                print(
                    "get_file: cannot get file'" +
                    basename +
                    "': file not exist")

        return False

    # 递归地构建文件树
    def _init_file_system_tree(self, now_path):  # now_path是当前递归到的绝对路径
        ''' 文件树采用字典形式, 文件名为键,
            当该文件为文件夹时, 其值为一个字典
            否则, 其值为长度为4的字符串, 表示类型 / 读 / 写 / 执行. '''
        file_list = os.listdir(now_path)
        part_of_tree = {}  # 当前文件夹对应的字典
        for file in file_list:
            file_path = os.path.join(now_path, file)
            if os.path.isdir(file_path):  # 文件夹为键 其值为字典
                part_of_tree[file] = self._init_file_system_tree(file_path)
            else:
                with open(file_path) as f:  # 普通文件为键, 其值为该文件的属性
                    data = json.load(f)
                    part_of_tree[file] = data['type']
                    if self.fill_file_into_blocks(
                            data, file_path[len(self.root_path):]) == -1:  # 将此文件的信息存于外存块中
                        # 没有足够的存储空间
                        print("block storage error: No Enough Space")
        return part_of_tree

    def _init_blocks(self):
        blocks = []  # 块序列
        for i in range(self.block_number):  # 新分配blocks
            b = Block(self.block_size)
            blocks.append(b)
        return blocks

    def find_free_blocks(self, num):  # num:需要的blocks数，此函数用于寻找连续的num个free blocks
        for i in self.all_blocks:  # 找到最后一个空闲块
            if not i.is_free():
                continue
            else:
                first_free_block = self.all_blocks.index(i)
                flag = True
                for j in range(1, num):
                    if first_free_block + j >= self.block_number or \
                            not self.all_blocks[first_free_block + j].is_free():  # 从这个开始的连续num个不满足皆空
                        flag = False
                        break
                if flag:  # 如果找到了
                    return first_free_block
        return -1

    def fill_file_into_blocks(self, f, fp):  # 将此文件的信息存于外存块中
        num = int(int(f["size"]) / self.block_size)
        occupy = int(f["size"]) % self.block_size
        first_free_block = self.find_free_blocks(num + 1)
        if first_free_block == -1:  # 没有足够空间存储此文件
            return -1
        free = self.block_size - occupy
        self.block_dir[fp] = (first_free_block, num + 1)  # block分配信息存在dir中
        count = first_free_block
        for i in range(num + 1):
            if i == num:  # 最后一块可能有碎片
                self.all_blocks[count].set_free_space(free)
            else:
                self.all_blocks[count].set_free_space(0)
            self.all_blocks[count].set_fp(fp)
            count += 1
        return 0

    def delete_file_from_blocks(self, fp):
        start = self.block_dir[fp][0]
        length = self.block_dir[fp][1]
        for i in range(start, start + length):
            self.all_blocks[i].set_free_space(self.block_size)
            self.all_blocks[i].set_fp(None)
        del self.block_dir[fp]
        return

    # 将 "目录的相对或绝对路径" 转化为 当前目录的字典, 用于之后的判断 文件存在 / 文件类型 几乎所有函数的第一句都是它
    def path2dict(self, dir_path):
        if dir_path == '' or dir_path[0] != self.file_separator:
            dir_path = self.current_working_path + dir_path

        dir_list = dir_path.split(self.file_separator)
        dir_list = [i for i in dir_list if i != '']  # 去除由\分割出的空值
        dir_dict = self.file_system_tree
        try:
            for i in range(len(dir_list)):
                dir_dict = dir_dict[dir_list[i]]
            if not isinstance(dir_dict, dict):
                print("path error")
                return -1
            return dir_dict
        # 出错, 即认为路径与当前文件树不匹配, 后续函数会用它来判断"文件夹"是否存在
        except KeyError:
            print("path error")
            return -1  # 返回错误值, 便于外层函数判断路径错误

    # 将 "路径" 分割为 该文件所在的目录 和 该文件名, 以元组返回
    def path_split(self, path):
        # 无视输入时末尾的\,但"\"(根目录)除外
        if len(path) != 1:
            path = path.rstrip(self.file_separator)
        # 从最后一个\分割开, 前一部分为该文件所在的目录(末尾有\), 后一部分为该文件
        basename = path.split(self.file_separator)[-1]
        upper_path = path[:len(path) - (len(basename))]
        # 除去"前一部分"末尾的\, 但"\"(根目录)除外
        if len(upper_path) != 1:
            upper_path = upper_path.rstrip(self.file_separator)
        return (upper_path, basename)

    # command: ls
    def ls(self, dir_path='', mode=''):  # dir_path为空时,列出当前目录文件; 非空(填相对路径时), 列出目标目录里的文件
        current_working_dict = self.path2dict(dir_path)
        # 异常1:ls路径出错. 由于path2dict()中已经报错 | 注: 此处偷懒 如果目标存在, 但不是文件夹, 同样报path
        # error
        if current_working_dict == -1:
            pass
        else:
            file_list = current_working_dict.keys()
            # 目录为空时, 直接结束
            if len(file_list) == 0:
                return
            if mode not in ('-a', '-l', '-al', ''):
                print("ls: invalid option'" + mode + "', try '-a' / '-l' / '-al'")
                return
            for file in file_list:
                # 隐藏文件不显示
                if file[0] == '.' and not mode[0:2] == '-a':
                    pass
                # 文件夹高亮蓝色显示
                elif isinstance(current_working_dict[file], dict):
                    if mode == '-l' or mode == '-al':
                        print('d---', '\t', '\033[1;34m' + file + '\033[0m')
                    else:
                        print('\033[1;34m' + file + '\033[0m', '\t', end='')
                # 可执行文件高亮绿色显示
                elif current_working_dict[file][3] == 'x':
                    if mode == '-l' or mode == '-al':
                        print(current_working_dict[file], '\t', '\033[1;34m' + file + '\033[0m')
                    else:
                        print('\033[1;32m' + file + '\033[0m', '\t', end='')
                else:
                    if mode == '-l' or mode == '-al':
                        print(current_working_dict[file], '\t', file)
                    else:
                        print(file, '\t', end='')
            print('')

    # command: cd
    def cd(self, dir_path=''):  # 参数仅支持目录名, 支持相对或绝对路径 之后以path结尾的表示支持相对或绝对路径, 以name结尾的表示仅支持名
        (upper_path, basename) = self.path_split(dir_path)
        current_working_dict = self.path2dict(upper_path)
        # 异常1:cd路径出错.
        if current_working_dict == -1:
            pass
        else:
            # 空参数和'.'指向自身, 无变化
            if dir_path == '' or dir_path == '.':
                pass
            # '..'指向上一级
            elif dir_path == '..':
                self.current_working_path = self.current_working_path.rsplit(self.file_separator, 2)[
                    0] + self.file_separator
            # 参数为"\"(根目录), 由于根目录无上级目录, 无法完成下一个分支中的操作, 故在这个分支中单独操作.
            elif dir_path == os.sep:
                self.current_working_path = os.sep
            else:
                try:

                    if isinstance(current_working_dict[basename], dict):
                        # 相对路径
                        if dir_path[0] != self.file_separator:
                            # 警告! 未解决异常: 当路径以数个\结尾时, \不会被无视.
                            self.current_working_path += dir_path + self.file_separator
                        # 绝对路径
                        else:
                            self.current_working_path = dir_path + self.file_separator
                        # print('cd ' + self.current_working_path + ' success')
            # 异常1 文件存在但不是目录
                    else:
                        print('cd: error ' + basename + ': Not a dir')
            # 异常2 文件不存在
                except BaseException:
                    print('cd: error ' + basename + ': No such dir')

    # command: make dir
    def mkdir(self, dir_path):
        (upper_path, basename) = self.path_split(dir_path)
        current_working_dict = self.path2dict(
            upper_path)  # 将获取到的字典直接赋值, 对其修改可以影响到文件树
        # 异常1 路径出错
        if current_working_dict == -1:
            pass
        else:
            # 异常2 文件已存在
            if basename in current_working_dict:
                print(
                    "mkdir: cannot create directory '" +
                    basename +
                    "': File exists")
            else:
                # 相对路径
                if dir_path[0] != self.file_separator:
                    mkdir_path = self.root_path + self.current_working_path + dir_path
                # 绝对路径
                else:
                    mkdir_path = self.root_path + dir_path
                os.makedirs(mkdir_path)
                current_working_dict[basename] = {}
                print("mkdir success")

    # command: make file
    def mkf(self, file_path, file_type='crwx', size='233', content=None):
        (upper_path, basename) = self.path_split(file_path)
        current_working_dict = self.path2dict(upper_path)
        json_text = {
            'name': file_path,
            'type': file_type,
            'size': size,
            'content': [content]}
        json_data = json.dumps(json_text, indent=4)
        # 异常1 路径出错
        if current_working_dict == -1:
            pass
        else:
            # 文件名是否已存在
            if basename not in current_working_dict:
                # 相对路径 先不与self.root_path相拼接, 为了紧接着的fill_file_into_blocks传参
                if file_path[0] != self.file_separator:
                    mkf_path = self.current_working_path + file_path
                # 绝对路径
                else:
                    mkf_path = file_path
                if self.fill_file_into_blocks(
                        json_text, mkf_path) == -1:  # 测试是否能装入block
                    print(
                        "mkf: cannot create file'" +
                        basename +
                        "': No enough Space")
                    return
                mkf_path = self.root_path + mkf_path
                f = open(mkf_path, 'w')
                f.write(json_data)
                f.close()
                # 同时修改文件树
                current_working_dict[basename] = file_type
                print("mkf success")
        # 异常2 文件已存在
            else:
                print("mkf: cannot create file'" + basename + "': file exists")

    # command: rm name
    def rm(self, file_path, mode=''):
        (upper_path, basename) = self.path_split(file_path)
        current_working_dict = self.path2dict(upper_path)
        # 异常 路径出错
        if current_working_dict == -1:
            pass
        else:
            # -r 与 -rf 删文件夹
            if mode[0:2] == '-r':
                try:
                    # 异常1: 目录不存在
                    if basename in current_working_dict:
                        # 相对路径
                        if file_path[0] != self.file_separator:
                            rmdir_path = self.root_path + self.current_working_path + file_path
                        # 绝对路径
                        else:
                            rmdir_path = self.root_path + file_path
                        # -rf: 递归地强制删除文件夹
                        if len(mode) == 3 and mode[2] == 'f':
                            sub_dir_dict = self.path2dict(file_path)
                            for i in copy.deepcopy(copy.deepcopy(list(sub_dir_dict.keys()))):  # 删除此目录下的每个文件
                                sub_file_path = file_path + '\\' + i
                                real_sub_file_path = rmdir_path + '\\' + i
                                # 非空的目录, 需要递归删除
                                # print(sub_dir_dict[i])
                                # print(type(sub_dir_dict[i]))
                                # print(isinstance(sub_dir_dict[i], str))
                                if isinstance(sub_dir_dict[i], dict) and sub_dir_dict[i]:
                                    self.rm(sub_file_path, '-rf')
                                # 空目录, 直接删除
                                elif isinstance(sub_dir_dict[i], dict) and not sub_dir_dict[i]:
                                    os.rmdir(real_sub_file_path)
                                # 是文件, 强制删除
                                elif isinstance(sub_dir_dict[i], str):
                                    self.rm(sub_file_path, '-f')

                            current_working_dict.pop(basename)
                            os.rmdir(rmdir_path)

                        # -r: 仅删除空文件夹
                        else:
                            # 同时修改文件树
                            current_working_dict.pop(basename)
                            os.rmdir(rmdir_path)
                    else:
                        print(
                            "rm -r: cannot remove '" +
                            basename +
                            "': No such directory")
                # 异常2 不是文件夹
                except NotADirectoryError:
                    print("rm -r: cannot remove '" + basename + "': not a dir")
                # 异常3 文件夹非空
                except OSError:
                    print(
                        "rm -r: cannot remove '" +
                        basename +
                        "': Dir not empty, try to use '-rf'")
            # 空参数 或 -f 删文件
            elif mode == '' or mode == '-f':
                try:
                    if basename in current_working_dict:
                        # 相对路径
                        if file_path[0] != self.file_separator:
                            rm_path = self.current_working_path + file_path
                        # 绝对路径
                        else:
                            rm_path = file_path
                        if current_working_dict[basename][2] == 'w' or mode == '-f':
                            # 在block中删除文件
                            self.delete_file_from_blocks(rm_path)
                            rm_path = self.root_path + rm_path
                            # 删真正文件
                            os.remove(rm_path)
                            # 同时修改文件树
                            current_working_dict.pop(basename)
                # 异常1 文件只读, 不可删除
                        else:
                            print(
                                "rm: cannot remove '" +
                                basename +
                                "': file read only, try to use -f option")
                # 异常2 文件不存在
                    else:
                        print(
                            "rm: cannot remove '" +
                            basename +
                            "': No such file")
                # 异常3 文件是目录
                except (PermissionError, KeyError):
                    print("rm: cannot remove '" + basename +
                          "': Is a dir. Try to use -r option")
            else:
                print("rm: invalid option'" + mode + "', try '-r' / '-f' / '-rf'")

    # 更改文件属性, name为所该文件名称, type为四字字符(警告!此处未对此四字符进行错误检测)
    def chmod(self, file_path, file_type):
        (upper_path, basename) = self.path_split(file_path)
        current_working_dict = self.path2dict(upper_path)
        # 异常 路径出错
        if current_working_dict == -1:
            pass
        else:
            if basename in current_working_dict:
                if not isinstance(current_working_dict[basename], dict):
                    if file_path[0] != self.file_separator:
                        chmod_path = self.root_path + self.current_working_path + file_path
                    # 绝对路径
                    else:
                        chmod_path = self.root_path + file_path
                    f_in = open(chmod_path, 'r')
                    json_data = json.load(f_in)
                    json_data["type"] = file_type
                    f_out = open(chmod_path, 'w')
                    f_out.write(json.dumps(json_data, indent=4))
                    f_in.close()
                    f_out.close()
                    current_working_dict[basename] = file_type
                    print("chmod success")
            # 异常1 文件是目录
                else:
                    print(
                        "chmod: cannot change mode '" +
                        basename +
                        "': dir not a common file")
            # 异常2 文件不存在
            else:
                print(
                    "chmod: cannot change mode '" +
                    basename +
                    "': No such file")

    # # 输出当前工作路径,-r表示不输出, 仅返回
    # def pwd(self, mode=''):
    #     if mode == '-r':
    #         return self.current_working_path
    #     else:
    #         print(self.current_working_path)

    # 仅做调试用, 将文件树很好看地打印出来
    def tree_dir(self, dir=root_path, layer=0):
        listdir = os.listdir(dir)
        for index, file in enumerate(listdir):
            file_path = os.path.join(dir, file)
            print("|  " * (layer - 1), end="")
            if (layer > 0):
                print("`--" if index == len(listdir) - 1 else "|--", end="")
            print(file)
            if (os.path.isdir(file_path)):
                self.tree_dir(file_path, layer + 1)

    # command: dss
    # print status of all blocks
    def display_storage_status(self):
        total = self.block_size * self.block_number  # 总字节数
        all_free = 0  # 剩余的总字节数
        # for fp, item in self.block_dir.items():  # 调试用
        #     print("{:<10}: start {}\t length {}".format(fp, item[0], item[1]))
        for i in range(self.block_number):
            b = self.all_blocks[i]
            occupy = self.block_size - b.get_free_space()
            all_free += b.get_free_space()
            print("block #{:<5} {:>5} / {} Byte(s)   {:<20}".format(i,
                                                                    occupy, self.block_size, str(b.get_fp())))

        all_occupy = total - all_free  # 已占用的总字节数
        print(
            "total: {0} B,\t allocated: {1} B,\t free: {2} B\n".format(
                total,
                all_occupy,
                all_free))

    # 目录的相对路径 转到 目录的键对应的值(字典)

if __name__ == '__main__':
    a = FileManager()
    # # test block function of mkf and rm
    # a.display_storage_status()
    # a.mkf("abc", size="2333")
    # a.display_storage_status()
    # a.mkf("1234", size="1234")
    # a.display_storage_status()
    # a.rm("1234")
    # a.display_storage_status()

    a.rm('\dir1\dir2', '-rf')
    # a.ls('')
    # a.ls('\\f1')
    # a.pwd()
    # print(a.file_system_tree)
    # a.chmod(r'\dir1\dir2\dir3\\f5', 'cr--')
    # print(a.file_system_tree)
