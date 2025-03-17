from injector import Injector, inject

class A:
  name:str = 'llm'

@inject
class B:
  def __init__(self, a:A):
    self.a = a

  def print_name(self):
    print(self.a.name)
    
injector = Injector()

b = injector.get(B)

b.print_name()