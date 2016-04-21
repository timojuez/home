import tempfile, shutil
class Tempdir(object):
    def open(self,prefix="tmp",keep=False,dir=None):
        """
        @prefix Prefix of the temporary directory name
        @dir Path to store the directory in, default: system's temp dir (/tmp)
        @keep Whether to delete the directory on close()
        """
        self.tempdir = tempfile.mkdtemp(prefix=prefix,dir=dir)
        self._keep=keep
    def __str__(self): return self.tempdir
    def close(self):
        if not self._keep:
            shutil.rmtree(self.tempdir)

