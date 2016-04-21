# -*- coding: utf-8 -*- 
'''
Authr: Timo Richter
'''

class _MachineLearner(object):
    """
    An abstract MachineLearner class. Implement the __call__ method in concrete classes.
    """

    # errorMatrix = dict {"TP": int, "FN": int, "FP": int, "TN": int}

    def partial_fit(self, X, y):
        raise NotImplementedError("This is an abstract class!")

    fit = partial_fit
    
    # TODO: add functions: predict()
    
    def getCorrelation(self):
            m = self.errorMatrix
            div = ((m["TP"]+m["FP"])*(m["TP"]+m["FN"])*           \
                    (m["TN"]+m["FP"])*(m["TN"]+m["FN"]))**(1.0/2)
            if div!=0:
                mcc = 1.0*((m["TP"])*(m["TN"])-m["FP"]*m["FN"])/div
                return mcc
            return None

    def getAccuracy(self):
            m = self.errorMatrix
            return float(m["TP"]+m["TN"])/(sum(m.values()))
    
    def printErrorMatrix(self):
            corr = self.getCorrelation()
            print
            print("\t%(TP)d\t%(FN)d\n\t%(FP)d\t%(TN)d"%self.errorMatrix)
            print("\tAccuracy: %0.3f"%self.getAccuracy())
            if corr:
                print("\tMatthews correlation coefficient: %0.3f"%corr)
            print

