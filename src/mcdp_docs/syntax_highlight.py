from mcdp import logger

try:
    import pygments  # @UnusedImport
except ImportError:
    msg = 'New dependency: pygments. Install with:'
    msg += '\n\n    pip install --user pygments pygments_markdown_lexer'
    logger.error(msg)
    raise Exception(msg)
    
from pygments.lexers import get_lexer_by_name

from bs4.element import Tag, NavigableString
from mcdp_utils_xml.parsing import bs

def strip_pre(soup):
    es = list(soup.select('[trim]'))
    for element in es:
        children = list(element.children)
        if children:
            s = list(element.children)[0]
            if isinstance(s, NavigableString):
                s2 = s.lstrip()
                if s != s2:
                    element.attrs['trimmed'] = 1
                    s.replace_with(s2)
            s = list(element.children)[-1]
            if isinstance(s, NavigableString):
                s2 = s.rstrip()
                if s != s2:
                    element.attrs['trimmed'] = 1
                    s.replace_with(s2)
            
    
def syntax_highlighting(soup):
    
    from pygments import highlight
    from pygments.formatters import HtmlFormatter  # @UnresolvedImport
    
    languages = [
        ('markdown', is_markdown, get_lexer_by_name('markdown', stripall=True)),
        ('python', is_python, get_lexer_by_name('python', stripall=True)),
        ('xml', is_xml, get_lexer_by_name('xml', stripall=True)),
        ('yaml', is_yaml,get_lexer_by_name('yaml', stripall=True)),
        ('cmake', is_cmake, get_lexer_by_name('cmake', stripall=True)),
        ('bash', is_bash, get_lexer_by_name('bash', stripall=True)),
        ('latex', is_latex, get_lexer_by_name('latex', stripall=True)),
    ]
    
    formatter = HtmlFormatter(linenos=False, cssclass="source")

    styles = formatter.get_style_defs(arg='')
    style = Tag(name='style')
    style.append(styles)
    soup.append(style)
    
     
    codes = list(soup.select('code'))
#     logger.info('codes: %s' % codes)
    for code in codes:
        if code.parent.name != 'pre':
            continue
        text = code.text
        
        def subwith(s):
            result = bs(s)
            result.name = 'div'
            pre = result.find('pre')
            pre.name = 'code'
            Pre = Tag(name='pre')
            Pre.append(pre)
            try:
                code.parent.replace_with(Pre)
            except:
                logger.debug(str(code.parent))
                raise
        
        for name, cond, lexer in languages:
            if name in code.attrs.get('class','') or cond(code):
                result = highlight(text, lexer, formatter)
                subwith(result)
                break
            
#             logger.debug(indent(code.text, 'not python: '))

def is_xml(e):
    assert e.name == 'code'
    t = e.text
    ok = False
    ok |= '/>' in t
    ok |= '</' in t
    ok |= '<div>' in t
    ok |= '<launch>' in t
    return ok

def is_markdown(e):
    assert e.name == 'code'
    t = e.text
    ok = False
    ok = ok or '[](' in t
    return ok

def is_python(e):
    assert e.name == 'code'
    t = e.text
    ok = False
    ok = ok or 'def ' in t
    ok = ok or 'rospy.' in t
    ok = ok or 'self.' in t
    ok = ok or 'generate_distutils_setup' in t
    ok = ok or 'from ' in t and ' import ' in t
    return ok

def is_yaml(e):
    assert e.name == 'code'
    t = e.text
    ok = False
    ok = ok or 'description:' in t
    return ok


def is_bash(e):
    assert e.name == 'code'
    t = e.text
    ok = False
    ok = ok or '#!/bin/bash' in t
    return ok

def is_cmake(e):
    assert e.name == 'code'
    t = e.text
    ok = False
    ok = ok or 'find_package' in t
    ok = ok or 'project(' in t
    ok = ok or 'catkin_python_setup(' in t
    return ok


def is_latex(e):
    assert e.name == 'code'
    t = e.text
    ok = False 
    ok = ok or r'\begin{' in t
    return ok
