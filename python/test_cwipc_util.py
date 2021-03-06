import unittest
import cwipc
import cwipc.playback
import os
import sys
import tempfile
if 0:
    # This code can be used to debug the C++ code in XCode:
    # - build for XCode with cmake
    # - build the cwipc_util project
    # - Fix the pathname for the dylib
    # - run `python3 test_cwipc_util`
    # - Attach to python in the XCode debugger
    # - press return to python3.
    import cwipc.util
    cwipc.util._cwipc_util_dll('/Users/jack/src/VRTogether/cwipc_util/build-xcode/lib/Debug/libcwipc_util.dylib')
    print('Type return after attaching in XCode debugger - ')
    sys.stdin.readline()

#
# Windows search path is horrible. Work around it for testing with an environment variable
#
if 'CWIPC_TEST_DLL' in os.environ:
	import cwipc.util
	filename = os.environ['CWIPC_TEST_DLL']
	dllobj = cwipc.util._cwipc_util_dll(filename)
#
# Find directories for test inputs and outputs
#
if 'CWIPC_TEST_DIR' in os.environ:
    CWIPC_TEST_DIR=os.environ['CWIPC_TEST_DIR']
else:
    _thisdir=os.path.dirname(__file__)
    _topdir=os.path.dirname(_thisdir)
    TEST_FIXTURES_DIR=os.path.join(_topdir, "tests", "fixtures")
    TEST_OUTPUT_DIR=os.path.join(TEST_FIXTURES_DIR, "output")
    if not os.access(TEST_OUTPUT_DIR, os.W_OK):
        TEST_OUTPUT_DIR=tempfile.mkdtemp('cwipc_util_test')
PLY_DIRNAME=os.path.join(TEST_FIXTURES_DIR, "input")
PLY_FILENAME=os.path.join(PLY_DIRNAME, "pcl_frame1.ply")

class TestApi(unittest.TestCase):

    def test_point(self):
        """Can a cwipc_point be created and the values read back?"""
        p = cwipc.cwipc_point(1, 2, 3, 0x10, 0x20, 0x30, 0)
        self.assertEqual(p.x, 1)
        self.assertEqual(p.y, 2)
        self.assertEqual(p.z, 3)
        self.assertEqual(p.r, 0x10)
        self.assertEqual(p.g, 0x20)
        self.assertEqual(p.b, 0x30)
        
    def test_pointarray(self):
        """Can an empty cwipc_point array be created and the values read back?"""
        p = cwipc.cwipc_point_array(count=10)
        self.assertEqual(p[0].x, 0)
        self.assertEqual(p[0].y, 0)
        self.assertEqual(p[0].z, 0)
        self.assertEqual(p[0].r, 0)
        self.assertEqual(p[0].g, 0)
        self.assertEqual(p[0].b, 0)
        self.assertEqual(p[9].x, 0)
        self.assertEqual(p[9].y, 0)
        self.assertEqual(p[9].z, 0)
        self.assertEqual(p[9].r, 0)
        self.assertEqual(p[9].g, 0)
        self.assertEqual(p[9].b, 0)
        with self.assertRaises(IndexError):
            p[10].x
                    
    def test_pointarray_filled(self):
        """Can a cwipc_point array be created with values and the values read back?"""
        p = cwipc.cwipc_point_array(values=[(1, 2, 3, 0x10, 0x20, 0x30, 0), (4, 5, 6, 0x40, 0x50, 0x60, 0)])
        self.assertEqual(len(p), 2)
        self.assertEqual(p[0].x, 1)
        self.assertEqual(p[0].y, 2)
        self.assertEqual(p[0].z, 3)
        self.assertEqual(p[0].r, 0x10)
        self.assertEqual(p[0].g, 0x20)
        self.assertEqual(p[0].b, 0x30)
        self.assertEqual(p[1].x, 4)
        self.assertEqual(p[1].y, 5)
        self.assertEqual(p[1].z, 6)
        self.assertEqual(p[1].r, 0x40)
        self.assertEqual(p[1].g, 0x50)
        self.assertEqual(p[1].b, 0x60)
        with self.assertRaises(IndexError):
            p[2].x
        
    def test_cwipc(self):
        """Can we create and free a cwipc object"""
        pc = cwipc.cwipc()
        pc.free()
        
    def test_cwipc_source(self):
        """Can we create and free a cwipc_source object"""
        pcs = cwipc.cwipc_source()
        pcs.free()
    
    def test_cwipc_from_points(self):
        """Can we create a cwipc object from a list of values"""
        points = cwipc.cwipc_point_array(values=[(1, 2, 3, 0x10, 0x20, 0x30, 1), (4, 5, 6, 0x40, 0x50, 0x60, 2)])
        pc = cwipc.cwipc_from_points(points, 0)
        self.assertEqual(pc.count(), len(points))
        newpoints = pc.get_points()
        self.assertEqual(len(points), len(newpoints))
        for i in range(len(points)):
            op = points[i]
            np = newpoints[i]
            self.assertEqual(op.x, np.x)
            self.assertEqual(op.y, np.y)
            self.assertEqual(op.z, np.z)
            self.assertEqual(op.r, np.r)
            self.assertEqual(op.g, np.g)
            self.assertEqual(op.b, np.b)
            self.assertEqual(op.tile, np.tile)
        pc.free()
    
    def test_cwipc_from_points_empty(self):
        """Can we create a cwipc object from a empty list of values"""
        points = cwipc.cwipc_point_array(values=[])
        pc = cwipc.cwipc_from_points(points, 0)
        newpoints = pc.get_points()
        self.assertEqual(len(points), 0)
        self.assertEqual(len(newpoints), 0)
        pc.free()
    
    def test_cwipc_timestamp_cellsize(self):
        """Can we set and retrieve the timestamp and cellsize in a cwipc"""
        timestamp = 0x11223344556677
        pc = cwipc.cwipc_from_points([(0,0,0,0,0,0,1), (1,0,0,0,0,0,1), (2,0,0,0,0,0,1), (3,0,0,0,0,0,1)], timestamp)
        self.assertEqual(pc.timestamp(), timestamp)
        self.assertEqual(pc.cellsize(), 0)
        pc._set_cellsize(0.1)
        self.assertAlmostEqual(pc.cellsize(), 0.1)
        pc._set_cellsize(-1)
        self.assertAlmostEqual(pc.cellsize(), 1.0)
        pc.free()

    def test_cwipc_read(self):
        """Can we read a cwipc from a ply file?"""
        pc = cwipc.cwipc_read(PLY_FILENAME, 1234)
        self.assertEqual(pc.timestamp(), 1234)
        self._verify_pointcloud(pc)
        pc.free()

    def test_cwipc_read_nonexistent(self):
        """When we read a cwipc from a nonexistent ply file do we get an exception?"""
        with self.assertRaises(cwipc.CwipcError):
            pc = cwipc.cwipc_read(PLY_FILENAME + '.nonexistent', 1234)
    
    def test_cwipc_write(self):
        """Can we write a cwipc to a ply file and read it back?"""
        pc = self._build_pointcloud()
        filename = os.path.join(TEST_OUTPUT_DIR, 'test_cwipc_write.ply')
        cwipc.cwipc_write(filename, pc)
        pc2 = cwipc.cwipc_read(filename, 0)
        self.assertEqual(list(pc.get_points()), list(pc2.get_points()))
    
    def test_cwipc_write_nonexistent(self):
        """When we write a cwipc from a nonexistent ply file do we get an exception?"""
        pc = self._build_pointcloud()
        with self.assertRaises(cwipc.CwipcError):
            pc = cwipc.cwipc_write(os.path.join(PLY_FILENAME, 'non', 'existent'), pc)

    def test_cwipc_write_debugdump(self):
        """Can we write a cwipc to a debugdump file and read it back?"""
        pc = self._build_pointcloud()
        filename = os.path.join(TEST_OUTPUT_DIR, 'test_cwipc_write_debugdump.cwipcdump')
        cwipc.cwipc_write_debugdump(filename, pc)
        pc2 = cwipc.cwipc_read_debugdump(filename)
        self.assertEqual(list(pc.get_points()), list(pc2.get_points()))
    
    def test_cwipc_write_debugdump_nonexistent(self):
        """When we write a cwipc from a nonexistent ply file do we get an exception?"""
        pc = self._build_pointcloud()
        filename = os.path.join(TEST_OUTPUT_DIR, 'test_cwipc_write_debugdump_nonexistent.cwipcdump', 'non', 'existent')
        with self.assertRaises(cwipc.CwipcError):
            cwipc.cwipc_write_debugdump(filename, pc)

    def test_cwipc_synthetic(self):
        """Can we create a synthetic pointcloud?"""
        pcs = cwipc.cwipc_synthetic()
        self.assertTrue(pcs.available(True))
        self.assertTrue(pcs.available(False))
        self.assertFalse(pcs.eof())
        pc = pcs.get()
        self._verify_pointcloud(pc)
        pc.free()
        pcs.free()
        
    def test_cwipc_synthetic_args(self):
        """Can we create a synthetic pointcloud with fps and npoints arguments?"""
        pcs = cwipc.cwipc_synthetic(10, 1000)
        self.assertTrue(pcs.available(True))
        self.assertTrue(pcs.available(False))
        self.assertFalse(pcs.eof())
        pc = pcs.get()
        self._verify_pointcloud(pc)
        pc.free()
        pcs.free()
        
    def test_cwipc_synthetic_tiled(self):
        """Is a synthetic pointcloud generator providing the correct tiling interface?"""
        pcs = cwipc.cwipc_synthetic()
        self.assertEqual(pcs.maxtile(), 3)
        self.assertEqual(pcs.get_tileinfo_dict(0), {'normal':{'x':0, 'y':0, 'z':0},'camera':b'synthetic', 'ncamera':3})
        self.assertEqual(pcs.get_tileinfo_dict(1), {'normal':{'x':0, 'y':0, 'z':1},'camera':b'synthetic', 'ncamera':1})
        self.assertEqual(pcs.get_tileinfo_dict(2), {'normal':{'x':0, 'y':0, 'z':-1},'camera':b'synthetic', 'ncamera':2})
        pcs.free()

    def test_tilefilter(self):
        """Check that the tilefilter returns the same number of points if not filtering, and correct number if filtering"""
        gen = cwipc.cwipc_synthetic()
        pc_orig = gen.get()
        pc_filtered = cwipc.cwipc_tilefilter(pc_orig, 0)
        self.assertEqual(len(pc_orig.get_points()), len(pc_filtered.get_points()))
        pc_filtered_1 = cwipc.cwipc_tilefilter(pc_orig, 1)
        pc_filtered_2 = cwipc.cwipc_tilefilter(pc_orig, 2)
        self.assertEqual(len(pc_orig.get_points()), len(pc_filtered_1.get_points()) + len(pc_filtered_2.get_points()))
        self.assertEqual(pc_orig.timestamp(), pc_filtered_1.timestamp())
        self.assertEqual(pc_orig.timestamp(), pc_filtered_2.timestamp())
        gen.free()
        pc_orig.free()
        pc_filtered.free()
        pc_filtered_1.free()
        pc_filtered_2.free()
        
    def test_tilefilter_empty(self):
        """Check that the tilefilter returns an empty pointcloud when passed an empty pointcloud"""
        pc_orig = cwipc.cwipc_from_points([], 0)
        pc_filtered = cwipc.cwipc_tilefilter(pc_orig, 0)
        self.assertEqual(len(pc_orig.get_points()), 0)
        self.assertEqual(len(pc_filtered.get_points()), 0)
        pc_orig.free()
        pc_filtered.free()
        
    def test_downsample(self):
        """Check that the downsampler returns at most the same number of points and eventually returns 1"""
        gen = cwipc.cwipc_synthetic()
        pc_orig = gen.get()
        count_orig = len(pc_orig.get_points())
        count_prev = count_orig
        factor = 1024
        while factor > 0.0001:
            pc_filtered = cwipc.cwipc_downsample(pc_orig, factor)
            count_filtered = len(pc_filtered.get_points())
            self.assertGreaterEqual(count_filtered, 1)
            self.assertLessEqual(count_filtered, count_orig)
            self.assertEqual(pc_orig.timestamp(), pc_filtered.timestamp())
            count_prev = count_filtered
            pc_filtered.free()
            if count_filtered > count_orig/2:
                break
            factor = factor / 2
        gen.free()
        pc_orig.free()
        
    def test_downsample_empty(self):
        """Check that the downsample returns an empty pointcloud when passed an empty pointcloud"""
        pc_orig = cwipc.cwipc_from_points([], 0)
        pc_filtered = cwipc.cwipc_downsample(pc_orig, 1)
        self.assertEqual(len(pc_orig.get_points()), 0)
        self.assertEqual(len(pc_filtered.get_points()), 0)
        pc_orig.free()
        pc_filtered.free()
        
    def test_playback_file(self):
        src = cwipc.playback.cwipc_playback([PLY_FILENAME], ply=True, loop=False)
        self.assertFalse(src.eof())
        pc = src.get()
        self._verify_pointcloud(pc)
        pc.free()
        self.assertTrue(src.eof())
        src.free()

    def test_playback_dir(self):
        src = cwipc.playback.cwipc_playback(PLY_DIRNAME, ply=True, loop=False)
        self.assertFalse(src.eof())
        pc = src.get()
        self._verify_pointcloud(pc)
        pc.free()
        src.free()

    def _verify_pointcloud(self, pc, tiled=False):
        points = pc.get_points()
        self.assertGreater(len(points), 1)
        p0 = points[0].x, points[0].y, points[0].z
        p1 = points[len(points)-1].x, points[len(points)-1].y, points[len(points)-1].z
        self.assertNotEqual(p0, p1)
        if tiled:
            t0 = points[0].tile
            t1 = points[len(points)-1].tile
            self.assertNotEqual(t0, t1)
    
    def _build_pointcloud(self):
         points = cwipc.cwipc_point_array(values=[(1, 2, 3, 0x10, 0x20, 0x30, 1), (4, 5, 6, 0x40, 0x50, 0x60, 2)])
         return cwipc.cwipc_from_points(points, 0)
   
if __name__ == '__main__':
    unittest.main()
