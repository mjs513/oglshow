from time import time
from os.path import getsize, basename
import gzip
import zlib
import bz2
import pylzma
import struct
import os
import sys
import webbrowser

from scene import load

# http://blogmag.net/blog/read/38/Print_human_readable_file_size
def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0

def on_disk_size(buf):
    return len(zlib.compress(buf))
    #return len(bz2.compress(buf))
    #return len(pylzma.compress(buf))

def write_bin(sc, fn):
    m = -1
    for t in sc.faces:
        m = max(m, t[0], t[1], t[2])
    print 'max', m

    buffer = []
    for t in sc.faces:
        buffer.append( struct.pack('HHH', t[0], t[1], t[2]) )
    out = ''.join(buffer)

    indices_size = on_disk_size(out)
    print indices_size

    buffer = []
    for p in sc.points:
        buffer.append( struct.pack('ddd', p[0], p[1], p[2]) )

    float_buf = ''.join(buffer)
    verts_size = on_disk_size(float_buf)
    print verts_size

    size = indices_size + verts_size
    index = float(indices_size) / size * 100
    verts = float(verts_size)   / size * 100

    #
    # http://code.google.com/apis/chart/
    #
    # http://chart.apis.google.com/chart?cht=p3&chs=250x100&chd=t:60,40&chl=Hello|World
    # http://chart.apis.google.com/chart?cht=p3&chs=250x100&chd=t:53,46&chl=Index|Verts&chdl=40|60
    base = 'http://chart.apis.google.com/chart?cht=p3'
    url = [base]
    title = 'chtt=%s %s' % (basename(fn), sizeof_fmt(getsize(fn)))
    url.append(title.replace(' ', '+'))
    url.append('chs=300x120') # Dimensions
    datas = ','.join('%d' % s for s in [index, verts])
    url.append('chd=t:' + datas )
    url.append('chl=Index|Verts')

    datas = '|'.join('%d%%' % s for s in [index, verts])
    url.append('chdl=' + datas)

    webbrowser.open('&'.join(url))

    return size
    
N = 100 * 1000
fn = sys.argv[1] if len(sys.argv) > 1 else 'test/data/dragon.obj'
print getsize(fn) / 1024, 'KB'

sc = load(fn)
size = write_bin(sc, fn)
print size / 1024, 'KB'

