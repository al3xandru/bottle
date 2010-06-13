import new
import unittest

class DynamicMethods(unittest.TestCase):
  def setUp(self):
    class ChildClass(RootClass): pass
    
    self.ChildClass = ChildClass
    self.child = ChildClass()
    
    def instance_child_method(obj): return "childclass"
    def static_child_method(): return "childclass"
    def class_child_method(kls): return "childclass"
    
    self.instance_method = instance_child_method
    self.static_method = static_child_method
    self.class_method = class_child_method
    
  def testNormalMethod(self):
    self.assertEquals(self.child.normal_method(), "rootclass")
    
    self.child.normal_method = new.instancemethod(self.instance_method, self.child, None)
    
    self.assertEquals(self.child.normal_method(), "childclass")
    
  def testAllInstanceMethod(self):
    self.assertEquals(self.child.normal_method(), "rootclass")

    self.ChildClass.normal_method = new.instancemethod(self.instance_method, None, self.ChildClass)
      
    self.assertEquals(self.ChildClass().normal_method(), "childclass")
    
  def testFailingNormalMethod(self):
    self.assertEquals(self.child.normal_method(), "rootclass")
    
    def method(): return "childclass"
    
    self.child.normal_method = new.instancemethod(method, self.child, None)
    
    self.assertRaises(TypeError, self.child.normal_method)
    
  def testUnderscoreMethod(self):
    self.child._underscore_method = new.instancemethod(self.instance_method, self.child, None)
    
    self.assertEquals(self.child._underscore_method(), "childclass")
    
  def testDoubleUnderscoreMethod(self):
    self.child.__underscore_method = new.instancemethod(self.instance_method, self.child, None)
    
    self.assertNotEquals(self.child.return_double_underscore_method(), "childclass")
    self.assertEquals(self.child.return_double_underscore_method(), "rootclass")
    
  def testStaticMethod(self):
    self.assertEquals(self.ChildClass.static_method(), "rootclass")
    
    self.ChildClass.static_method = staticmethod(self.static_method)
    
    self.assertEquals(self.ChildClass.static_method(), "childclass")
    self.assertEquals(self.ChildClass().static_method(), "childclass")
    
  def testClassMethod(self):
    self.assertEquals(self.ChildClass.class_method(), "rootclass")
    
    self.ChildClass.class_method = classmethod(self.class_method)
    
    self.assertEquals(self.ChildClass.class_method(), "childclass")
    self.assertEquals(self.ChildClass().class_method(), "childclass")
    
  def testClassMethodWithNew(self):
    self.assertEquals(self.ChildClass.class_method(), "rootclass")
    
    self.ChildClass.class_method = new.instancemethod(self.class_method, self.ChildClass, None)
    
    self.assertEquals(self.ChildClass.class_method(), "childclass")
    self.assertEquals(self.ChildClass().class_method(), "childclass")


class RootClass(object):
  def normal_method(self):
    return "rootclass"
  
  def _underscore_method(self):
    return "rootclass"
  
  def __underscore_method(self):
    return "rootclass"
  
  def return_double_underscore_method(self):
    return self.__underscore_method()
  
  @staticmethod
  def static_method():
    return "rootclass"
  
  @classmethod
  def class_method(kls):
    return "rootclass"
  
    
if __name__ == '__main__':
  unittest.main()