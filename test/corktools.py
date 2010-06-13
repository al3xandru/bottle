import wsgiref

import bottle
import bottlecork
import tools


class CorkedServerTest(tools.ServerTestBase):
  def setUp(self):
    super(CorkedServerTest, self).setUp()
    self.app = bottle.app.push(bottlecork.BottleCork())
    self.wsgiapp = wsgiref.validate.validator(self.app)
