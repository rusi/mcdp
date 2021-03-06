from collections import defaultdict
import logging
import urlparse

from webtest.app import AppError

import xml.sax.saxutils as saxutils
from mcdp.exceptions import DPInternalError


logger = logging.getLogger('mcdp.spider')
logger.setLevel(logging.DEBUG)

class Spider(object):
    def __init__(self, get_maybe_follow, ignore=None):
        self.get_maybe_follow = get_maybe_follow
        if ignore is None:
            ignore = lambda _url, _parsed: False
        self.ignore = ignore
        self.queue = []
        self.skipped = set()
        # 
        self.failed = {} # url -> Exception
        # 404
        self.not_found = {} # url -> Exception
        self.visited = {} # url -> Response
        self.referrers = defaultdict(lambda: set()) # url -> url referred to
        
    def visit(self, url):
        self.queue.append(url)
                          
    def go(self, max_fails=None, max_pages=None):
        while self.queue:
            self.step()
            if max_fails is not None:
                if len(self.failed) >= max_fails:
                    msg = 'Exiting because of max fails reached.'
                    logger.debug(msg)
                    break
                
            if max_pages is not None:
                if len(self.visited) > max_pages:
                    msg = 'Exiting because of max_pages = %d reached.' % max_pages
                    logger.debug(msg)
                    break
            
    def step(self):
        url = self.queue.pop(-1)
        if url in self.visited:
            return
        o = urlparse.urlparse(url)
        
        if self.ignore(url, o):
            self.skipped.add(url)
            return
        
        logger.debug('requests %s ... ' % url)
        
        try:
            url2, res = self.get_maybe_follow(url)
        except AppError as e:
            s = unicode(e).encode('utf8')
            s = saxutils.unescape(s)
            if '500' in s:
                self.failed[url] = s
                logger.error('failed %s' % url)
                return
            elif '404' in s:
                self.not_found[url] = s
                logger.error('not found %s' % url)
                return
            else:
                msg = 'Cannot classify this as 404 or 500:'
                msg += '\n' + str(s)
                raise DPInternalError(msg)

        if url2 != url:
            self.visited[url] = 'redirect to %s' % url2
            logger.debug('redirected %s -> %s' % (url, url2))
            
        self.visited[url2] = res
        
        if res.content_type == 'text/html':
            #print res.html
            urls = list(find_links(res.html, url2))
            logger.debug('read %s %s: %d links' % (url2, res.status, len(urls)))
            for u in urls:
                p = urlparse.urlparse(u)
                invalid = False
                invalid = invalid or '../../../' in p.path
                invalid = invalid or '//' in p.path
                
                if invalid:
                    msg = 'We generated a URL that is weird: '
                    msg += '\n URL: %s ' % u
                    msg += '\n generated by: %s ' % url2
                    if url != url2:
                        msg += '\n redirected from: %s ' % url
                    raise ValueError(msg)
                self.queue.append(u)
                self.referrers[u].add(url2)
    
    def log_summary(self):
        logger.info('Visited: %d' % len(self.visited))
        logger.info('Skipped: %d' % len(self.skipped))
        if self.failed:
            logger.error('Failed: %d' % len(self.failed))
        else:
            logger.info('No failures')
        if self.not_found:
            logger.error('Not found: %d' % len(self.not_found))
        else:
            logger.info('No 404s.')
        for url in sorted(self.visited):
            logger.info('visited %s' % url)
        # for url in sorted(self.skipped):
        # logger.debug('skipped %s' % url)
        for url in sorted(self.not_found):
            logger.error('not found %s' % url)
        for url in sorted(self.failed):
            logger.error('failed %s' % url)
            for r in self.referrers[url]:
                logger.error(' referred from %s' % r)
                _u0 = list(self.referrers[url])[0]
                # logger.debug(indent(self.visited[u0].body, ' referrer page '))

            logger.error(self.failed[url])



def find_links(html, url_base):
    '''
        Ignores "data:" urls in images.
    '''   
    def find(): 
        for link in html.select('link[href]'):
            yield link['href']
        for script in html.select('script[src]'):
            yield script['src']
        for img in html.select('img[src]'):
            if img['src'].startswith('data:'):
                continue
            yield img['src']
        for a in html.select('a[href]'):
            yield a['href']
    for url in find(): 
        yield urlparse.urljoin(url_base, url).encode('utf8')
