import unittest

import bottle
from corktools import CorkedServerTest

class ContentNegociation(CorkedServerTest):
  def testNoMediaType(self):
    @bottle.route('/null')
    def null(): pass

    self.assertStatus(204, '/null')
    self.assertBody('', '/null')

    @bottle.route('/error_return')
    def error_return(): return bottle.HTTPError(code=404)
    
    self.assertStatus(404, '/error_return')
    
    @bottle.route('/error_raise')
    def error_raise(): raise bottle.HTTPError(code=501)
    
    self.assertStatus(501, '/error_raise')
    
    @bottle.route('/unicode')
    def r_unicode(): return u'unicode'
    
    self.assertStatus(200, '/unicode')
    self.assertBody('unicode', '/unicode')
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/unicode')
    
    self.assertStatus(406, '/unicode', env={'HTTP_ACCEPT': 'application/xhtml'})
    
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
    
    #self.assertStatus(406, '/static_file', env={'HTTP_ACCEPT': 'application/xml'})
    
  def testFilters(self):
    self.app.add_filter(list, list_mapper, ['text/plain'])
    
    @bottle.route('/list')
    def r_list(): return [1, 2, 3]
    
    self.assertStatus(200, '/list')
    self.assertBody('list', '/list')
    
    #self.assertStatus(406, '/list', env={'HTTP_ACCEPT': 'application/xml'})
    
  def testAdvancedFilters(self):
    self.app.add_filter(A, lambda out: 'A', ['text/plain'])
    self.app.add_filter(B, lambda out: 'B', ['text/html'])
    self.app.add_filter(C, lambda out: 'C', ['text/plain'])
    
    @bottle.route('/b')
    def r_b(): return B()
    
    @bottle.route('/c')
    def r_c(): return C()
    
    self.assertStatus(200, '/b', env={'HTTP_ACCEPT': 'text/plain, text/html; q=0.8'})
    self.assertBody('A', '/b', env={'HTTP_ACCEPT': 'text/plain, text/html; q=0.8'})
    
    self.assertBody('C', '/c', env={'HTTP_ACCEPT': 'text/plain, text/html; q=0.8'})
                        
def list_mapper(out):
  return "list"

class A(object): pass

class B(A): pass

class C(B): pass

if __name__ == '__main__':
  unittest.main()