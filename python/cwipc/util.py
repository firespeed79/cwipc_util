import ctypes
import ctypes.util

__all__ = [
    'CwipcError',
    
    'cwipc',
    'cwipc_source',
    
    'cwipc_point',
    'cwipc_point_array',
    
    'cwipc_read',
    'cwipc_read_debugdump',
    'cwipc_write',
    'cwipc_write_debugdump',
    'cwipc_from_points',
    
    'cwipc_synthetic',
]

class CwipcError(RuntimeError):
    pass
    
_cwipc_util_dll_reference = None

class cwipc_p(ctypes.c_void_p):
    pass
    
class cwipc_source_p(ctypes.c_void_p):
    pass
    
#
# NOTE: the signatures here must match those in cwipc_util/api.h or all hell will break loose
#
def _cwipc_util_dll(libname=None):
    """Load the cwipc_util DLL and assign the signatures (if not already loaded)"""
    global _cwipc_util_dll_reference
    if _cwipc_util_dll_reference: return _cwipc_util_dll_reference
    
    if libname == None:
        libname = ctypes.util.find_library('cwipc_util')
        if not libname:
            raise RuntimeError('Dynamic library cwipc_util not found')
    assert libname
    _cwipc_util_dll_reference = ctypes.CDLL(libname)
    
    _cwipc_util_dll_reference.cwipc_read.argtypes = [ctypes.c_char_p, ctypes.c_ulonglong, ctypes.POINTER(ctypes.c_char_p)]
    _cwipc_util_dll_reference.cwipc_read.restype = cwipc_p
    
    _cwipc_util_dll_reference.cwipc_write.argtypes = [ctypes.c_char_p, cwipc_p, ctypes.POINTER(ctypes.c_char_p)]
    _cwipc_util_dll_reference.cwipc_write.restype = int
    
    _cwipc_util_dll_reference.cwipc_from_points.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_ulonglong, ctypes.POINTER(ctypes.c_char_p)]
    _cwipc_util_dll_reference.cwipc_from_points.restype = cwipc_p
    
    _cwipc_util_dll_reference.cwipc_read_debugdump.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p)]
    _cwipc_util_dll_reference.cwipc_read_debugdump.restype = cwipc_p
    
    _cwipc_util_dll_reference.cwipc_write_debugdump.argtypes = [ctypes.c_char_p, cwipc_p, ctypes.POINTER(ctypes.c_char_p)]
    _cwipc_util_dll_reference.cwipc_write_debugdump.restype = ctypes.c_int
    
    _cwipc_util_dll_reference.cwipc_free.argtypes = [cwipc_p]
    _cwipc_util_dll_reference.cwipc_free.restype = None
    
    _cwipc_util_dll_reference.cwipc_timestamp.argtypes = [cwipc_p]
    _cwipc_util_dll_reference.cwipc_timestamp.restype = ctypes.c_ulonglong
    
    _cwipc_util_dll_reference.cwipc_get_uncompressed_size.argtypes = [cwipc_p, ctypes.c_ulong]
    _cwipc_util_dll_reference.cwipc_get_uncompressed_size.restype = ctypes.c_size_t
    
    _cwipc_util_dll_reference.cwipc_copy_uncompressed.argtypes = [cwipc_p, ctypes.POINTER(ctypes.c_byte), ctypes.c_size_t]
    _cwipc_util_dll_reference.cwipc_copy_uncompressed.restype = ctypes.c_int
    
    _cwipc_util_dll_reference.cwipc_source_get.argtypes = [cwipc_source_p]
    _cwipc_util_dll_reference.cwipc_source_get.restype = cwipc_p
    
    _cwipc_util_dll_reference.cwipc_source_free.argtypes = [cwipc_source_p]
    _cwipc_util_dll_reference.cwipc_source_free.restype = None
    
    _cwipc_util_dll_reference.cwipc_synthetic.argtypes = []
    _cwipc_util_dll_reference.cwipc_synthetic.restype = cwipc_source_p
    return _cwipc_util_dll_reference
    
#
# C/Python cwipc_point structure. MUST match cwipc_util/api.h, but CWIPC_POINT_VERSION helps a bit.
#
class cwipc_point(ctypes.Structure):
    """Point in a pointcloud. Fields ar x,y,z (float coordinates) and r, g, b (color values 0..255)"""
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("r", ctypes.c_ubyte),
        ("g", ctypes.c_ubyte),
        ("b", ctypes.c_ubyte),
    ]
    
    def __eq__(self, other):
        for fld in self._fields_:
            if getattr(self, fld[0]) != getattr(other, fld[0]):
                return False
        return True

    def __ne__(self, other):
        for fld in self._fields_:
            if getattr(self, fld[0]) != getattr(other, fld[0]):
                return True
        return False
            
CWIPC_POINT_VERSION = 0x20190209

def cwipc_point_array(*, count=None, values=()):
    """Create an array of cwipc_point elements. `count` can be specified, or `values` can be a tuple or list of tuples (x, y, z, r, g, b), or both"""
    if count == None:
        count = len(values)
    allocator = cwipc_point * count
    if isinstance(values, bytearray):
        return allocator.from_buffer(values)
    if not isinstance(values, tuple):
        values = tuple(values)
    return allocator(*values)
    
class cwipc:
    """Pointcloud as an opaque object."""
    
    def __init__(self, _cwipc=None):
        if _cwipc != None:
            assert isinstance(_cwipc, cwipc_p)
        self._cwipc = _cwipc
        self._points = None
        self._bytes = None
        
    def _as_cwipc_p(self):
        assert self._cwipc
        return self._cwipc
            
    def free(self):
        """Delete the opaque pointcloud object (by asking the original creator to do so)"""
        if self._cwipc:
            _cwipc_util_dll().cwipc_free(self._as_cwipc_p())
        self._cwipc = None
        
    def timestamp(self):
        """Returns timestamp (microseconds) when this pointcloud was captured (relative to some unspecified origin)"""
        rv = _cwipc_util_dll().cwipc_timestamp(self._as_cwipc_p())
        return rv
        
    def get_uncompressed_size(self):
        """Get the size in bytes of the uncompressed pointcloud data"""
        rv = _cwipc_util_dll().cwipc_get_uncompressed_size(self._as_cwipc_p())
        return rv
        
    def get_points(self):
        """Get the pointcloud data as a cwipc_point_array"""
        if self._points == None:
            self._get_points_and_bytes()
        assert self._points
        return self._points
        
    def get_bytes(self):
        """Get the pointcloud data as Python bytes"""
        if self._bytes == None:
            self._get_points_and_bytes()
        assert self._bytes
        return self._bytes
        
    def _get_points_and_bytes(self):
        assert self._cwipc
        nBytes = _cwipc_util_dll().cwipc_get_uncompressed_size(self._as_cwipc_p(), CWIPC_POINT_VERSION)
        buffer = bytearray(nBytes)
        bufferCtypesType = ctypes.c_byte * nBytes
        bufferArg = bufferCtypesType.from_buffer(buffer)
        nPoints = _cwipc_util_dll().cwipc_copy_uncompressed(self._as_cwipc_p(), bufferArg, nBytes)
        points = cwipc_point_array(count=nPoints, values=buffer)
        assert points
        assert buffer
        self._bytes = buffer
        self._points = points

class cwipc_source:
    """Pointcloud source as an opaque object"""
    
    def __init__(self, _cwipc_source=None):
        if _cwipc_source != None:
            assert isinstance(_cwipc_source, cwipc_source_p)
        self._cwipc_source = _cwipc_source

    def _as_cwipc_source_p(self):
        assert self._cwipc_source
        return self._cwipc_source
            
        
    def free(self):
        """Delete the opaque pointcloud source object (by asking the original creator to do so)"""
        if self._cwipc_source:
            _cwipc_util_dll().cwipc_source_free(self._as_cwipc_source_p())
        self._cwipc_source = None
        
    def get(self):
        """Get a cwipc (opaque pointcloud) from this source. Returns None if no more pointcloudes are forthcoming"""
        rv = _cwipc_util_dll().cwipc_source_get(self._as_cwipc_source_p())
        if rv:
            return cwipc(rv)
        return None
        
def cwipc_read(filename, timestamp):
    """Read pointcloud from a .ply file, return as cwipc object. Timestamp must be passsed in too."""
    errorString = ctypes.c_char_p()
    rv = _cwipc_util_dll().cwipc_read(filename.encode('utf8'), timestamp, ctypes.byref(errorString))
    if errorString:
        raise CwipcError(errorString.value.decode('utf8'))
    if rv:
        return cwipc(rv)
    return None
    
def cwipc_write(filename, pointcloud):
    """Write a cwipc object to a .ply file."""
    errorString = ctypes.c_char_p()
    rv = _cwipc_util_dll().cwipc_write(filename.encode('utf8'), pointcloud._as_cwipc_p(), ctypes.byref(errorString))
    if errorString:
        raise CwipcError(errorString.value.decode('utf8'))
    return rv
    
def cwipc_from_points(points, timestamp):
    """Create a cwipc from either `cwipc_point_array` or a list or tuple of xyzrgb values"""
    if not isinstance(points, ctypes.Array):
        points = cwipc_point_array(points)
    addr = ctypes.addressof(points)
    nPoint = len(points)
    nBytes = ctypes.sizeof(points)
    errorString = ctypes.c_char_p()
    rv = _cwipc_util_dll().cwipc_from_points(addr, nBytes, nPoint, timestamp, ctypes.byref(errorString))
    if errorString:
        raise CwipcError(errorString.value.decode('utf8'))
    if rv:
        return cwipc(rv)
    return None
    
def cwipc_read_debugdump(filename):
    """Return a cwipc object read from a .cwipcdump file."""
    errorString = ctypes.c_char_p()
    rv = _cwipc_util_dll().cwipc_read_debugdump(filename.encode('utf8'), ctypes.byref(errorString))
    if errorString:
        raise CwipcError(errorString.value.decode('utf8'))
    if rv:
        return cwipc(rv)
    return None
    
def cwipc_write_debugdump(filename, pointcloud):
    """Write a cwipc object to a .cwipcdump file."""
    errorString = ctypes.c_char_p()
    rv = _cwipc_util_dll().cwipc_write_debugdump(filename.encode('utf8'), pointcloud._as_cwipc_p(), ctypes.byref(errorString))
    if errorString:
        raise CwipcError(errorString.value.decode('utf8'))
    return rv
    
def cwipc_synthetic():
    """Returns a cwipc_source object that returns synthetically generated cwipc objects on every get() call."""
    rv = _cwipc_util_dll().cwipc_synthetic()
    return cwipc_source(rv)
    
def main():
    generator = cwipc_synthetic()
    pc = generator.get()
    cwipc_write_debugdump('output.cwipcdump', pc)
    cwipc_write('output.ply', pc)
    
if __name__ == '__main__':
    main()
    
    
