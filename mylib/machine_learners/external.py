# -*- coding: utf-8 -*- 
'''
Download C5 binaries from https://www.rulequest.com/see5-info.html
(or other binaries) and adjust C5.BINS.

Authr: Timo Richter
'''

from collections import OrderedDict
import subprocess, codecs, os, re

from tempdir import Tempdir
from abstract_machine_learner import _MachineLearner

class _ExternalMachineLearner(_MachineLearner):
    """
    This class is a wrapper for the C4.5 and C5 implementations.
    It writes the matrix in a text file and reads the program call's output.
    """
    BINS = ""
    FILESTEM = "filestem"
    TYPES={ # data type and corresponding values
        bool: [str(int(True)),str(int(False))], 
        int: ["continuous"], 
        long: ["continuous"],
    }
    
    def __init__(self, classes, featureNames, featureTypes=None, keep=False, verbose=False):
        """
        @classes List of all classes, e.g. ["Good", "Bad"]
        @featureNames List of identifies of all features, order according to the 
            matrix columns! ["Amount of friends","Has cancer"]
        @featureTypes This defines the range of the feature values, e.g. [int, bool]. 
            Define custom ranges like this: [["1","2"],["Yes","Maybe","No"]]
        """
        if featureTypes is None:
            featureTypes = [int]*len(featureNames)
        self.names = {"classes":classes, "featureNames":featureNames, "featureTypes":featureTypes}
        self.tempdir = Tempdir()
        self.tempdir.open("C4_5",keep)
        self.verbose=verbose
        self.filestemFullPath = os.path.join(str(self.tempdir),self.FILESTEM)
        self._do_evaluate = self.evaluate
        self.evaluate = self._before_evaluate
        self._openDataFiles()

    def score(self, X, y):
        if self.verbose: print("\t\tSave test data...")
        self.partial_score(X, y)
        self.evaluate()
        
    def _openDataFiles(self):
        self.trainingDataFile = codecs.open("%s.%s"%(self.filestemFullPath, "data"), "w", "utf-8")
        self.testDataFile = codecs.open("%s.%s"%(self.filestemFullPath, "test"), "w", "utf-8")    

    def _closeDataFiles(self):
        self.trainingDataFile.close()
        self.testDataFile.close()

    def _programCall(self, bin):
        output=os.path.join(str(self.tempdir),"%s.output"%bin)
        f=open(output,"w")
        try:
            subprocess.call([os.path.join(self.BINS,bin), "-f", self.filestemFullPath],stdout=f,universal_newlines=True)
        except OSError: raise OSError("OSError: %s not found. Maybe adjust external.*.BINS."%os.path.join(self.BINS,bin))
        f.close()
        return output
        
    def _storeData(self, output, fv, cls):
        try:
            output.write("%s\n" % ", ".join([self._toStr(y) for y in [x for x in fv]+[cls]]))
        except ValueError:
            raise NotImplementedError("Value/IO-Error: Cannot evaluate twice using the same external machine learner. Please instantiate the class again.")
    
    def _toStr(self, x):
        try:
            y=int(x)
            #if y<0: return "?"
        except ValueError: y=x
        return str(y)
        # does this, but was too slow:
        #if type(x) is bool: return str(int(x))
        #return str(x)
        
    def escapeName(self, n):
        """ Returns str @n without unsave characters """
        return n.replace(",","_").replace(":","_").replace(".","_").replace("?","_").replace("|","_")
        
    def _createNames(self):
        """ make names file """
        filetext = "%(classes)s.\n\n%(features)s\n"
        classes = ", ".join(map(lambda x:str(x), self.names["classes"]))
        featuresDict = OrderedDict()
        for f,t in zip(self.names["featureNames"], self.names["featureTypes"]):
            if type(t) is list: featuresDict[f] = map(lambda x:str(x), t)
            elif t in self.TYPES: featuresDict[f] = self.TYPES[t]
            else: raise TypeError("Error: Type '%s' not in C5.TYPES. In featureTypes pass a "
                                 +"list with its possible values instead."%str(t))
        if len(featuresDict) != len(self.names["featureNames"]):
            raise Exception("ML: Error: Maybe a feature names occurs more than once?")
            
        features = "\n".join([
            "%s: %s."%(self.escapeName(f),", ".join(t)) 
            for f,t in featuresDict.items()
        ])
        with codecs.open("%s.names"%self.filestemFullPath, 
                "w", "utf-8"
                ) as f:
            f.write(filetext%{"classes":classes,"features":features})
    
    def partial_fit(self, X, y):
        """
        @X Matrix, list of lists
        @y class of each sample, list
        """
        if len(X[0]) != len(self.names["featureNames"]):
            print("WARNING: Machine Learning: On partial_fit(): amount of feature names does not match amout of features")
            
        for fv,cls in zip(X,y):
            self._storeData(self.trainingDataFile, fv, cls)
        
    def fit(self, X, y):
        if self.verbose: print("\t\tSave training data...")
        self.partial_fit(X,y)

    def partial_score(self, X, y):
        for fv,cls in zip(X,y):
            self._storeData(self.testDataFile, fv, cls)

    def _before_evaluate(self):
        self._closeDataFiles()
        if self.verbose: print("\t\tSave names file...")
        self._createNames()
        self._do_evaluate()
        self.tempdir.close()
        #self._openDataFiles()
        
    def evaluate(self):
        """
        This will automatically call _before_evaluate() before.
        """
        raise NotImplementedError("Extend class and implement predict().")

    def _parseErrorMatrix(self, f):
        with open(f, "r") as fp:
            content = fp.read()
        ms=re.findall("classified as\n[^\n]*\n\t\s{0,6}(\d*)\s{1,6}(\d*)[^\n]*\n\t\s{0,6}(\d*)\s{1,6}(\d*)",content)
        ms=[[n if n!='' else 0 for n in m] for m in ms]
        try:
            ms=[[int(n) for n in m] for m in ms]
        except TypeError: 
            raise TypeError("Can't parse error matrix.")
        ms=[dict(zip(["TP","FN","FP","TN"],m)) for m in ms]
        return ms # list of matrixes
    
    def _printErrorMatrixes(self, ms):
        #for m in ms: self._printErrorMatrix(m)
        self._printErrorMatrix(ms[-1])
            
class C4_5(_ExternalMachineLearner):
    """
    output from c4.5 -f filestem: 
        feature = value: class (all occurrences of feature=value/occurrences of feature=value where class is different)
    output from c4.5rules:
        Error = 100%–accuracy
        Test data := training data; set(Used), set(Wrong)
        for r in rules: conjunction([line for line in r])
    """
    BINS = './r8'
    def evaluate(self):
        if self.verbose:
            print("\t\tCall c4.5...")
        self._programCall("c4.5")
        if self.verbose:
            print("\t\tCall c4.5rules...")
        programOutput = self._programCall("c4.5rules")
        self.errorMatrix = self._parseErrorMatrix(programOutput)[-1]

class C5(_ExternalMachineLearner):
    BINS = './programs/C50'

    def evaluate(self):
        if self.verbose: print("\t\tCall c5...")
        programOutput = self._programCall("c5.0")
        self.errorMatrix = self._parseErrorMatrix(programOutput)[-1]

   
