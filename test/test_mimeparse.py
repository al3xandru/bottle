import unittest

from bottlecork import best_match, all_best_matches

class MimeparseTest(unittest.TestCase):
  def testSimpleQualityFactor(self):
    self.assertEquals('text/plain', best_match(['text/plain', 'text/html'], 'text/plain, text/html; q=0.8'))

  def testComplexQualityFactor(self):
    ACCEPT_HEADER = 'text/*;q=0.3, text/html;q=0.7, */*;q=0.5'
    self.assertEquals('text/html', best_match(['text/html', 'text/plain', 'text/json'], ACCEPT_HEADER))
    self.assertEquals('text/plain', best_match(['text/plain', 'text/json', 'application/json'], ACCEPT_HEADER))
    # check testMatchAll for explanation
    self.assertEquals('text/plain', best_match(['text/json', 'text/plain'], ACCEPT_HEADER))
    self.assertEquals('text/x-json', best_match(['text/x-json', 'text/plain'], ACCEPT_HEADER))
    # using the improved best_matches
    self.assertEquals(['text/plain', 'text/json'], all_best_matches(['text/json', 'text/plain'], ACCEPT_HEADER))
    self.assertEquals(['text/x-json', 'text/plain'], all_best_matches(['text/x-json', 'text/plain'], ACCEPT_HEADER))
    
    self.assertEquals('text/json', best_match(['text/json', 'application/json'], ACCEPT_HEADER))
    self.assertEquals('application/json', best_match(['application/json', 'application/html'], ACCEPT_HEADER))

  def testMatchAll(self):
    """ Validates an assumption that for a generic Accept: */* or m/* the match is just the last lexicographically sorted
    supported format"""
    SUPPORTED = ['application/atom+xml', 'application/json', 'application/x-javascript', 
                 'image/gif', 'image/jpeg', 'image/png',
                 'text/html', 'text/javascript',  'text/plain', 
                 'text/x-javascript', 'text/x-json']
    for i in range(len(SUPPORTED)):
      self.assertEquals(SUPPORTED[i], best_match(SUPPORTED[:i+1], '*/*'), "running %d" % i)
      
    TEXT_SUPPORTED = SUPPORTED[6:]
    for i in range(len(TEXT_SUPPORTED)):
      self.assertEquals(TEXT_SUPPORTED[i], best_match(TEXT_SUPPORTED[:i+1], 'text/*'), "running %d" % i)
      
      
  def testStarMatches(self):
    self.assertEquals(set(['text/plain', 'text/html', 'application/xml']), set(all_best_matches(['text/plain', 'text/html', 'application/xml'], '*/*')))
    self.assertEquals(set(['text/plain', 'text/html']), set(all_best_matches(['text/plain', 'text/html', 'application/xml'], 'text/*')))
    self.assertEquals(set(['text/plain', 'text/html']), set(all_best_matches(['text/plain', 'text/html', 'application/xml'], 'text/*; q=0.8, */*; q=0.1')))
    
  def testBestMatches(self):
    """ Validates an assumption that for a generic Accept: */* or m/* the match is just the last lexicographically sorted
    supported format"""
    SUPPORTED = ['application/atom+xml', 'application/json', 'application/x-javascript', 
                 'image/gif', 'image/jpeg', 'image/png',
                 'text/html', 'text/javascript',  'text/plain', 
                 'text/x-javascript', 'text/x-json']
    
    for i in range(len(SUPPORTED)):
      self.assertEquals(set(SUPPORTED[:i+1]), set(all_best_matches(SUPPORTED[:i+1], '*/*')), "running %d" % i)
      
    TEXT_SUPPORTED = SUPPORTED[6:]
    for i in range(len(TEXT_SUPPORTED)):
      self.assertEquals(set(TEXT_SUPPORTED[:i+1]), set(all_best_matches(TEXT_SUPPORTED[:i+1], 'text/*')), "running %d" % i)
      
    
  def testSamples(self):
    SUPPORTED = ['*/*', 'text/html', 'application/xml', 'application/octet-stream']
    for accept in ACCEPT_EXAMPLES:
      expected_matches = ACCEPT_EXAMPLES[accept]
      for idx in range(len(SUPPORTED)):
        #print "Match: %s <= Supported: %s -> Accept: %s" % (best_match([SUPPORTED[idx]], accept), SUPPORTED[idx], accept)
        self.assertEquals(expected_matches[idx], best_match([SUPPORTED[idx]], accept), "supported: %s accept: %s" % (SUPPORTED[idx], accept))

  def failUnlessEqual(self, first, second, msg=None):
    """Fail if the two objects are unequal as determined by the '=='
       operator.
    """
    msg = msg or ""
    if not first == second:
      raise self.failureException, \
            ("%r != %r (%s)" % (first, second, msg))


  assertEqual = assertEquals = failUnlessEqual


ACCEPT_EXAMPLES = {
  'text/xml, application/xml, application/xhtml+xml, text/html;q=0.9, text/plain;q=0.8, image/png, */*;q=0.5': ('*/*', 'text/html', 'application/xml', 'application/octet-stream'),
  'image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, application/x-shockwave-flash, */*': ('*/*', 'text/html', 'application/xml', 'application/octet-stream'),
  'text/html; q=1.0, text/*; q=0.8, image/gif; q=0.6, image/jpeg; q=0.6, image/*; q=0.5, */*; q=0.1': ('*/*', 'text/html', 'application/xml', 'application/octet-stream'),
  'text/html, text/plain, image/gif, image/jpeg, */*': ('*/*', 'text/html', 'application/xml', 'application/octet-stream'),
  'image/*, */*': ('*/*', 'text/html', 'application/xml', 'application/octet-stream'),
  'text/html, text/plain, image/gif, image/jpeg, */*; q=0.01': ('*/*', 'text/html', 'application/xml', 'application/octet-stream'),
  'audio/*; q=0.2, audio/basic': ('*/*', '', '', ''),
  'text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c': ('*/*', 'text/html', '', ''),
  'text/*, text/html, text/html;level=1, */*': ('*/*', 'text/html', 'application/xml', 'application/octet-stream'),
  'text/*;q=0.3, text/html;q=0.7, text/html;level=1, text/html;level=2;q=0.4, */*;q=0.5': ('*/*', 'text/html', 'application/xml', 'application/octet-stream'),
}

if __name__ == '__main__':
  unittest.main()
