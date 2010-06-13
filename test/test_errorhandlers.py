import unittest

import bottle

from corktools import CorkedServerTest

class ErrorHandlersTest(CorkedServerTest):
  def test406(self):
    @bottle.error(406)
    def handle406(error): pass

    @bottle.route("/406")
    def r406(): return [1, 2, 3]
    
    self.assertStatus(406, '/406')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/406')
    
    @bottle.route("/204")
    def r_none(): pass
    
    self.assertStatus(204, '/204')
    
if __name__ == '__main__':
  unittest.main()
      
    