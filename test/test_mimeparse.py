import unittest

from bottlecork import best_match

class MimeparseTest(unittest.TestCase):
  def testSimpleQualityFactor(self):
    self.assertEquals('text/plain', best_match(['text/plain', 'text/html'], 'text/plain, text/html; q=0.8'))

  def testComplexQualityFactor(self):
    ACCEPT_HEADER = 'text/*;q=0.3, text/html;q=0.7, */*;q=0.5'
    self.assertEquals('text/html', best_match(['text/html', 'text/plain', 'text/json'], ACCEPT_HEADER))
    self.assertEquals('text/plain', best_match(['text/plain', 'text/json', 'application/json'], ACCEPT_HEADER))
    self.assertEquals('text/plain', best_match(['text/json', 'text/plain'], ACCEPT_HEADER))
    self.assertEquals('text/json', best_match(['text/json', 'application/json'], ACCEPT_HEADER))
    self.assertEquals('application/json', best_match(['application/json', 'application/html'], ACCEPT_HEADER))
    
  #def testOne(self):
    #for accept in ACCEPT_EXAMPLES:
      #print "%s <= */* -> %s" % (mimeparse.best_match(['*/*'], accept), accept)
      #print "%s <= text/html -> %s" % (mimeparse.best_match(['text/html'], accept), accept)
      #print "%s <= application/xml -> %s" % (mimeparse.best_match(['application/xml'], accept), accept)
      #print "%s <= application/octet-stream -> %s:" % (mimeparse.best_match(['application/octet-stream'], accept), accept)
      
    
ACCEPT_EXAMPLES = (
  'text/xml, application/xml, application/xhtml+xml, text/html;q=0.9, text/plain;q=0.8, image/png,*/*;q=0.5',
  'image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, application/x-shockwave-flash, */*',
  'text/html; q=1.0, text/*; q=0.8, image/gif; q=0.6, image/jpeg; q=0.6, image/*; q=0.5, */*; q=0.1',
  'text/html, text/plain, image/gif, image/jpeg, */*',
  'image/*, */*',
  'text/html, text/plain, image/gif, image/jpeg, */*; q=0.01',
  'audio/*; q=0.2, audio/basic',
  'text/plain; q=0.5, text/html, text/x-dvi; q=0.8, text/x-c',
  'text/*, text/html, text/html;level=1, */*',
  'text/*;q=0.3, text/html;q=0.7, text/html;level=1, text/html;level=2;q=0.4, */*;q=0.5',
)

if __name__ == '__main__':
  unittest.main()
                   