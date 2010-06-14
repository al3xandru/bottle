- Improve behavior on HTTPError (basically it's very difficult to return something else than HTML) 
- Plugin automatic view dispatching for requests returning text/html
  (even with media-type detection I'm not sure how I can delegate to templates when preferred content is text/html)
