import stat

from fs.osfs import OSFS
import os
from os.path import getsize, join


class OSVFS(OSFS):

    def get_dir_size(self, path: str):
        self.check()
        path_ = self.validatepath(path)
        syspath = self._to_sys_path(path_)
        os.chmod(syspath, stat.S_IRWXU+stat.S_IRWXG+stat.S_IRWXO)
        size = 0
        num = 0
        for root, _, files in os.walk(syspath):
            size += sum(getsize(join(root, name)) for name in files)
            num = len(files)

        return size, num
