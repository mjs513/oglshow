
import sys
sys.path.insert(0, 'cpython/build/lib.macosx-10.5-i386-2.5')

from scene import ArgsOptions, load
from cobj import setup, projall, gethits

def scene2c():
    ao = ArgsOptions()
    options = [ao.options.fn,
               ao.options.verbose,
               ao.options.procedural]
    return load(*options)

sc = scene2c()
print sc

setup([p.pos for p in sc.objets[0].g.points], 
      sc.objets[0].g.index)

model = [-0.62869209,  0.77656037 , -0.04123428  , 0. ,
  0.22454762,  0.13051406 , -0.9656834   , 0. ,      
 -0.74452978, -0.61637658 , -0.25642794  , 0.        
 -0.03640071, -0.0022433  , -0.45071667  , 1.        ]
proj = [ 3.02691031,  0.         ,  0.          , 0.        ,
  0.        ,  3.4874146  ,  0.          , 0.        ,
  0.        ,  0.         , -1.01390326, -1.        ,
 -0.        , -0.         , -0.01119764, -0.        ]
view = [  0,   0, 674, 585]

projall(model, proj, view)

gethits(50, 50)

