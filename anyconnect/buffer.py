import zlib
from binascii import hexlify
from hashlib import md5
import inspect


def override(cls):
    def search(c, method_name):
        for base in inspect.getmro(c):
            if method_name in dir(base):
                return True
        else:
            return False

    def res(method):
        assert search(cls,
                      method.__name__), "Method '%s' of class '%s' marked override, but does not override" % (
            method.__name__, cls.__name__)
        return lambda *args, **kwargs: method(*args, **kwargs)

    return res

class Buffer(object):
    class Mode:
        read = object()
        write = object()

    def __init__(self, stream, mode, bufsize=1024):
        if mode == 'r':
            self.mode = Buffer.Mode.read
        elif mode == 'w':
            self.mode = Buffer.Mode.write
        elif mode == Buffer.Mode.read or mode == Buffer.Mode.write:
            self.mode = mode
        else:
            raise ValueError('Unknown mode stream mode "%s"' % str(mode))
        self.closed = False
        self.stream = stream
        self.buffer = bytearray(bufsize)
        self.buffersize = bufsize
        self.cursor = 0 if mode == Buffer.Mode.write else bufsize

    def write(self, data):
        written = 0
        size = len(data)
        while written < size:
            new_cursor = min(size - written + self.cursor, len(self.buffer))
            self.buffer[self.cursor:new_cursor] = data[written:written + new_cursor - self.cursor]
            written += new_cursor - self.cursor
            self.cursor = new_cursor
            if self.cursor == len(self.buffer):
                self.overflow(False)

    def read(self, size=-1):
        res = bytearray()
        read = 0
        read_size = None
        while (read < size or size < 0) and len(self.buffer) != 0:
            if self.cursor == len(self.buffer):
                read_size = self.underflow()
                self.buffersize = read_size
            new_cursor = min(size - read + self.cursor, len(self.buffer)) if size > 0 else len(self.buffer)
            res[read: read + new_cursor - self.cursor] = self.buffer[self.cursor:new_cursor]
            read += new_cursor - self.cursor
            self.cursor = new_cursor
            if read_size and read_size < len(self.buffer): break
        return res

    def overflow(self, end):
        raise NotImplementedError

    def underflow(self):
        raise NotImplementedError

    def flush(self):
        self.overflow(True)
        self.stream.flush()

    def close(self):
        if self.mode == Buffer.Mode.write and not self.closed:
            self.overflow(True)
            self.closed = True
            self.stream.close()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ChunkBuffer(Buffer):
    def __init__(self, stream, mode, bufsize=1024):
        super().__init__(stream, mode, bufsize)
        self.chunk_left = 0

    @override(Buffer)
    def overflow(self, end):
        self.stream.write('%lx\r\n' % self.cursor)
        self.stream.write(self.buffer[:self.cursor])
        self.stream.write('\r\n')
        self.cursor = 0

    @override(Buffer)
    def underflow(self):
        if self.chunk_left == 0:
            chunk_header = ''
            while True:
                c = self.stream.read(1)
                if c == '\n':
                    break
                else:
                    chunk_header += c
            self.chunk_left = int(chunk_header, 16)

        self.buffer = self.stream.read(min(self.chunk_left, self.buffersize))
        self.chunk_left -= len(self.buffer)

        if self.chunk_left == 0:
            self.stream.read(2)
        self.cursor = 0
        return len(self.buffer)

    @override(Buffer)
    def close(self):
        if self.mode == Buffer.Mode.write and not self.closed:
            self.flush()
            self.stream.write('0\r\n\r\n')
            self.closed = True
            self.stream.close()


class ZBuffer(Buffer):

    class Format:
        DEFLATE = object()
        GZIP = object()

    def __init__(self, stream, mode, format=Format.DEFLATE, buffersize=1024):
        super().__init__(stream, mode, buffersize)
        windowBits = 15 if format == ZBuffer.Format.DEFLATE else 31
        if mode == Buffer.Mode.write:
            self.compressor = zlib.compressobj(wbits=windowBits)
        elif mode == Buffer.Mode.read:
            self.decompressor = zlib.decompressobj(wbits=windowBits)

    @override(Buffer)
    def flush(self):
        self.stream.write(self.compressor.flush(zlib.Z_SYNC_FLUSH))
        self.stream.flush()

    @override(Buffer)
    def overflow(self, end):
        self.stream.write(self.compressor.compress(self.buffer[0:self.cursor]))
        self.cursor = 0
        if end:
            self.stream.write(self.compressor.flush())
            self.closed = True

    @override(Buffer)
    def underflow(self):
        self.buffer = self.decompressor.decompress(self.stream.read(self.buffersize))
        self.cursor = 0
        return len(self.buffer)


class MD5Buffer(Buffer):
    def __init__(self, stream, mode, buffersize=1024):
        super().__init__(stream, mode, buffersize)
        self.md5 = md5()

    @override(Buffer)
    def overflow(self, end):
        self.md5.update(self.buffer[0:self.cursor])
        self.stream.write(self.buffer[0:self.cursor])
        self.cursor = 0

    @override(Buffer)
    def underflow(self):
        self.buffer = self.stream.read(self.buffersize)
        self.md5.update(self.buffer)
        self.cursor = 0
        return len(self.buffer)

    def digest(self, hex=False):
        if hex:
            return hexlify(self.md5.digest())
        else:
            return self.md5.digest()


if __name__ == "__main__":
    import sys
    with open('/tmp/cscan', 'wb') as outfile:
        with ZBuffer(open('/tmp/cscan.gz', 'rb'), Buffer.Mode.read, ZBuffer.Format.GZIP) as stream:
            while True:
                buffer = stream.read(1024)
                outfile.write(buffer)
                if len(buffer) < 1024:
                    break