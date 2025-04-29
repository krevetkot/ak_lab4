class Memory:
    def __init__(self, size=256):
        self.data = [0] * size
        self.stack_pointer = size
        self.variables_pointer = int(size*0.5)
    
    def clear(self):
        self.data = [0] * len(self.data)
    
    def __getitem__(self, addr):
        return self.data[addr]
    
    def setitem(self, addr, value):
        self.data[addr] = value

    def setvariable(self, value):
        self.data[self.variables_pointer] = value
        self.variables_pointer += 1