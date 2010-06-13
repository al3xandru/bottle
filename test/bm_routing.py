import re

from benchmark import Benchmark

def all_match(regexp, cycles):
  matches = 0
  for i in range(cycles):
    for r in ROUTES:
      if regexp.match(r):
        matches += 1
  print "all_match: %d" % matches

def seq_match(regexp_list, cycles):
  matches = 0
  for i in range(cycles):
    for r in ROUTES:
      for reg in regexp_list:
        if reg.match(r):
          matches += 1
          break
  print "seq_match: %d" % matches
  
def mixed_seq_match(allregexp, regexp_list, cycles):
  matches = 0
  for i in range(cycles):
    for r in ROUTES:
      if allregexp.match(r):
        for reg in regexp_list:
          if reg.match(r):
            matches += 1
            break
  print "seq_match: %d" % matches
  
def build_all_pattern(limit):
  return re.compile("|".join(ROUTES_RULES[:limit]))
  
def build_seq_pattern(limit):
  regexps = []
  for r in ROUTES_RULES[:limit]:
    regexps.append(re.compile(r))
  return regexps

ROUTES_RULES = ('/hello/[^/]+', 
  '/get_object/[0-9]+',
  '/get_o/(?P<id>[0-9]+)',
  '/test/validate/[^/]+/[^/]+/[^/]+',
  '/images/.*\.png',
  '/restricted',
  '/hello2/[^/]+', 
  '/get_object2/[0-9]+',
  '/get_o2/(?P<id2>[0-9]+)',
  '/test/validate2/[^/]+/[^/]+/[^/]+',
  '/images2/.*\.png',
  '/restricted3',
  '/hello3/[^/]+', 
  '/get_object3/[0-9]+',
  '/get_o3/(?P<id3>[0-9]+)',
  '/test3/validate/[^/]+/[^/]+/[^/]+',
  '/images3/.*\.png',
  '/restricted3',
  '/hello4/[^/]+', 
  '/get_object4/[0-9]+',
  '/get_o4/(?P<id4>[0-9]+)',
  '/test/validate4/[^/]+/[^/]+/[^/]+',
  '/images4/.*\.png',
  '/restricted4',
  '/hello5/[^/]+', 
  '/get_object5/[0-9]+',
  '/get_o5/(?P<id5>[0-9]+)',
  '/test/validate5/[^/]+/[^/]+/[^/]+',
  '/images5/.*\.png',
  '/restricted5'
)

ROUTES = ('/',
          '/hello/foo/bar',
          '/hello/foo',
          '/get_object/foo',
          '/get_object/123',
          '/get_o/foo',
          '/get_o/123456',
          '/test/validate/a'
          '/test/validate/a/b',
          '/test/validate/a/b/c/d',
          '/test/validate/a/b/c',
          '/images/foo.pnf',
          '/images/foo.png',
          '/restrictedfoo',
          'restricted'
)

if __name__ == '__main__':
  counter = 1000
  Benchmark.bm(('all (6)', lambda: all_match(build_all_pattern(6), counter)),
               ('seq (6)', lambda: seq_match(build_seq_pattern(6), counter)),
               ('mix (6)', lambda: mixed_seq_match(build_all_pattern(6), build_seq_pattern(6), counter)),
               ('all (12)', lambda: all_match(build_all_pattern(12), counter)),
               ('seq (12)', lambda: seq_match(build_seq_pattern(12), counter)),
               ('mix (12)', lambda: mixed_seq_match(build_all_pattern(12), build_seq_pattern(12), counter)),
               ('all (18)', lambda: all_match(build_all_pattern(18), counter)),
               ('seq (18)', lambda: seq_match(build_seq_pattern(18), counter)),
               ('mix (18)', lambda: mixed_seq_match(build_all_pattern(18), build_seq_pattern(18), counter)),
               ('all (24)', lambda: all_match(build_all_pattern(24), counter)),
               ('seq (24)', lambda: seq_match(build_seq_pattern(24), counter)),
               ('mix (24)', lambda: mixed_seq_match(build_all_pattern(24), build_seq_pattern(24), counter)),
               ('all (30)', lambda: all_match(build_all_pattern(30), counter)),
               ('seq (30)', lambda: seq_match(build_seq_pattern(30), counter)),
               ('mix (30)', lambda: mixed_seq_match(build_all_pattern(30), build_seq_pattern(30), counter)),
               rehearse=False               )
  

          

