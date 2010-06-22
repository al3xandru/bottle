import functools
import re

import bottle

__all__ = ['route', 'MediaTypeFilter', 'view', 'mako_view', 'jinja2_view', 'cheetah_view']

_GENERIC_MAPPERS = {
  'text': ('text/plain'),
  'html': ('text/html','application/xhtml+xml',  ),
  'json': ('application/json', 'text/json',),
  'atom': ('application/atom+xml', 'application/xml', 'text/xml',)
}

def view(template_func=bottle.template, template=None, formats=None, mappings=None, **defaults):
  if (not template) and (not formats) and (not mappings):
    raise TypeError('view expects at least 1 of the parameters to be set')
  
  mappers = _create_mappers(template_func, template, formats, mappings)
  
  def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      result = func(*args, **kwargs)
      req = bottle.request
      res = bottle.response
      mt, handler = _get_mediatype(req, mappers)
      if handler:
        result = handler(result, **defaults)
        if _COMPLETE_MEDIA_TYPE.match(mt):
          res.content_type = "%s; charset=%s" % (mt, res.charset) if res.charset else mt
      return result
    return wrapper
  return decorator

_COMPLETE_MEDIA_TYPE = re.compile('[^\*]+/[^\*]+')

mako_view = functools.partial(view, bottle.mako_template)
jinja2_view = functools.partial(view, bottle.jinja2_template)
cheetah_view = functools.partial(view, bottle.cheetah_template)

def _create_mappers(template_func, template=None, formats=None, mappings=None):
  """ Creates a dict which maps given media types to special 
  handlers that will delegate the call to template functions.
  
  The rules for creating the dict:
    - if only `template` is specified, it is mapped to '*/*
    - if `template` and `formats` are given, then each format in the
    `formats` list is mapped to `template`
    - otherwise use the explicit `mappings`
  """
  mappers = {}
  if template:
    if formats:
      # we have a generic template for multiple media-types
      for fmt in formats:
        if fmt in _GENERIC_MAPPERS:
          for f in _GENERIC_MAPPERS[fmt]:
            mappers[f] = mappers.get(f) or _get_templatecall_delegator(template_func, template, f)
        else:
          mappers[fmt] = _get_templatecall_delegator(template_func, template, fmt)
    else:
      # we have a generic template for all media types
      # the template function is called only if the parameter type is dict
      mappers['*/*'] = lambda param, **defaults: _default_template_caller(template_func, template, param, allow_non_dict=False, **defaults)
  else:
    # we have explicit multiple mappings
    for k in mappings:
      if isinstance(k, tuple):
        # multi media-type mapper
        hdlr = mappings[k]
        for fmt in k:
          if fmt in _GENERIC_MAPPERS:
            for f in _GENERIC_MAPPERS[fmt]:
              mappers[f] = mappers.get(f) or _get_handler(template_func, hdlr, f)
          else:
            mappers[fmt] = _get_handler(template_func, hdlr, fmt)
      else:
        if k in _GENERIC_MAPPERS:
          for f in _GENERIC_MAPPERS[k]:
            mappers[f] = mappers.get(f) or _get_handler(template_func, mappings[k], f)
        else:
          mappers[k] = _get_handler(template_func, mappings[k], k)
  return mappers


def _default_template_caller(template_func, template_name, param, allow_non_dict=True, **defaults):
  if not allow_non_dict and not isinstance(param, dict):
    return param
  ctx = defaults.copy()
  if isinstance(param, dict):
    ctx.update(param)
  else:
    ctx['it'] = param
  return template_func(template_name, **ctx)

def _get_templatecall_delegator(template_func, template_name, format):
  """- calculates the template name based on the root `template_name` and the media type `format` 
    - return a function that delegates the real call to the designed template bottle.py method """
  template_name = "%s.%s" % (template_name, _MEDIATYPE_TEMPLATENAME_REGEXP.sub('.', format))
  return functools.partial(_default_template_caller, template_func, template_name)

_MEDIATYPE_TEMPLATENAME_REGEXP = re.compile('(/|-|\+)')

def _get_handler(template_func, hdlr, fmt):
  if callable(hdlr):
    return hdlr
  else:
    return lambda param, **defaults: _default_template_caller(template_func, hdlr, param, allow_non_dict=True, **defaults)
  

def _get_mediatype(req, mappers):
  accept_header = req.header.get('accept', '*/*')
  content_types = all_best_matches(mappers.keys(), accept_header)
  if not content_types:
    return (None, None)
  elif len(content_types) == 1:
    return (content_types[0], mappers[content_types[0]])
  # we have multiple matches so we just pick one in order of preferences
  for pref_mt in ('text/html', 'application/json', 'text/javascript', 'text/plain'):
    if pref_mt in content_types:
      return (pref_mt, mappers[pref_mt])
  return (content_types[0], mappers[content_types[0]])
  
  


#
# An improved @route decorator and a normal bottle filter
#
def route_decorator(app, path=None, method='GET', **kwargs):
  """ A decorator equivalent to `bootle.route` that also
  wrapps the return value into an `option` object so bottle.py
  filtering will always call the `cork` filter"""
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

""" An advanced route decoarator that works together with the
MediaTypeFilter to provide media-type negociation"""
route  = functools.partial(route_decorator, bottle.app())


class Option(object):
  """ A trivial wrapping object used to make bottle always 
  call `cork` filter"""
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
        
  def filter(self, opt, request=None, response=None):
    request = request or bottle.request
    response = response or bottle.response
    value = opt.value
    
    return mediatype_filter(value, request, response,
                            self.mediatype_filters,
                            self.types_mediatypes,
                            self._delegate_to_return,
                            self._chain_filter)

  def _delegate_to_return(self, value, request, response):
    return value
  
  def _chain_filter(self, value, request, response):
    return self.filter(option(value), request, response)
  

#
# A complicated solution that extends bottle.Bottle to allow overridding 
# the _cast method to handle media-type negotiation.
#
# The same solution can be achieved by using:
# bottlecork.view (for media type negotiation for defined views only)
# bottlecork.route and MediaTypeFilter (for media type negotiation for return types)
#
class BottleCork(bottle.Bottle):
  """ Extension of the Bottle instance that allows more advanced
  media-type negociation.
  
  Note: an alternative to this solution is to use the custom
  bottlecork.route annotation and the MediaTypeFilter with default bottle
  """
  def __init__(self, catchall=True, autojson=True, config=None):
    super(BottleCork, self).__init__(catchall, False, config)
    self.mediatype_filters = {}
    self.types_mediatypes = {}


  def add_filter(self, ftype, func, media_types=[]):
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
    media_types = media_types or ["*/*"]
    self.types_mediatypes[ftype] = self.types_mediatypes.get(ftype) or set()
    for mt in media_types:
      if self.mediatype_filters.has_key((ftype, mt)):
        print "WARNING: overriding filter %s for (%s, %s) with %s" % (self.mediatype_filters[(ftype, mt)].__name__, ftype.__name__, mt, func.__name__)
      self.mediatype_filters[(ftype, mt)] = func
      self.types_mediatypes[ftype].add(mt)

  def _delegate_to_super(self, out, request, response):
    return super(BottleCork, self)._cast(out, request, response)
  
  def _cast(self, out, request, response):
    return mediatype_filter(out, request, response, 
                            self.mediatype_filters,
                            self.types_mediatypes, 
                            self._delegate_to_super, self._cast)
    

#bottle.app = bottle.default_app = bottle.AppStack()
#bottle.app.push(BottleCork())


#
# implementation of media-type negotiation, used by both
# BottleCork and MediaTypeFilter
#
def mediatype_filter(value, request, response, mediatype_mappings, pertype_mappings, delegate_func, chain_func):
  if not value:
    response.headers['Content-Length'] = 0
    response.status = 204 if not response.status and request.method != 'HEAD' else response.status
    return []
  
  if isinstance(value, (bottle.HTTPError, bottle.HTTPResponse)):
    return delegate_func(value, request, response)
  
  request_accept_header = request.header.get('accept', '*/*')
  accepted_mediatypes = [parse_media_range(r) for r in request_accept_header.split(",")]
  
  # Just try to negociate media-type
  if hasattr(value, 'read'):
    if not response.content_type:
      content_types = best_matches(['application/octet-stream'], accepted_mediatypes)
      if len(content_types) == 1:
        response.content_type = 'application/octet-stream'
    return delegate_func(value, request, response)

  type_mtypes = {}
  for ftype in pertype_mappings:
    if isinstance(value, ftype):
      for mt in pertype_mappings[ftype]:
        type_mtypes[mt] = type_mtypes.get(mt, [])
        type_mtypes[mt].append(ftype)
  if type_mtypes:
    content_types = best_matches(type_mtypes.keys(), accepted_mediatypes)
    if content_types:
      # we have multiple media types; lets now determine the close in terms of object hierarchy
      types = set()
      types_matched_media = {}
      for ct in content_types:
        tps = type_mtypes[ct]
        types.update(tps)
        for t in tps:
          types_matched_media[t] = types_matched_media.get(t) or []
          types_matched_media[t].append(ct)
      sorted_types = sorted(types, cmp=lambda o1, o2: len(o2.__mro__) - len(o1.__mro__))
      mtype = sorted_types[0]
      ctypes = types_matched_media[mtype]
      if len(ctypes) > 1:
        print "WARNING: cannot determine exact match for value of type %s and Accept: %s" % (value.__class__.__name__, request_accept_header)
      content_type = ctypes[0]

      return chain_func(mediatype_mappings[(mtype, content_type)](value), request, response)

  # only string-like
  supported_mediatypes = ['application/octet-stream']
  if isinstance(value, unicode):
    value = value.encode(response.charset)
    supported_mediatypes.append("text/plain; charset=%s" % response.charset)
    
  if isinstance(value, bottle.StringType):
    if response.charset:
      supported_mediatypes.append("text/plain; charset=%s" % response.charset)
    if not response.content_type:
      content_types = best_matches(supported_mediatypes, accepted_mediatypes)

      if len(content_types):
        response.content_type = content_types[0]
      else:
        response.content_type = "text/plain; charset=%s" % response.charset if response.charset else 'text/plain'
    response.headers['Content-Length'] = str(len(value))
    return [value]
  
  return chain_func(bottle.HTTPError(code=406, 
                                     output="The requested URI '%s' exists, but not in a format preferred by the client." % request.path),                      
                    request, response)

def best_matches(supported, parsed_header):
  weighted_matches = [(fitness_and_quality_parsed(mime_type, parsed_header), mime_type)\
                      for mime_type in supported]
  weighted_matches.sort(reverse=True)
  result = weighted_matches[0][0][1] and weighted_matches[0][1] or ''
  result_list = []
  if result:
    result_list.append(result)
    # check if there aren't more matches with the same score
    score = weighted_matches[0][0][0]
    q = weighted_matches[0][0][1]
    for i in range(1, len(weighted_matches)):
      if score == weighted_matches[i][0][0] and q == weighted_matches[i][0][1]:
        result_list.append(weighted_matches[i][1])
  return result_list
  
def all_best_matches(supported, header):
  parsed_header = [parse_media_range(r) for r in header.split(",")]
  weighted_matches = [(fitness_and_quality_parsed(mime_type, parsed_header), mime_type)\
                      for mime_type in supported]
  weighted_matches.sort(reverse=True)
  result = weighted_matches[0][0][1] and weighted_matches[0][1] or ''
  result_list = []
  if result:
    result_list.append(result)
    # check if there aren't more matches with the same score
    score = weighted_matches[0][0][0]
    for i in range(1, len(weighted_matches)):
      if score == weighted_matches[i][0][0]:
        result_list.append(weighted_matches[i][1])
  return result_list

"""MIME-Type Parser:

Project page: http://code.google.com/p/mimeparse/
License: MIT License http://www.opensource.org/licenses/mit-license.php
"""

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

