import sys

from mcdp_utils_xml.parsing import bs
import os
from collections import OrderedDict, namedtuple

GenericReference = namedtuple('GenericReference', 'id url title')

def read_references(dirname, base_url, prefix):
    from mcdp_docs.mcdp_render_manual import look_for_files
    filenames = look_for_files([dirname], "*.html")
    res = OrderedDict()
    for f in filenames:
        contents = open(f).read()
        a = bs(contents)
        rel = os.path.relpath(os.path.realpath(f), os.path.realpath(dirname))
        for element in a.select('[id]'):
            id_ = element.attrs['id']
            url = base_url + '/' + rel + '#' + id_
            ident = element.select('span.ident')
            if ident:
                title = str(ident[0]) 
            else:
                title = None
            res[prefix + id_] = GenericReference(id_, url, title)
    return res
            
if __name__ == '__main__':
    dirname = sys.argv[1]
    base_url = 'base:'
    res = read_references(dirname, base_url, 'python:')
    for k,v in res.items():
        print('%s: %s' % (k, v))