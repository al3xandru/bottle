import unittest

import bottle
from corktools import CorkedServerTest

class ContentNegociation(CorkedServerTest):
  def testEmptyReturn(self):
    @bottle.route('/null')
    def r_null(): pass
    
    self.assertStatus(204, '/null')
    self.assertBody('', '/null')

    self.assertStatus(200, '/null', method='HEAD')
    
    @bottle.route('/null-post', method='POST')
    def r_null(): pass
    
    self.assertStatus(405, '/null-post', method='HEAD')
    
  def testHTTPError(self):
    @bottle.route('/error_return')
    def error_return(): return bottle.HTTPError(code=404)
    
    self.assertStatus(404, '/error_return')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/error_return')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/error_return', env={'HTTP_ACCEPT': 'text/html; q=0.5, text/plain; q=0.9'})
    
    @bottle.route('/error_raise')
    def error_raise(): raise bottle.HTTPError(code=501)
    
    self.assertStatus(501, '/error_raise')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/error_return')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/error_return', env={'HTTP_ACCEPT': 'text/html; q=0.5, text/plain; q=0.9'})    
    
    
  def testNoMediaType(self):
    @bottle.route('/unicode')
    def r_unicode(): return u'unicode'
    
    self.assertStatus(200, '/unicode')
    self.assertBody('unicode', '/unicode')
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/unicode')
    
    # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.7
    # HTTP/1.1 servers are allowed to return responses which are
    #  not acceptable according to the accept headers sent in the
    #  request. In some cases, this may even be preferable to sending a
    #  406 response.
    self.assertStatus(200, '/unicode', env={'HTTP_ACCEPT': 'application/xhtml'})
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/unicode')
    
    @bottle.route('/str')
    def r_str(): return 'str'
    
    self.assertStatus(200, '/str')
    self.assertBody('str', '/str')
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/str')    
    
  def testStaticFiles(self):
    @bottle.route('/static_file')
    def static(): return bottle.static_file('test_contentnegociation.py', root='.')

    self.assertStatus(200, '/static_file')
    self.assertHeader('Content-Type', 'text/x-python', '/static_file')
    
    # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.7
    self.assertStatus(200, '/static_file', env={'HTTP_ACCEPT': 'application/xml'})
    self.assertHeader('Content-Type', 'text/x-python', '/static_file')
    
  def testFilters(self):
    self.app.add_filter(list, lambda out: 'list', ['text/plain'])
    
    @bottle.route('/list')
    def r_list(): return [1, 2, 3]
    
    self.assertStatus(200, '/list')
    self.assertBody('list', '/list')
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/list')
    
    self.assertStatus(406, '/list', env={'HTTP_ACCEPT': 'application/xml'})
    
  def testAdvancedFilters(self):
    def to_b(out):
      from bottle import response
      response.content_type = 'text/html'
      return 'B'
    self.app.add_filter(A, lambda out: 'A', ['text/plain'])
    self.app.add_filter(B, to_b, ['text/html'])
    self.app.add_filter(C, lambda out: 'C', ['text/plain'])
    
    @bottle.route('/b')
    def r_b(): return B()
    
    @bottle.route('/c')
    def r_c(): return C()
    
    ACCEPT_HEADERS = {'HTTP_ACCEPT': 'text/plain, text/html; q=0.8'}
    self.assertStatus(200, '/b', env=ACCEPT_HEADERS)
    self.assertBody('A', '/b', env=ACCEPT_HEADERS)
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/b', env=ACCEPT_HEADERS)
    
    ACCEPT_HEADERS = {'HTTP_ACCEPT': ' text/html, text/plain; q=0.9'}
    self.assertStatus(200, '/b', env=ACCEPT_HEADERS)
    self.assertBody('B', '/b', env=ACCEPT_HEADERS)
    self.assertHeader('Content-Type', 'text/html', '/b', env=ACCEPT_HEADERS)
    
    ACCEPT_HEADERS = {'HTTP_ACCEPT': 'text/plain, text/html; q=0.8'}
    self.assertBody('C', '/c', env=ACCEPT_HEADERS)
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/c', env=ACCEPT_HEADERS)
    
import functools
from tools import ServerTestBase

from cork import MediaTypeFilter, option_route, option

class StandardContentNegociation(ServerTestBase):
  def testEmptyReturn(self):
    route  = functools.partial(option_route, self.app)
    mtf = MediaTypeFilter()
    self.app.add_filter(option, mtf.filter)

    @route('/null')
    def r_null(): pass
    
    self.assertStatus(204, '/null')
    self.assertBody('', '/null')

    self.assertStatus(200, '/null', method='HEAD')
    
    @route('/null-post', method='POST')
    def r_null(): pass
    
    self.assertStatus(405, '/null-post', method='HEAD')
    
  def testHTTPError(self):
    route  = functools.partial(option_route, self.app)
    mtf = MediaTypeFilter()
    self.app.add_filter(option, mtf.filter)

    @route('/error_return')
    def error_return(): 
      import bottle
      return bottle.HTTPError(code=404)
    
    self.assertStatus(404, '/error_return')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/error_return')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/error_return', env={'HTTP_ACCEPT': 'text/html; q=0.5, text/plain; q=0.9'})
    
    @route('/error_raise')
    def error_raise(): 
      import bottle
      raise bottle.HTTPError(code=501)
    
    self.assertStatus(501, '/error_raise')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/error_return')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/error_return', env={'HTTP_ACCEPT': 'text/html; q=0.5, text/plain; q=0.9'})    

  def testNoMediaType(self):
    route  = functools.partial(option_route, self.app)
    mtf = MediaTypeFilter()
    self.app.add_filter(option, mtf.filter)
    
    @route('/unicode')
    def r_unicode(): return u'unicode'
    
    self.assertStatus(200, '/unicode')
    self.assertBody('unicode', '/unicode')
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/unicode')
    
    # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.7
    # HTTP/1.1 servers are allowed to return responses which are
    #  not acceptable according to the accept headers sent in the
    #  request. In some cases, this may even be preferable to sending a
    #  406 response.
    self.assertStatus(200, '/unicode', env={'HTTP_ACCEPT': 'application/xhtml'})
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/unicode')
    
    @route('/str')
    def r_str(): return 'str'
    
    self.assertStatus(200, '/str')
    self.assertBody('str', '/str')
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/str')   
    
  def testStaticFiles(self):
    route  = functools.partial(option_route, self.app)
    mtf = MediaTypeFilter()
    self.app.add_filter(option, mtf.filter)

    @route('/static_file')
    def static(): 
      from bottle import static_file
      return static_file('test_contentnegociation.py', root='.')

    self.assertStatus(200, '/static_file')
    self.assertHeader('Content-Type', 'text/x-python', '/static_file')
    
    # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.7
    self.assertStatus(200, '/static_file', env={'HTTP_ACCEPT': 'application/xml'})
    self.assertHeader('Content-Type', 'text/x-python', '/static_file')
    
  def testFilters(self):
    route  = functools.partial(option_route, self.app)
    mtf = MediaTypeFilter()
    self.app.add_filter(option, mtf.filter)
    
    mtf.add_filter(lambda out: 'list', list, ['text/plain'])
    
    @route('/list')
    def r_list(): return [1, 2, 3]
    
    self.assertStatus(200, '/list')
    self.assertBody('list', '/list')
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/list')
    
    self.assertStatus(406, '/list', env={'HTTP_ACCEPT': 'application/xml'})
    
  def testAdvancedFilters(self):
    route  = functools.partial(option_route, self.app)
    mtf = MediaTypeFilter()
    self.app.add_filter(option, mtf.filter)
    
    def to_b(out):
      from bottle import response
      response.content_type = 'text/html'
      return 'B'
    mtf.add_filter(lambda out: 'A', A, ['text/plain'])
    mtf.add_filter(to_b, B, ['text/html'])
    mtf.add_filter(lambda out: 'C', C, ['text/plain'])
    
    @route('/b')
    def r_b(): return B()
    
    @route('/c')
    def r_c(): return C()
    
    ACCEPT_HEADERS = {'HTTP_ACCEPT': 'text/plain, text/html; q=0.8'}
    self.assertStatus(200, '/b', env=ACCEPT_HEADERS)
    self.assertBody('A', '/b', env=ACCEPT_HEADERS)
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/b', env=ACCEPT_HEADERS)
    
    ACCEPT_HEADERS = {'HTTP_ACCEPT': ' text/html, text/plain; q=0.9'}
    self.assertStatus(200, '/b', env=ACCEPT_HEADERS)
    self.assertBody('B', '/b', env=ACCEPT_HEADERS)
    self.assertHeader('Content-Type', 'text/html', '/b', env=ACCEPT_HEADERS)
    
    ACCEPT_HEADERS = {'HTTP_ACCEPT': 'text/plain, text/html; q=0.8'}
    self.assertBody('C', '/c', env=ACCEPT_HEADERS)
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/c', env=ACCEPT_HEADERS)
    
                        
class A(object): pass

class B(A): pass

class C(B): pass

if __name__ == '__main__':
  unittest.main()
