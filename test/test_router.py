import unittest
import bottle

class TestRouter(unittest.TestCase):
    def setUp(self):
        self.r = r = bottle.Router()

    def testBasic(self):
        add = self.r.add
        match = self.r.match
        add('/static', 'static')
        self.assertMatches('/static', 'static')
        add('/\\:its/:#.+#/:test/:name#[a-z]+#/', 'handler')
        self.assertMatches('/:its/a/cruel/world/', 'handler', {'test': 'cruel', 'name': 'world'})
        add('/:test', 'notail')
        self.assertMatches('/test', 'notail', {'test': 'test'})
        add(':test/', 'nohead')
        self.assertMatches('test/', 'nohead', {'test': 'test'})
        add(':test', 'fullmatch')
        self.assertMatches('test', 'fullmatch', {'test': 'test'})
        add('/:#anon#/match', 'anon')
        self.assertMatches('/anon/match', 'anon')
        self.assertFalse(match('//no/m/at/ch/'), "Expecting empty list of matches")
        

    def testParentheses(self):
        add = self.r.add
        match = self.r.match
        add('/func(:param)', 'func')
        self.assertMatches('/func(foo)', 'func', {'param':'foo'})
        add('/func2(:param#(foo|bar)#)', 'func2')
        self.assertMatches('/func2(foo)', 'func2', {'param':'foo'})
        self.assertMatches('/func2(bar)', 'func2', {'param':'bar'})
        self.assertFalse( match('/func2(baz)'), "Expecting empty list of matches") 
        add('/groups/:param#(foo|bar)#', 'groups')
        self.assertMatches('/groups/foo', 'groups', {'param':'foo'})

    def testErrorInPattern(self):
        self.assertRaises(bottle.RouteSyntaxError, self.r.add, '/:bug#(#/', 'buggy')

    def testBuild(self):
        add = self.r.add
        build = self.r.build
        add('/:test/:name#[a-z]+#/', 'handler', name='testroute')
        add('/anon/:#.#', 'handler', name='anonroute')
        url = build('testroute', test='hello', name='world')
        self.assertEqual('/hello/world/', url)
        self.assertRaises(bottle.RouteBuildError, build, 'test')
        # RouteBuildError: No route found with name 'test'.
        self.assertRaises(bottle.RouteBuildError, build, 'testroute')
        # RouteBuildError: Missing parameter 'test' in route 'testroute'
        #self.assertRaises(bottle.RouteBuildError, build, 'testroute', test='hello', name='1234')
        # RouteBuildError: Parameter 'name' does not match pattern for route 'testroute': '[a-z]+'
        #self.assertRaises(bottle.RouteBuildError, build, 'anonroute')
        # RouteBuildError: Anonymous pattern found. Can't generate the route 'anonroute'.
        
    def assertMatches(self, uri, handler_name, params={}, method='GET'):
        match = self.r.match
        expected_value = match(uri)
        self.assertEquals(len(expected_value), 1)
        tpl = expected_value[0].get(method)
        self.assertTrue(tpl != None, "Method doesn't match")
        self.assertEquals(handler_name, tpl[0])
        if params:
            expected_params = tpl[1].match(uri).groupdict()
            self.assertEquals(params, expected_params)

if __name__ == '__main__':
    unittest.main()
