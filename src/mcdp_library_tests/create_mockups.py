# -*- coding: utf-8 -*-
import os
import tempfile
from mcdp.utils.fileutils import get_mcdp_tmp_dir

__all__ = ['create_hierarchy']

def create_hierarchy(files0):
    """ 
        Creates a temporary directory with the given files 
    
        files = {
            'lib1.mcdplib/poset1': <contents>
        }
    
    """
    flattened = mockup_flatten(files0)
    mcdp_tmp_dir = get_mcdp_tmp_dir()
    prefix = 'mcdp_library_tests_create_hierarchy'
    d = tempfile.mkdtemp(dir=mcdp_tmp_dir, prefix=prefix)
    
    for filename, contents in flattened.items():
        fn = os.path.join(d, filename)
        dn = os.path.dirname(fn)
        if not os.path.exists(dn):
            os.makedirs(dn)
        with open(fn, 'w') as f:
            f.write(contents)
    return d


def mockup_flatten(d): 
    '''
        from
            a:
                b:
                    x
        to 
            'a/b': x
    '''
    res = {}
    for k, v in d.items():
        if isinstance(v, dict):
            x = mockup_add_prefix(k, mockup_flatten(v))
            res.update(x)
        else:
            res[k] = v
    return res
    
    
def mockup_add_prefix(prefix, d):
    res = {}
    for k, v in d.items():
        res['%s/%s' % (prefix, k)] = v
    return res

