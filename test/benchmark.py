import os
import sys
import time

from StringIO import StringIO

class Benchmark(object):
  """ Example:
  
  - Benchmark.measure(manualBenchmark)
  
  - Benchmark.measure(manualBenchmark, 'second run')

  - Benchmark.bm(manualBenchmark, manualBench2)
  
  - Benchmark.bm(('Manual', manualBench2), ('Automatic', manualBenchmark))
  """

  @staticmethod
  def measure(function, label=''):
    """ Time the execution of a single function. """
    if not callable(function):
      raise TypeError("Expecting a function")
    label = label or function.__name__
    Benchmark.bm((label, function))
  
  @staticmethod
  def bm(*args, **kwargs):
    """ Time the execution of multiple functions and display
    the results in a readable way.
    
    The only named parameter allowed is `rehearse`
    """
    rehearse = kwargs.get('rehearse', False)
    new_stdout = StringIO()
    sys.stdout = sys.stderr = new_stdout
    
    try:
      results = {}
      order = []
      is_tuples = isinstance(args[0], tuple)
      if is_tuples:
        for l, f in args:
          if not callable(f):
            raise TypeError("Expecting a function for %s" % l)
          order.append(l)
          results[l] = f
      else:
        for f in args:
          if not callable(f):
            raise TypeError("Expecting a list of functions")
          order.append(f.__name__)
          results[f.__name__] = f
          
      max_label = max(map(len, order))
      print >> sys.__stdout__, "%s    user        system      total       real" % (" " * (max_label + (6 if rehearse else 2)))
      total = TimeStruct(0, 0, 0)
      for l in order:
        if rehearse:
          t = Benchmark._exec(results[l])
          print >> sys.__stdout__,  "%s%s(r): %11.6f %11.6f %11.6f %11.6f" % (l, ' ' * (max_label - len(l)), t.utime, t.stime, t.ttime, t.rtime)

        indent = ' ' * (max_label - len(l) + (3 if rehearse else 0))
        t = Benchmark._exec(results[l])
        print >> sys.__stdout__,  "%s%s: %11.6f %11.6f %11.6f %11.6f" % (l, indent, t.utime, t.stime, t.ttime, t.rtime)
        total = total + t
        
          
      if len(results) > 1:
        print >> sys.__stdout__, ''
        print >> sys.__stdout__,  "Total%s: %11.6f %11.6f %11.6f %11.6f" % (" " * (max_label - 5 + (3 if rehearse else 0)) , total.utime, total.stime, total.ttime, total.rtime)
    finally:
      sys.stdout = sys.__stdout__
      sys.stderr = sys.__stderr__
      print 
      print "Output:"
      print new_stdout.getvalue()

    
      
  @staticmethod
  def _print(order, results):
    max_label = max(map(len, order))
    print "%s    user        system      total       real" % (" " * (max_label + 2))
    total = TimeStruct(0, 0, 0)
    for l in order:
      indent = ' ' * (max_label - len(l))
      t = results[l]
      print "%s%s: %11.6f %11.6f %11.6f %11.6f" % (l, indent, t.utime, t.stime, t.ttime, t.rtime)
      total = total + t
    if len(results) > 1:
      print 
      print "Total%s: %11.6f %11.6f %11.6f %11.6f" % (" " * (max_label - 5) , total.utime, total.stime, total.ttime, total.rtime)
      
  @staticmethod
  def _exec(function):
    tstart = TimeStruct.new()
    try:
      function()
    finally:
      tstop = TimeStruct.new()
    return (tstop - tstart)
  
  
class TimeStruct(object):
  __slots__ = ['utime', 'stime', 'rtime', 'ttime', '_format']
  
  @staticmethod
  def new():
    ost = os.times()
    return TimeStruct(ost[0], ost[1], time.time())
  
  def __init__(self, u, s, r, format="%.6f"):
    self.utime = u
    self.stime = s
    self.rtime = r
    self.ttime = u + s
    self._format = (format + ' ') * 4
    
  def __sub__(self, other):
    return TimeStruct(self.utime - other.utime,
                      self.stime - other.stime,
                      self.rtime - other.rtime)
  
  def __add__(self, other):
    return TimeStruct(self.utime + other.utime,
                      self.stime + other.stime,
                      self.rtime + other.rtime)
  
  def __str__(self):
    return self._format % (self.utime, self.stime, self.rtime, self.ttime)
  

