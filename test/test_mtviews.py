import bottle
import unittest

from tools import ServerTestBase

from mtviews import jinja2_view as view

# curl -X GET http://localhost:8080/get_dict => start 1
#
# curl -X GET http://localhost:8080/get_list => 406 !!!
#
# curl -H "Accept: text/html" -X GET http://localhost:8080/single_template_dict => <html>Param: {'a': 'A', 'b': 'B'}</html>
# curl -H "Accept: text/plain" -X GET http://localhost:8080/single_template_dict => Text Plain Param: {'a': 'A', 'b': 'B'}
# curl -H "Accept: application/xml" -X GET http://localhost:8080/single_template_dict => 500 (template not found)s
# curl  -X GET http://localhost:8080/single_template_dict => <html>Param: {'a': 'A', 'b': 'B'}. Extra param: titilola</html>
#
# curl -H "Accept: text/html" -X GET http://localhost:8080/single_template_nondict => <html>Param: set([1, 2, 3])</html>
# curl -X GET http://localhost:8080/single_template_nondict => <html>Param: set([1, 2, 3]). Extra param: titilola</html>
#
# curl -X GET http://localhost:8080/single_template_genericmt => <html>Param: {'a': 'A', 'b': 'B'}. Extra param: titilola
# curl -H "Accept: application/xml" -X GET http://localhost:8080/single_template_genericmt => 406 !!!
#
# curl  -X GET http://localhost:8080/complete_templates => <html>Param: {'a': 'A', 'b': 'B'}. Extra param: titilola</html>
# curl -H "Accept: text/html" -X GET http://localhost:8080/complete_templates => <html>Param: {'a': 'A', 'b': 'B'}. Extra param: titilola</html>
# curl -H "Accept: text/*" -X GET http://localhost:8080/complete_templates => <html>Param: {'a': 'A', 'b': 'B'}. Extra param: titilola</html>
# curl -H "Accept: text/plain;q=0.8, text/*;q=0.6" -X GET http://localhost:8080/complete_templates => Text Plain Param: {'a': 'A', 'b': 'B'} Extra param: titilola
# curl -H "Accept: application/xml" -X GET http://localhost:8080/complete_templates => <xml>atom</xml>
# curl -H "Accept: application/json" -X GET http://localhost:8080/complete_templates => json
# 


class TestWsgi(ServerTestBase):
  def testDictNoMediaDefinition(self):
    @bottle.route('/get_dict')
    @view(template='jinja2_simple', extra_param='titilola')
    def get_dict():
      return dict(var='1', key2='2')
    
    self.assertBody('start 1 end', '/get_dict')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/get_dict')
    
  def testNonDictNoMediaDef(self):
    @bottle.route('/get_list')
    @view(template='jinja2_inherit.tpl', extra_param='titilola')
    def get_list():
      return ['item1', 'item2', 'item3']
    
    self.assertBody('item1item2item3', '/get_list')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/get_list')
    
  def testDictSingleTemplateManyFormats(self):
    @bottle.route('/single_template_dict')
    @view(template='mtviews_jj2', formats=['text/html', 'text/plain', 'application/xml'], extra_param='titilola')
    def single_template_dict():
      return dict(it={'a': 'A', 'b': 'B'}, key2='2')
    
    self.assertInBody('<html>', '/single_template_dict')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/single_template_dict')

    self.assertInBody('<html>', '/single_template_dict', env={'HTTP_ACCEPT': 'text/html'})
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/single_template_dict', env={'HTTP_ACCEPT': 'text/html'})

    self.assertInBody('Text Plain', '/single_template_dict', env={'HTTP_ACCEPT': 'text/plain'})
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/single_template_dict', env={'HTTP_ACCEPT': 'text/plain'})

    #self.assertInBody('<xml>', '/single_template_dict', env={'HTTP_ACCEPT': 'application/xml'})
    #self.assertHeader('Content-Type', 'application/xml; charset=UTF-8', '/single_template_dict', env={'HTTP_ACCEPT': 'application/xml'})
    
  def testNonDictSingleTemplManyFormats(self):
    @bottle.route('/single_template_nondict')
    @view(template='mtviews_jj2', formats=['text/html', 'text/plain', 'application/xml'], extra_param='titilola')
    def single_template():
      return set([1, 2, 3])
    
    self.assertInBody('<html>', '/single_template_nondict')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/single_template_nondict')

    self.assertInBody('<html>', '/single_template_nondict', env={'HTTP_ACCEPT': 'text/html'})
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/single_template_nondict', env={'HTTP_ACCEPT': 'text/html'})
    
    self.assertInBody('Text Plain', '/single_template_nondict', env={'HTTP_ACCEPT': 'text/plain'})
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/single_template_nondict', env={'HTTP_ACCEPT': 'text/plain'})
    
  def testDictGenericFormat(self):
    @bottle.route('/single_template_genericmt')
    @view(template='mtviews_jj2', formats=['html'], extra_param='titilola')
    def single_template_genericmt():
      return dict(it={'a': 'A', 'b': 'B'}, key2='2')

    self.assertInBody('<html>', '/single_template_genericmt')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/single_template_genericmt')
    
    self.assertInBody('{', '/single_template_genericmt', env={'HTTP_ACCEPT': 'application/xml'})
    self.assertHeader('Content-Type', 'application/json', '/single_template_genericmt', env={'HTTP_ACCEPT': 'application/xml'})

  def testComplexFormatMappings(self):
    @bottle.route('/complete_templates')
    @view(mappings={'text/html': 'mtviews_jj2.text.html', 
                    'text/plain':'mtviews_jj2.text.plain',
                    ('application/json', 'application/x-javascript', 'text/javascript', 'text/x-javascript', 'text/x-json'): to_json,
                    'atom': to_atom}, 
          extra_param='titilola')
    def complete_templates():
        return dict(it={'a': 'A', 'b': 'B'}, key2='2')

    self.assertInBody('<html>', '/complete_templates')
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/complete_templates')

    self.assertInBody('<html>', '/complete_templates', env={'HTTP_ACCEPT': 'text/html'})
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/complete_templates', env={'HTTP_ACCEPT': 'text/html'})

    self.assertInBody('<html>', '/complete_templates', env={'HTTP_ACCEPT': 'text/*'})
    self.assertHeader('Content-Type', 'text/html; charset=UTF-8', '/complete_templates', env={'HTTP_ACCEPT': 'text/*'})

    self.assertInBody('Text Plain', '/complete_templates', env={'HTTP_ACCEPT': 'text/plain;q=0.8, text/*;q=0.6'})
    self.assertHeader('Content-Type', 'text/plain; charset=UTF-8', '/complete_templates', env={'HTTP_ACCEPT': 'text/plain;q=0.8, text/*;q=0.6'})

    self.assertInBody('<xml>atom</xml>', '/complete_templates', env={'HTTP_ACCEPT': 'application/xml'})
    self.assertHeader('Content-Type', 'application/xml; charset=UTF-8', '/complete_templates', env={'HTTP_ACCEPT': 'application/xml'})

    self.assertInBody('json', '/complete_templates', env={'HTTP_ACCEPT': 'application/json'})
    self.assertHeader('Content-Type', 'application/json; charset=UTF-8', '/complete_templates', env={'HTTP_ACCEPT': 'application/json'})

    
def to_json(param, **kwargs):
  print ".to_json: param:{%s} kwargs:{%s}" % (param, kwargs)
  return 'json'

def to_atom(param, **kwargs):
  print ".to_atom: param:{%s} kwargs:{%s}" % (param, kwargs)
  return '<xml>atom</xml>'



#@bottle.route('/get_dict')
#@view(template='jinja2_simple', extra_param='titilola')
#def get_dict():
  #return dict(var='1', key2='2')


#@bottle.route('/get_list')
#@view(template='jinja2_inherit.tpl', extra_param='titilola')
#def get_list():
  #return ['item1', 'item2', 'item3']

#@bottle.route('/single_template_dict')
#@view(template='mtviews_jj2', formats=['text/html', 'text/plain', 'application/xml'], extra_param='titilola')
#def single_template_dict():
  #return dict(it={'a': 'A', 'b': 'B'}, key2='2')

#@bottle.route('/single_template_nondict')
#@view(template='mtviews_jj2', formats=['text/html', 'text/plain', 'application/xml'], extra_param='titilola')
#def single_template():
  #return set([1, 2, 3])

#@bottle.route('/single_template_genericmt')
#@view(template='mtviews_jj2', formats=['html'], extra_param='titilola')
#def single_template_genericmt():
  #return dict(it={'a': 'A', 'b': 'B'}, key2='2')

#@bottle.route('/complete_templates')
#@view(mappings={'text/html': 'mtviews_jj2.text.html', 
                #'text/plain':'mtviews_jj2.text.plain',
                #('application/json', 'application/x-javascript', 'text/javascript', 'text/x-javascript', 'text/x-json'): to_json,
                #'atom': to_atom}, extra_param='titilola')
#def complete_templates():
    #return dict(it={'a': 'A', 'b': 'B'}, key2='2')

if __name__ == '__main__':
  #bottle.run(host='localhost', port=8080, reloader=False)
  unittest.main()