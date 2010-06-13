import unittest

class ParseAcceptHeaderTest(unittest.TestCase):
    def testParse(self):
        actual = parse_accept_header("text/html; q=1.0, text/*; q=0.8, image/gif; q=0.6, image/jpeg; q=0.6, image/*; q=0.5, */*; q=0.1")
        print actual

# Character classes from RFC 2616 section 2.2
SEPARATORS = '()<>@,;:\\"/[]?={} \t'
LWS = ' \t\n\r'  # linear white space

try:
    # Turn character classes into set types (for Python 2.4 or greater)
    SEPARATORS = frozenset([c for c in SEPARATORS])
    LWS = frozenset([c for c in LWS])
    del c
except NameError:
    # Python 2.3 or earlier, leave as simple strings
    pass

def parse_accept_header( header_value ):
    """Parses the Accept: header.

    The value of the header as a string should be passed in; without
    the header name itself.
    
    This will parse the value of any of the HTTP headers "Accept",
    "Accept-Charset", "Accept-Encoding", or "Accept-Language".  These
    headers are similarly formatted, in that they are a list of items
    with associated quality factors.  The quality factor, or qvalue,
    is a number in the range [0.0..1.0] which indicates the relative
    preference of each item.

    This function returns a list of those items, sorted by preference
    (from most-prefered to least-prefered).  Each item in the returned
    list is actually a tuple consisting of:

       ( item_name, item_parms, qvalue, accept_parms )

    As an example, the following string,
        text/plain; charset="utf-8"; q=.5; columns=80
    would be parsed into this resulting tuple,
        ( 'text/plain', [('charset','utf-8')], 0.5, [('columns','80')] )

    The value of the returned item_name depends upon which header is
    being parsed, but for example it may be a MIME content or media
    type (without parameters), a language tag, or so on.  Any optional
    parameters (delimited by semicolons) occuring before the "q="
    attribute will be in the item_parms list as (attribute,value)
    tuples in the same order as they appear in the header.  Any quoted
    values will have been unquoted and unescaped.

    The qvalue is a floating point number in the inclusive range 0.0
    to 1.0, and roughly indicates the preference for this item.
    Values outside this range will be capped to the closest extreme.

         (!) Note that a qvalue of 0 indicates that the item is
         explicitly NOT acceptable to the user agent, and should be
         handled differently by the caller.

    The accept_parms, like the item_parms, is a list of any attributes
    occuring after the "q=" attribute, and will be in the list as
    (attribute,value) tuples in the same order as they occur.
    Usually accept_parms will be an empty list, as the HTTP spec
    allows these extra parameters in the syntax but does not
    currently define any possible values.

    All empty items will be removed from the list.  However, duplicate
    or conflicting values are not detected or handled in any way by
    this function.
    """
    def parse_mt_only(s, start):
        mt, k = parse_media_type(s, start, with_parameters=False)
        ct = content_type()
        ct.major = mt[0]
        ct.minor = mt[1]
        return ct, k

    alist, k = parse_qvalue_accept_list( header_value, item_parser=parse_mt_only )
    if k < len(header_value):
        raise ParseError('Accept header is invalid',header_value,k)

    ctlist = []
    for ct, ctparms, q, acptparms  in alist:
        if ctparms:
            ct.set_parameters( dict(ctparms) )
        ctlist.append( (ct, q, acptparms) )
    return ctlist

def parse_media_type(media_type, start=0, with_parameters=True):
    """Parses a media type (MIME type) designator into it's parts.

    Given a media type string, returns a nested tuple of it's parts.

        ((major,minor,parmlist), chars_consumed)

    where parmlist is a list of tuples of (parm_name, parm_value).
    Quoted-values are appropriately unquoted and unescaped.
    
    If 'with_parameters' is False, then parsing will stop immediately
    after the minor media type; and will not proceed to parse any
    of the semicolon-separated paramters.

    Examples:
        image/png -> (('image','png',[]), 9)
        text/plain; charset="utf-16be"
                  -> (('text','plain',[('charset,'utf-16be')]), 30)

    """

    s = media_type
    pos = start
    ctmaj, k = parse_token(s, pos)
    if k == 0:
        raise ParseError('Media type must be of the form "major/minor".', s, pos)
    pos += k
    if pos >= len(s) or s[pos] != '/':
        raise ParseError('Media type must be of the form "major/minor".', s, pos)
    pos += 1
    ctmin, k = parse_token(s, pos)
    if k == 0:
        raise ParseError('Media type must be of the form "major/minor".', s, pos)
    pos += k
    if with_parameters:
        parmlist, k = parse_parameter_list(s, pos)
        pos += k
    else:
        parmlist = []
    return ((ctmaj, ctmin, parmlist), pos - start)


def parse_token(s, start=0):
    """Parses a token.

    A token is a string defined by RFC 2616 section 2.2 as:
       token = 1*<any CHAR except CTLs or separators>

    Returns a tuple (token, chars_consumed), or ('',0) if no token
    starts at the given string position.  On a syntax error, a
    ParseError exception will be raised.

    """
    return parse_token_or_quoted_string(s, start, allow_quoted=False, allow_token=True)

def parse_token_or_quoted_string(s, start=0, allow_quoted=True, allow_token=True):
    """Parses a token or a quoted-string.

    's' is the string to parse, while start is the position within the
    string where parsing should begin.  It will returns a tuple
    (token, chars_consumed), with all \-escapes and quotation already
    processed.

    Syntax is according to BNF rules in RFC 2161 section 2.2,
    specifically the 'token' and 'quoted-string' declarations.
    Syntax errors in the input string will result in ParseError
    being raised.

    If allow_quoted is False, then only tokens will be parsed instead
    of either a token or quoted-string.

    If allow_token is False, then only quoted-strings will be parsed
    instead of either a token or quoted-string.
    """
    if not allow_quoted and not allow_token:
        raise ValueError('Parsing can not continue with options provided')

    if start >= len(s):
        raise ParseError('Starting position is beyond the end of the string',s,start)
    has_quote = (s[start] == '"')
    if has_quote and not allow_quoted:
        raise ParseError('A quoted string was not expected', s, start)
    if not has_quote and not allow_token:
        raise ParseError('Expected a quotation mark', s, start)

    s2 = ''
    pos = start
    if has_quote:
        pos += 1
    while pos < len(s):
        c = s[pos]
        if c == '\\' and has_quote:
            # Note this is NOT C-style escaping; the character after the \ is
            # taken literally.
            pos += 1
            if pos == len(s):
                raise ParseError("End of string while expecting a character after '\\'",s,pos)
            s2 += s[pos]
            pos += 1
        elif c == '"' and has_quote:
            break
        elif not has_quote and (c in SEPARATORS or ord(c)<32 or ord(c)>127):
            break
        else:
            s2 += c
            pos += 1
    if has_quote:
        # Make sure we have a closing quote mark
        if pos >= len(s) or s[pos] != '"':
            raise ParseError('Quoted string is missing closing quote mark',s,pos)
        else:
            pos += 1
    return s2, (pos - start)


def parse_qvalue_accept_list( s, start=0, item_parser=parse_token ):
    """Parses any of the Accept-* style headers with quality factors.

    This is a low-level function.  It returns a list of tuples, each like:
       (item, item_parms, qvalue, accept_parms)

    You can pass in a function which parses each of the item strings, or
    accept the default where the items must be simple tokens.  Note that
    your parser should not consume any paramters (past the special "q"
    paramter anyway).

    The item_parms and accept_parms are each lists of (name,value) tuples.

    The qvalue is the quality factor, a number from 0 to 1 inclusive.

    """
    itemlist = []
    pos = start
    if pos >= len(s):
        raise ParseError('Starting position is beyond the end of the string',s,pos)
    item = None
    while pos < len(s):
        item, k = item_parser(s, pos)
        pos += k
        while pos < len(s) and s[pos] in LWS:
            pos += 1
        if pos >= len(s) or s[pos] in ',;':
            itemparms, qvalue, acptparms = [], None, []
            if pos < len(s) and s[pos] == ';':
                pos += 1
                while pos < len(s) and s[pos] in LWS:
                    pos += 1
                parmlist, k = parse_parameter_list(s, pos)
                for p, v in parmlist:
                    if p == 'q' and qvalue is None:
                        try:
                            qvalue = float(v)
                        except ValueError:
                            raise ParseError('qvalue must be a floating point number',s,pos)
                        if qvalue < 0 or qvalue > 1:
                            raise ParseError('qvalue must be between 0 and 1, inclusive',s,pos)
                    elif qvalue is None:
                        itemparms.append( (p,v) )
                    else:
                        acptparms.append( (p,v) )
                pos += k
            if item:
                # Add the item to the list
                if qvalue is None:
                    qvalue = 1
                itemlist.append( (item, itemparms, qvalue, acptparms) )
                item = None
            # skip commas
            while pos < len(s) and s[pos] == ',':
                pos += 1
                while pos < len(s) and s[pos] in LWS:
                    pos += 1
        else:
            break
    return itemlist, pos - start

def parse_parameter_list(s, start=0):
    """Parses a semicolon-separated 'parameter=value' list.

    Returns a tuple (parmlist, chars_consumed), where parmlist
    is a list of tuples (parm_name, parm_value).

    The parameter values will be unquoted and unescaped as needed.

    Empty parameters (as in ";;") are skipped, as is insignificant
    white space.  The list returned is kept in the same order as the
    parameters appear in the string.

    """
    pos = start
    parmlist = []
    while pos < len(s):
        while pos < len(s) and s[pos] in LWS:
            pos += 1 # skip whitespace
        if pos < len(s) and s[pos] == ';':
            pos += 1
            while pos < len(s) and s[pos] in LWS:
                pos += 1 # skip whitespace
        if pos >= len(s):
            break
        parmname, k = parse_token(s, pos)
        if parmname:
            pos += k
            while pos < len(s) and s[pos] in LWS:
                pos += 1 # skip whitespace
            if not (pos < len(s) and s[pos] == '='):
                raise ParseError('Expected an "=" after parameter name', s, pos)
            pos += 1
            while pos < len(s) and s[pos] in LWS:
                pos += 1 # skip whitespace
            parmval, k = parse_token_or_quoted_string( s, pos )
            pos += k
            parmlist.append( (parmname, parmval) )
        else:
            break
    return parmlist, pos - start

def is_token(s):
    """Determines if the string is a valid token."""
    for c in s:
        if ord(c) < 32 or ord(c) > 128 or c in SEPARATORS:
            return False
    return True

class content_type(object):
    """This class represents a media type (aka a MIME content type), including parameters.

    You initialize these by passing in a content-type declaration
    string, such as "text/plain; charset=ascii", to the constructor or
    to the set() method.  If you provide no string value, the object
    returned will represent the wildcard */* content type.

    Normally you will get the value back by using str(), or optionally
    you can access the components via the 'major', 'minor', 'media_type',
    or 'parmdict' members.

    """
    def __init__(self, content_type_string=None, with_parameters=True):
        """Create a new content_type object.

        See the set() method for a description of the arguments.
        """
        if content_type_string:
            self.set( content_type_string, with_parameters=with_parameters )
        else:
            self.set( '*/*' )

    def set_parameters(self, parameter_list_or_dict):
        """Sets the optional paramters based upon the parameter list.

        The paramter list should be a semicolon-separated name=value string.
        Any paramters which already exist on this object will be deleted,
        unless they appear in the given paramter_list.

        """
        if hasattr(parameter_list_or_dict, 'has_key'):
            # already a dictionary
            pl = parameter_list_or_dict
        else:
            pl, k = parse_parameter_list(parameter_list)
            if k < len(parameter_list):
                raise ParseError('Invalid parameter list',paramter_list,k)
        self.parmdict = dict(pl)

    def set(self, content_type_string, with_parameters=True):
        """Parses the content type string and sets this object to it's value.

        For a more complete description of the arguments, see the
        documentation for the parse_media_type() function in this module.
        """
        mt, k = parse_media_type( content_type_string, with_parameters=with_parameters )
        if k < len(content_type_string):
            raise ParseError('Not a valid content type',content_type_string, k)
        major, minor, pdict = mt
        self._set_major( major )
        self._set_minor( minor )
        self.parmdict = dict(pdict)
        
    def _get_major(self):
        return self._major
    def _set_major(self, s):
        s = s.lower()  # case-insentive
        if not is_token(s):
            raise ValueError('Major media type contains an invalid character')
        self._major = s

    def _get_minor(self):
        return self._minor
    def _set_minor(self, s):
        s = s.lower()  # case-insentive
        if not is_token(s):
            raise ValueError('Minor media type contains an invalid character')
        self._minor = s

    major = property(_get_major,_set_major,doc="Major media classification")
    minor = property(_get_minor,_set_minor,doc="Minor media sub-classification")

    def __str__(self):
        """String value."""
        s = '%s/%s' % (self.major, self.minor)
        if self.parmdict:
            extra = '; '.join([ '%s=%s' % (a[0],quote_string(a[1],False)) \
                                for a in self.parmdict.items()])
            s += '; ' + extra
        return s

    def __unicode__(self):
        """Unicode string value."""
        return unicode(self.__str__())

    def __repr__(self):
        """Python representation of this object."""
        s = '%s(%s)' % (self.__class__.__name__, repr(self.__str__()))
        return s


    def __hash__(self):
        """Hash this object; the hash is dependent only upon the value."""
        return hash(str(self))

    def __getstate__(self):
        """Pickler"""
        return str(self)

    def __setstate__(self, state):
        """Unpickler"""
        self.set(state)

    def __len__(self):
        """Logical length of this media type.
        For example:
           len('*/*')  -> 0
           len('image/*') -> 1
           len('image/png') -> 2
           len('text/plain; charset=utf-8')  -> 3
           len('text/plain; charset=utf-8; filename=xyz.txt') -> 4

        """
        if self.major == '*':
            return 0
        elif self.minor == '*':
            return 1
        else:
            return 2 + len(self.parmdict)

    def __eq__(self, other):
        """Equality test.

        Note that this is an exact match, including any parameters if any.
        """
        return self.major == other.major and \
                   self.minor == other.minor and \
                   self.parmdict == other.parmdict

    def __ne__(self, other):
        """Inequality test."""
        return not self.__eq__(other)
            
    def _get_media_type(self):
        """Returns the media 'type/subtype' string, without parameters."""
        return '%s/%s' % (self.major, self.minor)

    media_type = property(_get_media_type, doc="Returns the just the media type 'type/subtype' without any paramters (read-only).")

    def is_wildcard(self):
        """Returns True if this is a 'something/*' media type.
        """
        return self.minor == '*'

    def is_universal_wildcard(self):
        """Returns True if this is the unspecified '*/*' media type.
        """
        return self.major == '*' and self.minor == '*'

    def is_composite(self):
        """Is this media type composed of multiple parts.
        """
        return self.major == 'multipart' or self.major == 'message'

    def is_xml(self):
        """Returns True if this media type is XML-based.

        Note this does not consider text/html to be XML, but
        application/xhtml+xml is.
        """
        return self.minor == 'xml' or self.minor.endswith('+xml')

if __name__ == '__main__':
    unittest.main()