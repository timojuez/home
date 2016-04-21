class TerminalPrint(object):
    """
    Printing manager for terminal output
        - Supports multiple levels
    """
    depth = []
    showingStatus = []
    
    @classmethod
    def open(self, progress, maxprogress, msg):
        self.depth.append(0)
        self.showingStatus.append(False)
        sys.stdout.write("\033[2K \r\t(%d/%d) %s"%(progress,maxprogress,msg))

    @classmethod
    def write(self,msg):
        self.showingStatus[-1] = False
        sys.stdout.write("\n \033[2K \r\t\t%s"%msg)
        #self.depth[-1] += ceil(terminalwidth*1.0/msg) # FIXME: TODO
        self.depth[-1] += 1
        sys.stdout.flush()
        
    @classmethod
    def status(self, msg):
        if self.showingStatus[-1]:
            sys.stdout.write("\033[2K \r\t\t%s"%msg)
            sys.stdout.flush()
        else: 
            r = self.write(msg)
            self.showingStatus[-1] = True
            return r

    @classmethod
    def close(self):
        sys.stdout.write("\r")
        sys.stdout.write("\033[K\r\033[1A"*self.depth[-1])
        sys.stdout.write("\033[K\r")
        self.showingStatus.pop()
        self.depth.pop()

