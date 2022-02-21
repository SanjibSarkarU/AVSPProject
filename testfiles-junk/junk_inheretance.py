class Parents:
    def __init__(self, att1:str, att2):
        self.att1 = att1

    def test(self,att2:str):
        print(self.att1+att2)

class Child(Parents):
    def __init__(self, x:str):
        Parents.__init__(self, att1=x, att2=att2)
        self.att1 = x
        print('Child:', self.att1)

p = Parents('P')
# p.test('-Class')

c = Child('C')