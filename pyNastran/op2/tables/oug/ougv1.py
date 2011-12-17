import sys
import copy
from struct import unpack

# pyNastran
from ougv1_Objects import (
     temperatureObject,displacementObject,  # analysisCode=1, formatCode=1 sortCode=0
     complexDisplacementObject,             # analysisCode=5  formatCode=3 sortCode=1
     fluxObject,                            # analysisCode=1, formatCode=1 sortCode=3
     nonlinearTemperatureObject,            # analysisCode=10,formatCode=1 sortCode=0 ???
     )

from oug_eigenvectors import (
     eigenVectorObject,                     # analysisCode=2, sortCode=0 formatCode   tableCode=7
     complexEigenVectorObject,              # analysisCode=5, sortCode=1 formatCode=1 tableCode=7
     realEigenVectorObject,                 # analysisCode=9, sortCode=1 formatCode=1 tableCode=7
     )

class OUGV1(object):
    """Table of displacements/velocities/acceleration/heat flux/temperature"""

    def readTable_OUG1(self):
        self.tableName = 'OUG'
        table3 = self.readTable_OUGV1_3
        table4Data = self.readOUGV1_Data
        self.readResultsTable(table3,table4Data)
        self.deleteAttributes_OUG()

    def deleteAttributes_OUG(self):
        params = ['lsdvm','mode','eigr','modeCycle','freq','dt','lftsfq','thermal','randomCode','fCode','numWide','acousticFlag']
        self.deleteAttributes(params)
    
    def addDataParameter(self,data,Name,Type,FieldNum,applyNonlinearFactor=True):
        #self.mode      = self.getValues(data,'i',5) ## mode number
        value = self.getValues(data,Type,FieldNum)
        setattr(self,Name,value)
        self.dataCode[Name] = value
        
        if applyNonlinearFactor:
            self.nonlinearFactor = value
            self.dataCode['nonlinearFactor'] = value
            self.dataCode['name'] = Name

    def readTable_OUGV1_3(self,iTable): # iTable=-3
        bufferWords = self.getMarker()
        if self.makeOp2Debug:
            self.op2Debug.write('bufferWords=%s\n' %(str(bufferWords)))
        #print "2-bufferWords = ",bufferWords,bufferWords*4,'\n'

        data = self.getData(4)
        bufferSize, = unpack('i',data)
        data = self.getData(4*50)
        #print self.printBlock(data)
        
        (three) = self.parseApproachCode(data)

        self.addDataParameter(data,'randomCode',  'i',8,False)   ## random code
        self.addDataParameter(data,'formatCode',  'i',9,False)   ## format code
        self.addDataParameter(data,'numWide',     'i',10,False)  ## number of words per entry in record; @note is this needed for this table ???
        self.addDataParameter(data,'acousticFlag','f',13,False)  ## acoustic pressure flag
        self.addDataParameter(data,'thermal',     'i',23,False)  ## thermal flag; 1 for heat ransfer, 0 otherwise
        
        #self.printBlock(data) # on
        ## assuming tCode=1
        if self.analysisCode==1:   # statics / displacement / heat flux
            self.addDataParameter(data,'lsdvmn',  'i',5,False)   ## load set number
        elif self.analysisCode==2: # real eigenvalues
            self.addDataParameter(data,'mode',     'i',5)   ## mode number
            self.addDataParameter(data,'eigr',     'f',6,False)   ## real eigenvalue
            self.addDataParameter(data,'modeCycle','i',7,False)   ## mode or cycle @todo confused on the type - F1???
            assert self.dataCode['name']=='mode'
            #print "mode(5)=%s eigr(6)=%s modeCycle(7)=%s" %(self.mode,self.eigr,self.modeCycle)
        #elif self.analysisCode==3: # differential stiffness
        #    self.lsdvmn = self.getValues(data,'i',5) ## load set number
        #elif self.analysisCode==4: # differential stiffness
        #    self.lsdvmn = self.getValues(data,'i',5) ## load set number
        elif self.analysisCode==5:   # frequency
            self.addDataParameter(data,'freq','f',5)   ## frequency
        elif self.analysisCode==6: # transient
            self.addDataParameter(data,'dt','f',5)   ## time step
            #print "DT(5)=%s" %(self.dt)
        elif self.analysisCode==7: # pre-buckling
            self.addDataParameter(data,'lsdvmn',  'i',5)   ## load set number
            #print "LSDVMN(5)=%s" %(self.lsdvmn)
        elif self.analysisCode==8: # post-buckling
            self.addDataParameter(data,'lsdvmn',  'i',5)   ## load set number
            self.addDataParameter(data,'eigr',    'f',6,False)   ## real eigenvalue
            #print "LSDVMN(5)=%s  EIGR(6)=%s" %(self.lsdvmn,self.eigr)
        elif self.analysisCode==9: # complex eigenvalues
            self.addDataParameter(data,'mode','i',5)   ## mode number
            self.addDataParameter(data,'eigr','f',6,False)   ## real eigenvalue
            self.addDataParameter(data,'eigi','f',7,False)   ## imaginary eigenvalue
            #print "mode(5)=%s  eigr(6)=%s  eigi(7)=%s" %(self.mode,self.eigr,self.eigi)
        elif self.analysisCode==10: # nonlinear statics
            self.addDataParameter(data,'lftsfq','f',5)   ## load step
            #print "LFTSFQ(5) = %s" %(self.lftsfq)
        elif self.analysisCode==11: # old geometric nonlinear statics
            self.addDataParameter(data,'lsdvmn',  'i',5)   ## load set number
            #print "LSDVMN(5)=%s" %(self.lsdvmn)
        elif self.analysisCode==12: # contran ? (may appear as aCode=6)  --> straight from DMAP...grrr...
            self.addDataParameter(data,'lsdvmn',  'i',5)   ## load set number
            #print "LSDVMN(5)=%s" %(self.lsdvmn)
        else:
            raise InvalidAnalysisCodeError('invalid analysisCode...analysisCode=%s' %(self.analysisCode))
        # tCode=2
        #if self.analysisCode==2: # sort2
        #    self.lsdvmn = self.getValues(data,'i',5)
        
        #print "*iSubcase=%s"%(self.iSubcase)
        #print "analysisCode=%s tableCode=%s thermal=%s" %(self.analysisCode,self.tableCode,self.thermal)

        #self.printBlock(data)
        self.readTitle()


    def readOUGV1_Data(self):
        #print "self.analysisCode=%s tableCode(1)=%s thermal(23)=%g" %(self.analysisCode,self.tableCode,self.thermal)
        tfsCode = [self.tableCode,self.formatCode,self.sortCode]
        #if self.thermal==2:
        #    self.skipOES_Element()
        #print "tfsCode=%s" %(tfsCode)
        # displacement
        if   tfsCode==[1,1,0]:
            self.readOUGV1_Data_table1_format1_sort0()
        #elif tfsCode==[1,1,1]:
        #    self.readOUGV1_Data_table1_format1_sort1()
        elif tfsCode==[1,2,0]:
            self.readOUGV1_Data_table1_format2_sort0()
        #elif tfsCode==[1,2,1]:
        #    self.readOUGV1_Data_table1_format2_sort1()
        #elif tfsCode==[1,2,2]:
        #    self.readOUGV1_Data_table1_format2_sort2()
        #elif tfsCode==[1,3,0]:
        #    self.readOUGV1_Data_table1_format3_sort0()
        #elif tfsCode==[1,3,1]:
        #    self.readOUGV1_Data_table1_format3_sort1()
        #elif tfsCode==[1,3,2]:
        #    self.readOUGV1_Data_table1_format3_sort2()

        # modes
        elif tfsCode==[7,1,0]:
            self.readOUGV1_Data_table7_format1_sort0()
        #elif tfsCode==[7,1,1]:
        #    self.readOUGV1_Data_table7_format1_sort1()
        elif tfsCode==[7,2,0]:
            self.readOUGV1_Data_table7_format2_sort0()
        #elif tfsCode==[7,2,1]:
        #    self.readOUGV1_Data_table7_format2_sort1()
        #elif tfsCode==[7,2,2]:
        #    self.readOUGV1_Data_table7_format2_sort2()
        #elif tfsCode==[7,3,0]:
        #    self.readOUGV1_Data_table7_format3_sort0()
        #elif tfsCode==[7,3,1]:
        #    self.readOUGV1_Data_table7_format3_sort1()
        #elif tfsCode==[7,3,2]:
        #    self.readOUGV1_Data_table7_format3_sort2()

        # velocity
        elif tfsCode==[10,1,0]:
            self.readOUGV1_Data_table10_format1_sort0()
        #elif tfsCode==[10,1,1]:
        #    self.readOUGV1_Data_table10_format1_sort1()
        #elif tfsCode==[10,2,0]:
        #    self.readOUGV1_Data_table10_format2_sort0()
        #elif tfsCode==[10,2,1]:
        #    self.readOUGV1_Data_table10_format2_sort1()
        #elif tfsCode==[10,2,2]:
        #    self.readOUGV1_Data_table10_format2_sort2()
        #elif tfsCode==[10,3,0]:
        #    self.readOUGV1_Data_table10_format3_sort0()
        #elif tfsCode==[10,3,1]:
        #    self.readOUGV1_Data_table10_format3_sort1()
        #elif tfsCode==[10,3,2]:
        #    self.readOUGV1_Data_table10_format3_sort2()

        # Acceleration vector
        elif tfsCode==[11,1,0]:
            self.readOUGV1_Data_table11_format1_sort0()
        #elif tfsCode==[11,1,1]:
        #    self.readOUGV1_Data_table11_format1_sort1()
        #elif tfsCode==[11,2,0]:
        #    self.readOUGV1_Data_table11_format2_sort0()
        #elif tfsCode==[11,2,1]:
        #    self.readOUGV1_Data_table11_format2_sort1()
        #elif tfsCode==[11,2,2]:
        #    self.readOUGV1_Data_table11_format2_sort2()
        #elif tfsCode==[11,3,0]:
        #    self.readOUGV1_Data_table11_format3_sort0()
        #elif tfsCode==[11,3,1]:
        #    self.readOUGV1_Data_table11_format3_sort1()
        #elif tfsCode==[11,3,2]:
        #    self.readOUGV1_Data_table11_format3_sort2()

        else:
            #print "***start skipping***"
            print 'skipping approach/table/format/sortCode=%s on OUG table' %(self.atfsCode)
            print self.codeInformation()
            self.skipOES_Element()
            #print "***end skipping***"
            #raise Exception('bad approach/table/format/sortCode=%s on OUG table' %(self.atfsCode))
        ###
        #print self.obj

    def readOUGV1_Data_table1_format1_sort0(self):
        print self.codeInformation()
        assert self.formatCode==1 # Real
        assert self.sortCode==0   # Real

        if self.thermal==0 or self.thermal>1:  ## @warning dont leave the thermal>0!!!!
            if self.analysisCode==1: # displacement
                #print "isDisplacement"
                #print "self.dataCode = ",self.dataCode
                self.createTransientObject(self.displacements,displacementObject)

            elif self.analysisCode==5: # frequency displacement
                #print "isFrequencyDisplacement"
                self.createTransientObject(self.displacements,eigenVectorObject)

            elif self.analysisCode==6: # transient displacement
                #print "isTransientDisplacement"
                self.createTransientObject(self.displacements,displacementObject)

            elif self.analysisCode==7: # pre-buckling displacement
                #print "isPreBucklingDisplacement"
                self.createTransientObject(self.displacements,displacementObject)

            elif self.analysisCode==8: # post-buckling eigenvector
                #print "isPostBucklingEigenvector"
                self.createTransientObject(self.displacements,eigenVectorObject)

            #elif self.analysisCode==9: # nonlinear static eigenvector
                #print "isComplexEigenvalues"
                #self.createTransientObject(self.complexEigenvalues,eigenVectorObject)

            elif self.analysisCode==10: # nonlinear static displacement
                #print "isNonlinearStaticDisplacement"
                self.createTransientObject(self.nonlinearDisplacements,displacementObject)
            elif self.analysisCode==11: # nonlinear geometric static displacement
                #print "isNonlinearStaticDisplacement"
                self.createTransientObject(self.nonlinearDisplacements,displacementObject)
            else:
                pass
                #raise Exception('unsupported OUGV1 static solution...atfsCode=%s' %(self.atfsCode))
            ###

        elif self.thermal==1:
            if self.analysisCode==1: # temperature
                #print "isTemperature"
                self.createTransientObject(self.temperatures,temperatureObject)
            elif self.analysisCode==6: # transient temperature
                #print "isTransientTemperature"
                self.createTransientObject(self.temperatures,temperatureObject)
            elif self.analysisCode==10: # nonlinear static displacement
                #print "isNonlinearStaticTemperatures"
                self.createTransientObject(self.nonlinearTemperatures,nonlinearTemperatureObject)
            else:
                #raise Exception('unsupported OUGV1 thermal solution...atfsCode=%s' %(self.atfsCode))
                pass
            ###
        else:
            pass
            #raise Exception('invalid OUGV1 thermal flag...not 0 or 1...flag=%s' %(self.thermal))
        ###
        if self.obj:
            self.readScalars8()
        else:
            self.skipOES_Element()
        ###
        #print self.obj
        #return

    def readOUGV1_Data_table7_format1_sort0(self):
        assert self.formatCode==1 # Real
        assert self.sortCode==0   # Real

        if self.thermal==0 or self.thermal>1:  ## @warning dont leave the thermal>0!!!!
            if self.analysisCode==2: # nonlinear static eigenvector
                #print "isEigenvector"
                self.createTransientObject(self.eigenvectors,eigenVectorObject)
            elif self.analysisCode==8: # post-buckling eigenvector
                #print "isPostBucklingEigenvector"
                self.createTransientObject(self.eigenvectors,realEigenVectorObject)
            else:
                #raise Exception('unsupported OUGV1 static solution...atfsCode=%s' %(self.atfsCode))
                pass
            ###
        elif self.thermal==1:
            #raise Exception('unsupported OUGV1 thermal solution...atfsCode=%s' %(self.atfsCode))
            pass
        else:
            #raise Exception('invalid OUGV1 thermal flag...not 0 or 1...flag=%s' %(self.thermal))
            pass
        ###
        if self.obj:
            self.readScalars8(debug=False)
        else:
            self.skipOES_Element()
        #if self.analysisCode not in [2,8]:
        #    raise Exception('check_format1...')
        ###

    def readOUGV1_Data_table10_format1_sort0(self): # velocity
        assert self.formatCode==1 # Real
        assert self.sortCode==0   # Real
        if self.thermal==0 or self.thermal>1:  ## @warning dont leave the thermal>0!!!!
            if self.analysisCode==1: # velocity
                #print "isVelocity"
                self.createTransientObject(self.velocities,displacementObject)
            elif self.analysisCode==6: # transient velocity
                #print "isTransientVelocity"
                self.createTransientObject(self.velocities,displacementObject)
            else:
                raise Exception('unsupported OUGV1 static solution...atfsCode=%s' %(self.atfsCode))
            ###
        elif self.thermal==1:
            #raise Exception('unsupported OUGV1 thermal solution...atfsCode=%s' %(self.atfsCode))
            pass
        else:
            raise Exception('invalid OUGV1 thermal flag...not 0 or 1...flag=%s' %(self.thermal))
        ###
        if self.obj:
            self.readScalars8(debug=True)
        else:
            self.skipOES_Element()
        ###

    def readOUGV1_Data_table11_format1_sort0(self): # velocity
        assert self.formatCode==1 # Real
        assert self.sortCode==0   # Real
        if self.thermal==0 or self.thermal>1:  ## @warning dont leave the thermal>0!!!!
            if self.analysisCode==1: # acceleration
                #print "isAcceleration"
                self.createTransientObject(self.accelerations,displacementObject)
            elif self.analysisCode==6: # transient acceleration
                #print "isTransientAcceleration"
                self.createTransientObject(self.accelerations,displacementObject)

            else:
                raise Exception('unsupported OUGV1 static solution...atfsCode=%s' %(self.atfsCode))
            ###
        elif self.thermal==1:
            raise Exception('unsupported OUGV1 thermal solution...atfsCode=%s' %(self.atfsCode))
        else:
            raise Exception('invalid OUGV1 thermal flag...not 0 or 1...flag=%s' %(self.thermal))
        ###
        self.readScalars8(debug=True)

    def readOUGV1_Data_table1_format1_sort1(self):
        assert self.formatCode==1 # Real
        assert self.sortCode==1   # Real/Imaginary
        if self.thermal==0:
            if self.analysisCode==5: # complex displacements (real/imaginary)
                #print "isComplexDisplacement"
                self.createTransientObject(self.displacements,complexDisplacementObject)
            #elif self.analysisCode==7: # pre-buckling displacement
                #print "isPreBucklingDisplacement"
                #self.createTransientObject(self.displacements,displacementObject)
            #elif self.analysisCode==9: # nonlinear static eigenvector
                #print "isComplexEigenvalues"
                #self.createTransientObject(self.displacements,eigenVectorObject)
            #elif self.analysisCode==11: # Geometric nonlinear statics
                #print "isNonlinearStaticDisplacement"
                #self.createTransientObject(self.displacements,displacementObject)
            else:
                raise Exception('unsupported OUGV1 static table1_format1_sort1 solution...atfsCode=%s' %(self.atfsCode))
            ###
        else:
            raise Exception('invalid thermal flag...not 0 or 1...flag=%s' %(self.thermal))
        ###
        #print "objName = ",self.obj.name()
        self.readScalars14(debug=False)
        #print self.obj
        #return

    def readOUGV1_Data_table7_format1_sort1(self):
        assert self.formatCode==1 # Real
        assert self.sortCode==1   # Real/Imaginary
        if self.thermal==0:
            #if self.analysisCode==5: # frequency displacement
                #print "isFrequencyDisplacement"
                #self.createTransientObject(self.freqDisplacements,eigenVectorObject)
            #elif self.analysisCode==7: # pre-buckling displacement
                #print "isPreBucklingDisplacement"
                #self.createTransientObject(self.displacements,displacementObject)
            if self.analysisCode==9: # nonlinear static eigenvector
                #print "isComplexEigenvalues"
                self.createTransientObject(self.eigenvectors,complexEigenVectorObject)
            #elif self.analysisCode==11: # Geometric nonlinear statics
                #print "isNonlinearStaticDisplacement"
                #self.createTransientObject(self.displacements,displacementObject)
            else:
                raise Exception('unsupported OUGV1 static table7_format1_sort1 solution...atfsCode=%s' %(self.atfsCode))
            ###
        else:
            raise Exception('invalid thermal flag...not 0 or 1...flag=%s' %(self.thermal))
        ###
        #print "objName = ",self.obj.name()
        self.readScalars14()
        #print self.obj
        #return

    def readOUGV1_Data_table10_format1_sort1(self):
        assert self.formatCode==1 # Real
        assert self.sortCode==1   # Real/Imaginary
        if self.thermal==0:
            if self.analysisCode==5: # frequency velocity
                #print "isFrequencyVelocity"
                self.createTransientObject(self.velocities,complexEigenVectorObject)
            #elif self.analysisCode==7: # pre-buckling displacement
                #print "isPreBucklingDisplacement"
                #self.createTransientObject(self.displacements,displacementObject)
            elif self.analysisCode==9: # nonlinear static eigenvector
                #print "isComplexVelocities"
                self.createTransientObject(self.velocites,complexDisplacementObject)
            #elif self.analysisCode==11: # Geometric nonlinear statics
                #print "isNonlinearStaticDisplacement"
                #self.createTransientObject(self.displacements,displacementObject)
            else:
                raise Exception('unsupported OUGV1 static table7_format1_sort1 solution...atfsCode=%s' %(self.atfsCode))
            ###
        else:
            raise Exception('invalid thermal flag...not 0 or 1...flag=%s' %(self.thermal))
        ###
        #print "objName = ",self.obj.name()
        self.readScalars14()
        #print self.obj
        #return

    def readOUGV1_Data_table1_format2_sort0(self):
        if self.thermal==0:
            if self.analysisCode==6: # transient displacement
                #print "isTransientDisplacement"
                self.createTransientObject(self.displacements,displacementObject)
            else:
                raise Exception('unsupported OUGV1 static solution...atfsCode=%s' %(self.atfsCode))
            ###
        elif self.thermal==1:
            raise Exception('unsupported OUGV1 thermal solution...atfsCode=%s' %(self.atfsCode))
        else:
            raise Exception('invalid thermal flag...not 0 or 1...flag=%s' %(self.thermal))
        ###
        self.readScalars8()

    def readOUGV1_Data_table1_format2_sort1(self):
        assert self.formatCode==2 # Real/Imaginary
        assert self.sortCode==1   # Real/Imaginary
        if self.thermal==0:
            if self.analysisCode==5: # frequency displacement
                #print "isFrequencyDisplacement"
                self.createTransientObject(self.displacements,complexDisplacementObject)
                self.readScalarsF14()
            elif self.analysisCode==7: # pre-buckling displacement
                #print "isPreBucklingDisplacement"
                self.createTransientObject(self.displacements,displacementObject)
                self.readScalarsF14()
            #elif self.analysisCode==9 and self.sortCode==1: # nonlinear static eigenvector
                #print "isComplexEigenvalues"
                #self.createTransientObject(self.complexEigenvalues,eigenVectorObject)
                #self.readScalars8()
            else:
                raise Exception('unsupported OUGV1 static solution...atfsCode=%s' %(self.atfsCode))
            ###
        elif self.thermal==1:
            raise Exception('unsupported OUGV1 thermal solution...atfsCode=%s' %(self.atfsCode))
        else:
            raise Exception('invalid thermal flag...not 0 or 1...flag=%s' %(self.thermal))
        ###
        #print self.obj
        #return


    def readOUGV1_Data_table1_format3_sort0(self):
        assert self.formatCode==3 # Magnitude/Phase
        assert self.sortCode==0   # Real
        if self.thermal==0:
            raise Exception('unsupported OUGV1 static solution...atfsCode=%s' %(self.atfsCode))
            if self.analysisCode==1: # displacement
                #print "isDisplacement"
                self.createTransientObject(self.displacements,displacementObject)
            elif self.analysisCode==2: # nonlinear static eigenvector
                #print "isEigenvector"
                self.createTransientObject(self.eigenvectors,eigenVectorObject)
            elif self.analysisCode==5: # frequency displacement
                #print "isFreqDisplacement"
                self.createTransientObject(self.freqDisplacements,displacementObject)
            elif self.analysisCode==6: # transient displacement
                #print "isTransientDisplacement"
                self.createTransientObject(self.displacements,displacementObject)
            elif self.analysisCode==7: # pre-buckling displacement
                #print "isPreBucklingDisplacement"
                self.createTransientObject(self.preBucklingDisplacements,displacementObject)
            elif self.analysisCode==10: # transient velocity
                #print "isTransientVelocity"
                self.createTransientObject(self.velocities,displacementObject,self.dt)
            else:
                raise Exception('unsupported OUGV1 static solution...atfsCode=%s' %(self.atfsCode))
            ###
        elif self.thermal==1:
            raise Exception('unsupported OUGV1 thermal solution...atfsCode=%s' %(self.atfsCode))
        else:
            raise Exception('invalid thermal flag...not 0 or 1...flag=%s' %(self.thermal))
        ###
        self.readScalars8()

    def readOUGV1_Data_table1_format3_sort1(self):
        assert self.formatCode==3 # Magnitude/Phase
        assert self.sortCode==1   # Imaginary
        if self.thermal==0:
            if self.analysisCode==5: # complex frequency displacement
                #print "isComplexFreqDisplacement"
                self.createTransientObject(self.displacements,complexDisplacementObject)
            elif self.analysisCode==7: # pre-buckling displacement
                #print "isComlexPreBucklingDisplacement"
                self.createTransientObject(self.complexDisplacements,displacementObject)
            elif self.analysisCode==9: # nonlinear static eigenvector
                #print "isComplexEigenvalues"
                self.createTransientObject(self.complexEigenvalues,eigenVectorObject)
            else:
                raise Exception('unsupported OUGV1 static solution...atfsCode=%s' %(self.atfsCode))
            ###
        elif self.thermal==1:
            raise Exception('unsupported OUGV1 thermal solution...atfsCode=%s' %(self.atfsCode))
        else:
            raise Exception('invalid thermal flag...not 0 or 1...flag=%s' %(self.thermal))
        ###
        self.readScalars14()

