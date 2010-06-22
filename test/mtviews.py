import functools
import re

from bottle import request, response, mako_template, jinja2_template, cheetah_template
from bottle import template as bottle_template
from bottlecork import all_best_matches


__all__ = ['generic_media_type', 'view', 'mako_view', 'jinja2_view', 'cheetah_view']

# TODO:
#
# - (done) for _default_template_func_caller it is impossible to say if 
#   template_func was called or not so we should not set media type


_GENERIC_MAPPERS = {
  'text': ('text/plain'),
  'html': ('text/html','application/xhtml+xml',  ),
  'json': ('application/json', 'text/json',),
  'atom': ('application/atom+xml', 'application/xml', 'text/xml',)
}

def generic_media_type(name, iana_media_types=[]):
  """ Allows registering a `generic` media type mapper.
  
  A generic media type mapper is a simple way to specify multiple
  common real media types. 
  
  Example: html -> text/html, application/xhtml+xml
  
  Parameters:
    - name: the name of the generic media type
    - iana_media_types: a list of real media types to which this generic
  type must be expanded
  """
  if iana_media_types:
    _GENERIC_MAPPERS[name] = tuple(iana_media_types)

    
def view(template_func=bottle_template, template=None, formats=None, mappings=None, **defaults):
  if (not template) and (not formats) and (not mappings):
    raise TypeError('view expects at least 1 of the parameters to be set')
  
  mappers = _create_mappers(template_func, template, formats, mappings)
  
  def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      result = func(*args, **kwargs)
      mt, handler = _get_mediatype(request, mappers)
      if handler:
        result = handler(result, **defaults)
        if _COMPLETE_MEDIA_TYPE.match(mt):
          response.content_type = "%s; charset=%s" % (mt, response.charset) if response.charset else mt
      return result
    return wrapper
  return decorator

_COMPLETE_MEDIA_TYPE = re.compile('[^\*]+/[^\*]+')

mako_view = functools.partial(view, mako_template)
jinja2_view = functools.partial(view, jinja2_template)
cheetah_view = functools.partial(view, cheetah_template)

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
  
  

