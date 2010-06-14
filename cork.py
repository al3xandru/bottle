import functools

import bottle


def option_route(app, path=None, method='GET', **kwargs):
  def _wrapper(function):
    @functools.wraps(function)
    def _result_wrapper(*a, **ka):
      try:
        result = function(*a, **ka)
      except Exception, e:
        result = e
      return option(result)
    return app.route(path, method, **kwargs)(_result_wrapper)
  return _wrapper
  
route  = functools.partial(option_route, bottle.app())

class Option(object):
  __slots__ = ['value']
  
  def __init__(self, v=None):
    self.value = v
    
option = Option


class MediaTypeFilter(object):
  def __init__(self):
    self.mediatype_filters = {}
    self.types_mediatypes = {}
    
  def add_filter(self, func, ftype, media_types=[]):
    ''' Register a new output filter for the given type and the media types. 
    Whenever bottle hits a handler output matching `ftype` and content negotiation picks
    a media type, `func` is applyed to it. 

    ftype: return type to be matched
    media_types: iterable of media types
    func: function to be called
    '''
    if not isinstance(ftype, type):
      raise TypeError("Expected type object, got %s" % type(ftype))
    if not media_types:
      print "WARNING: filters should declare their specific media types"
    media_types = media_types or ['*/*']
    self.types_mediatypes[ftype] = self.types_mediatypes.get(ftype) or set()
    for mt in media_types:
      if self.mediatype_filters.has_key((ftype, mt)):
        print "WARNING: overriding filter %s for (%s, %s) with %s" % (self.mediatype_filters[(ftype, mt)].__name__, ftype.__name__, mt, func.__name__)
      self.mediatype_filters[(ftype, mt)] = func
      self.types_mediatypes[ftype].add(mt)
      
  def filter(self, opt):
    app = bottle.app()
    value = opt.value
    if not value:
      bottle.response.headers['Content-Length'] = 0
      bottle.response.status = 204 if not bottle.response.status and bottle.request.method != 'HEAD' else bottle.response.status
      return []
    
    if isinstance(value, bottle.HTTPError):
      value.apply(bottle.response)
      err_handler = app.error_handler.get(value.status)
      if not err_handler:
        err_handler = repr
        bottle.response.content_type = "text/html" if not bottle.response.charset else "text/html; charset=%s" % bottle.response.charset
      return value
      
    if isinstance(value, (bottle.HTTPError, bottle.HTTPResponse)):
      return value
    
    accepted_mediatypes = [parse_media_range(r) for r in bottle.request.header.get('accept', '*/*').split(",")]
    
    # Should return after setting the content type
    if hasattr(value, 'read'):
      if not bottle.response.content_type:
        content_type = self._best_media_match(['application/octet-stream'], accepted_mediatypes)
        if content_type and content_type != '*/*':
          bottle.response.content_type = content_type 
      return value
  
      
    type_mtypes = {}
    for ftype in self.types_mediatypes:
      if isinstance(value, ftype):
        for mt in self.types_mediatypes[ftype]:
          type_mtypes[mt] = type_mtypes.get(mt, [])
          type_mtypes[mt].append(ftype)
    if type_mtypes:
      content_type = self._best_media_match(type_mtypes.keys(), accepted_mediatypes)
      if content_type:
        types = type_mtypes[content_type]
        types = sorted(types, cmp=lambda o1, o2: len(o2.__mro__) - len(o1.__mro__))
        mtype = types[0]
  
        return self.filter(option(self.mediatype_filters[(mtype, content_type)](value)))
      
    # only string-like
    supported = ['application/octet-stream']
    if isinstance(value, unicode):
      value = value.encode(bottle.response.charset)
      supported.append("text/plain; charset=%s" % bottle.response.charset)
      
    if isinstance(value, bottle.StringType):
      if bottle.response.charset:
        supported.append("text/plain; charset=%s" % bottle.response.charset)
      if not bottle.response.content_type:
        bottle.response.content_type = self._best_media_match(supported, accepted_mediatypes) or \
                     ("text/plain; charset=%s" % bottle.response.charset if bottle.response.charset else 'text/plain')
      bottle.response.headers['Content-Length'] = str(len(value))
      return [value]
    
    return self.filter(option(bottle.HTTPError(code=406, 
                                               output="The requested URI '%s' exists, but not in a format preferred by the client." % bottle.request.path)
                              ))

  
  def _best_media_match(self, supported, parsed_header):
    """Takes a list of supported mime-types and finds the best
    match for all the media-ranges listed in header. `parsed_header`
    is the already parsed HTTP Accept header.
    The value of 'supported' is a list of mime-types.

    """
    weighted_matches = [(fitness_and_quality_parsed(mime_type, parsed_header), mime_type)\
                        for mime_type in supported]
    weighted_matches.sort()
    return weighted_matches[-1][0][1] and weighted_matches[-1][1] or ''


"""MIME-Type Parser

This module provides basic functions for handling mime-types. It can handle
matching mime-types against a list of media-ranges. See section 14.1 of 
the HTTP specification [RFC 2616] for a complete explanation.

   http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.1

Contents:
    - parse_mime_type():   Parses a mime-type into its component parts.
    - parse_media_range(): Media-ranges are mime-types with wild-cards and a 'q' quality parameter.
    - quality():           Determines the quality ('q') of a mime-type when compared against a list of media-ranges.
    - quality_parsed():    Just like quality() except the second parameter must be pre-parsed.
    - best_match():        Choose the mime-type with the highest quality ('q') from a list of candidates. 
"""

__version__ = "0.1.2"
__author__ = 'Joe Gregorio'
__email__ = "joe@bitworking.org"
__credits__ = ""

def parse_mime_type(mime_type):
  """Carves up a mime-type and returns a tuple of the
     (type, subtype, params) where 'params' is a dictionary
     of all the parameters for the media range.
     For example, the media range 'application/xhtml;q=0.5' would
     get parsed into:

     ('application', 'xhtml', {'q', '0.5'})
     """
  parts = mime_type.split(";")
  params = dict([tuple([s.strip() for s in param.split("=")])\
                 for param in parts[1:] ])
  full_type = parts[0].strip()
  # Java URLConnection class sends an Accept header that includes a single "*"
  # Turn it into a legal wildcard.
  if full_type == '*': full_type = '*/*'
  (type, subtype) = full_type.split("/")
  return (type.strip(), subtype.strip(), params)

def parse_media_range(range):
  """Carves up a media range and returns a tuple of the
     (type, subtype, params) where 'params' is a dictionary
     of all the parameters for the media range.
     For example, the media range 'application/*;q=0.5' would
     get parsed into:

     ('application', '*', {'q', '0.5'})

     In addition this function also guarantees that there 
     is a value for 'q' in the params dictionary, filling it
     in with a proper default if necessary.
     """
  (type, subtype, params) = parse_mime_type(range)
  if not params.has_key('q') or not params['q'] or \
     not float(params['q']) or float(params['q']) > 1\
     or float(params['q']) < 0:
    params['q'] = '1'
  return (type, subtype, params)

def fitness_and_quality_parsed(mime_type, parsed_ranges):
  """Find the best match for a given mime-type against 
     a list of media_ranges that have already been 
     parsed by parse_media_range(). Returns a tuple of
     the fitness value and the value of the 'q' quality
     parameter of the best match, or (-1, 0) if no match
     was found. Just as for quality_parsed(), 'parsed_ranges'
     must be a list of parsed media ranges. """
  best_fitness = -1 
  best_fit_q = 0
  (target_type, target_subtype, target_params) =\
   parse_media_range(mime_type)
  for (type, subtype, params) in parsed_ranges:
    if (type == target_type or type == '*' or target_type == '*') and \
       (subtype == target_subtype or subtype == '*' or target_subtype == '*'):
      param_matches = reduce(lambda x, y: x+y, [1 for (key, value) in \
                                                target_params.iteritems() if key != 'q' and \
                                                params.has_key(key) and value == params[key]], 0)
      fitness = (type == target_type) and 100 or 0
      fitness += (subtype == target_subtype) and 10 or 0
      fitness += param_matches
      if fitness > best_fitness:
        best_fitness = fitness
        best_fit_q = params['q']

  return best_fitness, float(best_fit_q)

def quality_parsed(mime_type, parsed_ranges):
  """Find the best match for a given mime-type against
  a list of media_ranges that have already been
  parsed by parse_media_range(). Returns the
  'q' quality parameter of the best match, 0 if no
  match was found. This function bahaves the same as quality()
  except that 'parsed_ranges' must be a list of
  parsed media ranges. """
  return fitness_and_quality_parsed(mime_type, parsed_ranges)[1]

def quality(mime_type, ranges):
  """Returns the quality 'q' of a mime-type when compared
  against the media-ranges in ranges. For example:

  >>> quality('text/html','text/*;q=0.3, text/html;q=0.7, text/html;level=1, text/html;level=2;q=0.4, */*;q=0.5')
  0.7

  """ 
  parsed_ranges = [parse_media_range(r) for r in ranges.split(",")]
  return quality_parsed(mime_type, parsed_ranges)

def best_match(supported, header):
  """Takes a list of supported mime-types and finds the best
  match for all the media-ranges listed in header. The value of
  header must be a string that conforms to the format of the 
  HTTP Accept: header. The value of 'supported' is a list of
  mime-types.

  >>> best_match(['application/xbel+xml', 'text/xml'], 'text/*;q=0.5,*/*; q=0.1')
  'text/xml'
  """
  parsed_header = [parse_media_range(r) for r in header.split(",")]
  weighted_matches = [(fitness_and_quality_parsed(mime_type, parsed_header), mime_type)\
                      for mime_type in supported]
  weighted_matches.sort()
  return weighted_matches[-1][0][1] and weighted_matches[-1][1] or ''

