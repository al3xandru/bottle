# -*- coding: utf-8 -*-
import unittest
import bottle

from tools import ServerTestBase

class TestHttpResponse(ServerTestBase):
  #def testReturnHttpResponse(self):
    #@bottle.route('/200')
    #def test200(): return bottle.HTTPResponse(output='normal output')
    
    #self.assertStatus(200, '/200')
    #self.assertBody('normal output', '/200')
    
    #@bottle.route('/404')
    #def test404(): return bottle.HTTPResponse(output="404 not found", status=404)
    
    #self.assertStatus(404, '/404')
    #self.assertBody('404 not found', '/404')
  
  def testRaiseHttpResponse(self):
    @bottle.route('/200')
    def test200(): raise bottle.HTTPResponse(output='normal output')
    
    self.assertStatus(200, '/200')
    self.assertBody('normal output', '/200')
    
    @bottle.route('/404')
    def test404(): raise bottle.HTTPResponse(output="404 not found", status=404)
    
    self.assertStatus(404, '/404')
    self.assertBody('404 not found', '/404')

  def testRedirect(self):
    @bottle.route('/303')
    def test(): bottle.redirect('/200')
    
    self.assertStatus(303, '/303')
    self.assertHeader('Location', 'http://127.0.0.1/200', '/303')

    @bottle.route('/301')
    def test(): bottle.redirect('/200', code=301)
    
    self.assertStatus(301, '/301')
    self.assertHeader('Location', 'http://127.0.0.1/200', '/301')

  
  #def testReturnHttpError(self):
    #@bottle.route('/200')
    #def test200(): return bottle.HTTPError(code=200)
    
    #self.assertStatus(200, '/200')
    #self.assertInBody('<pre>Unknown Error</pre>', '/200')
    #self.assertInBody('<title>Error 200: Ok</title>', '/200')
    
    #@bottle.route('/500')
    #def test500(): return bottle.HTTPError()
    
    #self.assertStatus(500, '/500')
    #self.assertInBody('<title>Error 500: Internal Server Error</title>', '/500')
  
  #def testRaiseHttpError(self):
    #@bottle.route('/200')
    #def test200(): raise bottle.HTTPError(code=200)
    
    #self.assertStatus(200, '/200')
    #self.assertInBody('<pre>Unknown Error</pre>', '/200')
    #self.assertInBody('<title>Error 200: Ok</title>', '/200')

    
    #@bottle.route('/500')
    #def test500(): raise bottle.HTTPError()
    
    #self.assertStatus(500, '/500')
    #self.assertInBody('<title>Error 500: Internal Server Error</title>', '/500')
    
  #def testNotFound(self):
    #self.assertStatus(404, '/404')
    #self.assertInBody('<title>Error 404: Not Found</title>', '/404')

if __name__ == '__main__':
    unittest.main()