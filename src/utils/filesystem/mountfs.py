from dataclasses import dataclass

from fs.mountfs import MountFS
from fs.path import forcedir, abspath


class UnMountError(Exception):
    """Thrown when mounts conflict."""


class MountVFS(MountFS):

    def unmount(self, name: str):
        self.check()
        path_ = forcedir(abspath(name))
        unmount = []
        for m in self.mounts:
            if path_ == m[0]:
                unmount.append(m)
        if not unmount:
            raise UnMountError("unmount point isn't existing")
        self.default_fs.removetree(path_)
        self.mounts.remove(unmount[0])

    def get_dir_size(self, path: str):
        self.check()
        fs, path_ = self._delegate(path)
        size = 0
        num = 0
        for f in fs.walk.info(path_, namespaces=['basic', 'details', 'access']):
            if not f[1].is_dir:
                size += f[1].size
                num += 1

        return size, num


@dataclass
class FS:
    ctx: MountVFS = MountVFS()
