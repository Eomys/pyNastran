#pylint: disable=C0301,C0103
"""
This file defines the OUG Table, which contains:
 * Real/Complex Displacement
   - DISPLACEMENT = ALL
 * Real/Complex Acceleration
   - ACCELERATION = ALL
 * Real/Complex Velocity
   - VELOCITY = ALL
 * Real/Complex Eigenvectors
   - DISPLACEMENT = ALL
 * Real Temperature
   - DISPLACEMENT = ALL
"""
from struct import Struct
import numpy as np
#from pyNastran import is_release
from pyNastran.utils.numpy_utils import integer_types
from pyNastran.op2.op2_interface.op2_common import OP2Common
from pyNastran.op2.op2_interface.op2_reader import mapfmt

from pyNastran.op2.tables.oug.oug_displacements import (
    RealDisplacementArray, ComplexDisplacementArray)

from pyNastran.op2.tables.oug.oug_velocities import (
    RealVelocityArray, ComplexVelocityArray)

from pyNastran.op2.tables.oug.oug_accelerations import (
    RealAccelerationArray, ComplexAccelerationArray)

from pyNastran.op2.tables.oug.oug_temperatures import (
    RealTemperatureArray)

from pyNastran.op2.tables.oug.oug_eigenvectors import (
    RealEigenvectorArray, ComplexEigenvectorArray,
)

from pyNastran.op2.tables.opg_appliedLoads.opg_load_vector import RealThermalVelocityVectorArray


class OUG(OP2Common):
    """
    OUG : Output U in the global frame

    U is:
     - Displacement
     - Velocity
     - Accelerations

    The global frame is:
     - the analysis coordinate frame, not the 0 coordinate frame
     """
    def __init__(self):
        OP2Common.__init__(self)

    def update_mode_cycle(self, name):
        value = getattr(self, name)
        if value == 0.0:
            #print('table_name=%r mode=%s eigr=%s' % (self.table_name, self.mode, self.eigr))
            value = np.sqrt(np.abs(self.eign)) / (2. * np.pi)
            setattr(self, name, value)
            self.data_code[name] = value

    def _read_otemp1_3(self, data: bytes, ndata: int):
        """SOL 401 table"""
        self.nonlinear_factor = np.nan
        self.is_table_1 = True
        self.is_table_2 = False
        unused_three = self.parse_approach_code(data)
        self.words = [
            'approach_code', 'table_code', '???', 'isubcase',
            '???', '???', '???', '???',
            'format_code', 'num_wide', '???', '???',
            '???', '???', '???', '???',
            '???', '???', '???', '???',
            '???', '???', 'thermal', '???',
            '???', 'Title', 'subtitle', 'label']

        ## format code
        self.format_code = self.add_data_parameter(data, 'format_code', b'i', 9, False)

        ## number of words per entry in record
        self.num_wide = self.add_data_parameter(data, 'num_wide', b'i', 10, False)

        ## nBolt sequence number for SOL 401 preloaded bolts
        self.bolt_seq_id = self.add_data_parameter(data, 'bolt_seq_id', b'i', 28, False)

        if self.analysis_code == 6:  # transient
            # time step
            self.dt = self.add_data_parameter(data, 'dt', b'f', 5)
            self.data_names = self.apply_data_code_value('data_names', ['dt'])
        elif self.analysis_code == 10:  # nonlinear statics
            # load step
            self.lftsfq = self.add_data_parameter(data, 'lftsfq', b'f', 5)
            self.data_names = self.apply_data_code_value('data_names', ['lftsfq'])
        else:  # pragma: no cover
            msg = f'invalid analysis_code...analysis_code={self.analysis_code}\ndata={self.data_code}'
            raise RuntimeError(msg)

        if self.is_debug_file:
            self.binary_debug.write('  approach_code  = %r\n' % self.approach_code)
            self.binary_debug.write('  tCode          = %r\n' % self.tCode)
            self.binary_debug.write('  isubcase       = %r\n' % self.isubcase)
        self._read_title(data)
        self._write_debug_bits()
        #print(self.code_information())

    def _read_otemp1_4(self, data: bytes, ndata: int):
        """SOL 401 table"""
        nfields = ndata // 4
        nnodes = nfields // 2
        result_name = 'temperatures'
        storage_obj = self.temperatures
        real_vector = RealTemperatureArray
        is_cid = False
        self.data_code['_times_dtype'] = 'float32'
        #self._times_dtype = 'float32'
        auto_return = self._create_table_vector(
            result_name, nnodes, storage_obj, real_vector, is_cid=is_cid)
        if auto_return:
            return ndata

        #print(self.obj)
        #print(self.code_information())
        floats = np.frombuffer(data, dtype=self.fdtype).reshape(nnodes, 2).copy()
        ints = np.frombuffer(data, dtype=self.idtype).reshape(nnodes, 2) // 10
        #print(self.obj.get_stats())
        nids = ints[:, 0]
        temps = floats[:, 1]
        self.obj.node_gridtype[:, 0] = nids
        self.obj.data[self.obj.itime, :, 0] = temps
        return ndata

    def _read_oug1_3(self, data: bytes, ndata: int):
        """reads table 3 (the header table)"""
        #self._set_times_dtype()
        self.nonlinear_factor = np.nan
        self.is_table_1 = True
        self.is_table_2 = False
        unused_three = self.parse_approach_code(data)
        self.words = [
            'approach_code', 'table_code', '???', 'isubcase',
            '???', '???', '???', 'random_code',
            'format_code', 'num_wide', '???', '???',
            'acoustic_flag', '???', '???', '???',
            '???', '???', '???', '???',
            '???', '???', 'thermal', '???',
            '???', 'Title', 'subtitle', 'label']

        ## random code
        self.random_code = self.add_data_parameter(data, 'random_code', b'i', 8, False)

        ## format code
        self.format_code = self.add_data_parameter(data, 'format_code', b'i', 9, False)

        ## number of words per entry in record
        self.num_wide = self.add_data_parameter(data, 'num_wide', b'i', 10, False)

        ## acoustic pressure flag
        self.acoustic_flag = self.add_data_parameter(data, 'acoustic_flag', b'i', 13, False)

        ## thermal flag; 1 for heat transfer, 0 otherwise
        self.thermal = self.add_data_parameter(data, 'thermal', b'i', 23, False)

        if self.analysis_code == 1:   # statics / displacement / heat flux
            # load set number
            self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5, False)
            self.data_names = self.apply_data_code_value('data_names', ['lsdvmn'])
            self.setNullNonlinearFactor()
        elif self.analysis_code == 2:  # real eigenvalues
            # mode number
            self.mode = self.add_data_parameter(data, 'mode', b'i', 5)
            # eigenvalue
            self.eign = self.add_data_parameter(data, 'eign', b'f', 6, False)
            # mode or cycle .. todo:: confused on the type - F1???
            # float - C:\MSC.Software\simcenter_nastran_2019.2\tpl_post1\mftank.op2
            #self.mode_cycle = self.add_data_parameter(data, 'mode_cycle', b'i', 7, False)  # nope...
            self.mode_cycle = self.add_data_parameter(data, 'mode_cycle', b'f', 7, False) # radians
            self.update_mode_cycle('mode_cycle')
            self.data_names = self.apply_data_code_value('data_names', ['mode', 'eign', 'mode_cycle'])
        #elif self.analysis_code == 3: # differential stiffness
            #self.lsdvmn = self.get_values(data, b'i', 5) ## load set number
            #self.data_code['lsdvmn'] = self.lsdvmn
        #elif self.analysis_code == 4: # differential stiffness
            #self.lsdvmn = self.get_values(data, b'i', 5) ## load set number
        elif self.analysis_code == 5:   # frequency
            # frequency
            self.freq = self.add_data_parameter(data, 'freq', b'f', 5)
            self.data_names = self.apply_data_code_value('data_names', ['freq'])
        elif self.analysis_code == 6:  # transient
            # time step
            self.dt = self.add_data_parameter(data, 'dt', b'f', 5)
            self.data_names = self.apply_data_code_value('data_names', ['dt'])
        elif self.analysis_code == 7:  # pre-buckling
            # load set number
            self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            self.data_names = self.apply_data_code_value('data_names', ['lsdvmn'])
        elif self.analysis_code == 8:  # post-buckling
            # load set number
            self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            # real eigenvalue
            self.eigr = self.add_data_parameter(data, 'eigr', b'f', 6, False)
            self.data_names = self.apply_data_code_value('data_names', ['lsdvmn', 'eigr'])
        elif self.analysis_code == 9:  # complex eigenvalues
            # mode number
            self.mode = self.add_data_parameter(data, 'mode', b'i', 5)
            # real eigenvalue
            self.eigr = self.add_data_parameter(data, 'eigr', b'f', 6, False)
            # imaginary eigenvalue
            self.eigi = self.add_data_parameter(data, 'eigi', b'f', 7, False)
            self.data_names = self.apply_data_code_value('data_names', ['mode', 'eigr', 'eigi'])
        elif self.analysis_code == 10:  # nonlinear statics
            # load step
            self.lftsfq = self.add_data_parameter(data, 'lftsfq', b'f', 5)
            self.data_names = self.apply_data_code_value('data_names', ['lftsfq'])
        elif self.analysis_code == 11:  # old geometric nonlinear statics
            # load set number
            self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            self.data_names = self.apply_data_code_value('data_names', ['lsdvmn'])
        elif self.analysis_code == 12:  # contran ? (may appear as aCode=6)  --> straight from DMAP...grrr...
            # load set number
            self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            self.data_names = self.apply_data_code_value('data_names', ['lsdvmn'])
        else:  # pragma: no cover
            msg = f'invalid analysis_code...analysis_code={self.analysis_code}\ndata={self.data_code}'
            raise RuntimeError(msg)

        #print self.code_information()
        self._fix_oug_format_code()
        self._parse_thermal_code()
        if self.is_debug_file:
            self.binary_debug.write('  approach_code  = %r\n' % self.approach_code)
            self.binary_debug.write('  tCode          = %r\n' % self.tCode)
            self.binary_debug.write('  isubcase       = %r\n' % self.isubcase)
        self._read_title(data)
        self._write_debug_bits()
        self._correct_eigenvalue()

    def _correct_eigenvalue(self):
        """Nastran 95 gets the frequency wrong"""
        if self._nastran_format == 'nasa95' and self.analysis_code == 2:  # real eigenvalues
            #print(self.mode, self.eign, self.mode_cycle)
            # sqrt(lambda) = omega = 2*pi*f
            freq = (self.eign) ** 0.5 / (2 * np.pi)
            self.mode_cycle = freq
            self.data_code['mode_cycle'] = freq

    def _read_oug2_3(self, data: bytes, ndata: int):
        """reads the SORT2 version of table 4 (the data table)"""
        #self._set_times_dtype()
        #return self._read_oug1_3(data)
        self.nonlinear_factor = np.nan

        self.is_table_1 = False
        self.is_table_2 = True
        unused_three = self.parse_approach_code(data)
        self.words = [
            'approach_code', 'table_code', '???', 'isubcase',
            '???', '???', '???', 'random_code',
            'format_code', 'num_wide', '???', '???',
            'acoustic_flag', '???', '???', '???',
            '???', '???', '???', '???',
            '???', '???', 'thermal', '???',
            '???', 'Title', 'subtitle', 'label']

        ## random code
        self.random_code = self.add_data_parameter(data, 'random_code', b'i', 8, False)

        ## format code
        self.format_code = self.add_data_parameter(data, 'format_code', b'i', 9, False)

        ## number of words per entry in record
        self.num_wide = self.add_data_parameter(data, 'num_wide', b'i', 10, False)

        ## acoustic pressure flag
        self.acoustic_flag = self.add_data_parameter(data, 'acoustic_flag', b'i', 13, False)

        ## thermal flag; 1 for heat transfer, 0 otherwise
        self.thermal = self.add_data_parameter(data, 'thermal', b'i', 23, False)

        self.node_id = self.add_data_parameter(data, 'node_id', b'i', 5, fix_device_code=True)
        #if self.analysis_code == 1:  # statics / displacement / heat flux
            ## load set number
            #self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5, False)
            #self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            #self.setNullNonlinearFactor()

        if self.analysis_code == 1:  # static...because reasons.
            self._analysis_code_fmt = b'f'
            self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            self.apply_data_code_value('analysis_method', 'N/A')
        elif self.analysis_code == 2:  # real eigenvalues
            ## mode number
            #self.mode = self.add_data_parameter(data, 'mode', b'i', 5)
            self._analysis_code_fmt = b'i'
            # real eigenvalue
            self.eigr = self.add_data_parameter(data, 'eigr', b'f', 6, False)
            ## mode or cycle .. todo:: confused on the type - F1???
            # float - C:\MSC.Software\simcenter_nastran_2019.2\tpl_post1\mftank.op2
             # mode or cycle .. todo:: confused on the type - F1???
            self.mode_cycle = self.add_data_parameter(data, 'mode_cycle', b'i', 7, False)
            #self.mode_cycle = self.add_data_parameter(data, 'mode_cycle', b'f', 7, False)
            self.data_names = self.apply_data_code_value('data_names', ['node_id', 'eigr', 'mode_cycle'])
            self.apply_data_code_value('analysis_method', 'mode')
        #elif self.analysis_code == 3: # differential stiffness
            #self.lsdvmn = self.get_values(data, b'i', 5) ## load set number
            #self.data_code['lsdvmn'] = self.lsdvmn
        #elif self.analysis_code == 4: # differential stiffness
            #self.lsdvmn = self.get_values(data, b'i', 5) ## load set number
        elif self.analysis_code == 5:   # frequency
            # frequency
            #self.freq = self.add_data_parameter(data, 'freq', b'f', 5)
            self._analysis_code_fmt = b'f'
            self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            self.apply_data_code_value('analysis_method', 'freq')
        elif self.analysis_code == 6:  # transient
            ## time step
            #self.dt = self.add_data_parameter(data, 'dt', b'f', 5)
            self._analysis_code_fmt = b'f'
            self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            self.apply_data_code_value('analysis_method', 'dt')
        elif self.analysis_code == 7:  # pre-buckling
            ## load set number
            #self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            self._analysis_code_fmt = b'i'
            self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            self.apply_data_code_value('analysis_method', 'lsdvmn')
        elif self.analysis_code == 8:  # post-buckling
            ## load set number
            #self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            self._analysis_code_fmt = b'f'
            ## real eigenvalue
            self.eigr = self.add_data_parameter(data, 'eigr', b'f', 6, False)
            self.data_names = self.apply_data_code_value('data_names', ['node_id', 'eigr'])
            self.apply_data_code_value('analysis_method', 'eigr')
        elif self.analysis_code == 9:  # complex eigenvalues
            ## mode number
            #self.mode = self.add_data_parameter(data, 'mode', b'i', 5)
            self._analysis_code_fmt = b'i'
            ## real eigenvalue
            self.eigr = self.add_data_parameter(data, 'eigr', b'f', 6, False)
            ## imaginary eigenvalue
            self.eigi = self.add_data_parameter(data, 'eigi', b'f', 7, False)
            self.data_names = self.apply_data_code_value('data_names', ['node_id', 'eigr', 'eigi'])
            self.apply_data_code_value('analysis_method', 'mode')
        elif self.analysis_code == 10:  # nonlinear statics
            ## load step
            #self.lftsfq = self.add_data_parameter(data, 'lftsfq', b'f', 5)
            self._analysis_code_fmt = b'f'
            self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            self.apply_data_code_value('analysis_method', 'lftsfq')
        elif self.analysis_code == 11:  # old geometric nonlinear statics
            ## load set number
            #self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            self.data_names = self.apply_data_code_value('data_names', ['node_id'])
        elif self.analysis_code == 12:  # contran ? (may appear as aCode=6)  --> straight from DMAP...grrr...
            ## load set number
            #self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            self.apply_data_code_value('analysis_method', 'lsdvmn')
        else:
            msg = 'invalid analysis_code...analysis_code=%s' % self.analysis_code
            raise RuntimeError(msg)

        self._fix_oug_format_code()
        self._parse_thermal_code()
        if self.is_debug_file:
            self.binary_debug.write('  %-14s = %r %s\n' % ('approach_code', self.approach_code,
                                                           self.approach_code_str(self.approach_code)))
            self.binary_debug.write('  %-14s = %r\n' % ('tCode', self.tCode))
            self.binary_debug.write('  %-14s = %r\n' % ('isubcase', self.isubcase))
        self._read_title(data)
        self._write_debug_bits()
        assert isinstance(self.nonlinear_factor, integer_types), self.nonlinear_factor

    def _read_ougpc1_3(self, data: bytes, ndata: int):
        """reads table 3 (the header table)"""
        self.to_nx(f' because table_name={self.table_name} was found')
        #self._set_times_dtype()
        self.nonlinear_factor = np.nan
        self.is_table_1 = True
        self.is_table_2 = False
        unused_three = self.parse_approach_code(data)
        self.words = [
            'approach_code', 'table_code', '???', 'isubcase',
            '???', '???', '???', '???',
            'format_code', 'num_wide', '???', '???',
            '???', '???', '???', '???',
            '???', '???', '???', '???',
            '???', '???', 'thermal', '???',
            '???', 'Title', 'subtitle', 'label']

        ## pcode
        # Panel contribution code: +/-1=abs, +/-2=norm

        ## data_type
        #Acoustic dof code (10*grid ID + direction)
        #Direction has the following values:
        #=0, Pressure
        #=1, X-displacement
        #=2, Y-displacement
        #=3, Z-displacement
        #=4, RX-displacement
        #=5, RY-displacement
        #=6, RZ-displacement
        self.dcode = self.add_data_parameter(data, 'dcode', b'i', 5, False)

        ## Panel name (0 for TOTAL)
        panel_name1 = self.add_data_parameter(data, 'data_type', b'4s', 6, False,
                                              add_to_dict=False)
        panel_name2 = self.add_data_parameter(data, 'panel_name', b'4s', 7, False,
                                              add_to_dict=False)
        self.panel_name = panel_name1 + panel_name2
        self.data_code['panel_name'] = self.panel_name

        ## data_type
        ## (1=pressure, 2=first derivative, 3=second derivative)
        self.data_type = self.add_data_parameter(data, 'data_type', b'i', 8, False)

        ## format code
        self.format_code = self.add_data_parameter(data, 'format_code', b'i', 9, False)

        ## number of words per entry in record
        self.num_wide = self.add_data_parameter(data, 'num_wide', b'i', 10, False)


        # 1 ACODE(C) I Device code + 10*Approach Code
        # 2 TCODE(C) I Table Code
        # 3 PCODE I Panel contribution code: +/-1=abs, +/-2=norm
        # 4 SUBCASE I Subcase number
        # 5 DCODE I Acoustic dof code (10*grid ID + direction)
        # Direction has the following values:
        # =0, Pressure
        # =1, X-displacement
        # =2, Y-displacement
        # =3, Z-displacement
        # =4, RX-displacement
        # =5, RY-displacement
        # =6, RZ-displacement
        # TCODE,1=01 Sort 1
        #   ACODE,4=05 Frequency
        #   6 FREQ RS Frequency (Hz)
        #   End ACODE,4
        # TCODE,1=02 Sort 2
        # 6 PNAME(2) CHAR4 Panel name (0 for TOTAL)
        # End TCODE,1
        # 8 DATTYP I Data Type (1=pressure, 2=first derivative, 3=second derivative)
        if self.analysis_code == 1 and 0:   # statics / displacement / heat flux
            # load set number
            self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5, False)
            self.data_names = self.apply_data_code_value('data_names', ['lsdvmn'])
            self.setNullNonlinearFactor()
        #elif self.analysis_code == 2:  # real eigenvalues
            ## mode number
            #self.mode = self.add_data_parameter(data, 'mode', b'i', 5)
            ## eigenvalue
            #self.eign = self.add_data_parameter(data, 'eign', b'f', 6, False)
            ## mode or cycle .. todo:: confused on the type - F1???
            ## float - C:\MSC.Software\simcenter_nastran_2019.2\tpl_post1\mftank.op2
            ##self.mode_cycle = self.add_data_parameter(data, 'mode_cycle', b'i', 7, False)  # nope...
            #self.mode_cycle = self.add_data_parameter(data, 'mode_cycle', b'f', 7, False) # radians
            #self.update_mode_cycle('mode_cycle')
            #self.data_names = self.apply_data_code_value('data_names', ['mode', 'eign', 'mode_cycle'])
        #elif self.analysis_code == 3: # differential stiffness
            #self.lsdvmn = self.get_values(data, b'i', 5) ## load set number
            #self.data_code['lsdvmn'] = self.lsdvmn
        #elif self.analysis_code == 4: # differential stiffness
            #self.lsdvmn = self.get_values(data, b'i', 5) ## load set number
        elif self.analysis_code == 5:   # frequency
            # frequency
            self.freq = self.add_data_parameter(data, 'freq', b'i', 5)
            self.data_names = self.apply_data_code_value('data_names', ['freq'])
        #elif self.analysis_code == 6:  # transient
            ## time step
            #self.dt = self.add_data_parameter(data, 'dt', b'f', 5)
            #self.data_names = self.apply_data_code_value('data_names', ['dt'])
        #elif self.analysis_code == 7:  # pre-buckling
            ## load set number
            #self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            #self.data_names = self.apply_data_code_value('data_names', ['lsdvmn'])
        #elif self.analysis_code == 8:  # post-buckling
            ## load set number
            #self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            ## real eigenvalue
            #self.eigr = self.add_data_parameter(data, 'eigr', b'f', 6, False)
            #self.data_names = self.apply_data_code_value('data_names', ['lsdvmn', 'eigr'])
        #elif self.analysis_code == 9:  # complex eigenvalues
            ## mode number
            #self.mode = self.add_data_parameter(data, 'mode', b'i', 5)
            ## real eigenvalue
            #self.eigr = self.add_data_parameter(data, 'eigr', b'f', 6, False)
            ## imaginary eigenvalue
            #self.eigi = self.add_data_parameter(data, 'eigi', b'f', 7, False)
            #self.data_names = self.apply_data_code_value('data_names', ['mode', 'eigr', 'eigi'])
        #elif self.analysis_code == 10:  # nonlinear statics
            ## load step
            #self.lftsfq = self.add_data_parameter(data, 'lftsfq', b'f', 5)
            #self.data_names = self.apply_data_code_value('data_names', ['lftsfq'])
        #elif self.analysis_code == 11:  # old geometric nonlinear statics
            ## load set number
            #self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            #self.data_names = self.apply_data_code_value('data_names', ['lsdvmn'])
        #elif self.analysis_code == 12:  # contran ? (may appear as aCode=6)  --> straight from DMAP...grrr...
            ## load set number
            #self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            #self.data_names = self.apply_data_code_value('data_names', ['lsdvmn'])
        else:  # pragma: no cover
            msg = f'invalid analysis_code...analysis_code={self.analysis_code}\ndata={self.data_code}'
            raise RuntimeError(msg)

        #print self.code_information()
        self._fix_oug_format_code()
        if self.is_debug_file:
            self.binary_debug.write('  approach_code  = %r\n' % self.approach_code)
            self.binary_debug.write('  tCode          = %r\n' % self.tCode)
            self.binary_debug.write('  isubcase       = %r\n' % self.isubcase)
        self._read_title(data)
        self._write_debug_bits()
        self.warn_skip_table()

    def warn_skip_table(self):
        if self._table4_count == 0:
            self.log.warning(f'skipping {self.table_name}')
            self._table4_count += 1

    def _read_ougpc2_3(self, data: bytes, ndata: int):
        """reads the SORT2 version of table 4 (the data table)"""
        #self._set_times_dtype()
        self.nonlinear_factor = np.nan

        self.is_table_1 = False
        self.is_table_2 = True
        unused_three = self.parse_approach_code(data)
        self.words = [
            'approach_code', 'table_code', '???', 'isubcase',
            '???', '???', '???', '???',
            'format_code', 'num_wide', '???', '???',
            '???', '???', '???', '???',
            '???', '???', '???', '???',
            '???', '???', '???', '???',
            '???', 'Title', 'subtitle', 'label']

        ## data_type
        ## (1=pressure, 2=first derivative, 3=second derivative)
        self.data_type = self.add_data_parameter(data, 'data_type', b'i', 8, False)

        ## format code
        self.format_code = self.add_data_parameter(data, 'format_code', b'i', 9, False)

        ## number of words per entry in record
        self.num_wide = self.add_data_parameter(data, 'num_wide', b'i', 10, False)

        self.node_id = self.add_data_parameter(data, 'node_id', b'i', 5, fix_device_code=True)
        #if self.analysis_code == 1:  # statics / displacement / heat flux
            ## load set number
            #self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5, False)
            #self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            #self.setNullNonlinearFactor()

        #if self.analysis_code == 1:  # static...because reasons.
            #self._analysis_code_fmt = b'f'
            #self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            #self.apply_data_code_value('analysis_method', 'N/A')
        #elif self.analysis_code == 2:  # real eigenvalues
            ### mode number
            ##self.mode = self.add_data_parameter(data, 'mode', b'i', 5)
            #self._analysis_code_fmt = b'i'
            ## real eigenvalue
            #self.eigr = self.add_data_parameter(data, 'eigr', b'f', 6, False)
            ### mode or cycle .. todo:: confused on the type - F1???
            ## float - C:\MSC.Software\simcenter_nastran_2019.2\tpl_post1\mftank.op2
             ## mode or cycle .. todo:: confused on the type - F1???
            #self.mode_cycle = self.add_data_parameter(data, 'mode_cycle', b'i', 7, False)
            ##self.mode_cycle = self.add_data_parameter(data, 'mode_cycle', b'f', 7, False)
            #self.data_names = self.apply_data_code_value('data_names', ['node_id', 'eigr', 'mode_cycle'])
            #self.apply_data_code_value('analysis_method', 'mode')
        #elif self.analysis_code == 3: # differential stiffness
            #self.lsdvmn = self.get_values(data, b'i', 5) ## load set number
            #self.data_code['lsdvmn'] = self.lsdvmn
        #elif self.analysis_code == 4: # differential stiffness
            #self.lsdvmn = self.get_values(data, b'i', 5) ## load set number

        if self.analysis_code == 5:   # frequency
            # frequency
            ## Panel name (0 for TOTAL)
            panel_name1 = self.add_data_parameter(data, 'panel_name1', b'4s', 6, False,
                                                  add_to_dict=False)
            panel_name2 = self.add_data_parameter(data, 'panel_name2', b'4s', 7, False,
                                                  add_to_dict=False)
            self.panel_name = panel_name1 + panel_name2
            self.data_code['panel_name'] = self.panel_name
            #print(self.panel_name)


            #self.freq = self.add_data_parameter(data, 'freq', b'f', 5)
            self._analysis_code_fmt = b'f'
            self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            self.apply_data_code_value('analysis_method', 'freq')
        #elif self.analysis_code == 6:  # transient
            ### time step
            ##self.dt = self.add_data_parameter(data, 'dt', b'f', 5)
            #self._analysis_code_fmt = b'f'
            #self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            #self.apply_data_code_value('analysis_method', 'dt')
        #elif self.analysis_code == 7:  # pre-buckling
            ### load set number
            ##self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            #self._analysis_code_fmt = b'i'
            #self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            #self.apply_data_code_value('analysis_method', 'lsdvmn')
        #elif self.analysis_code == 8:  # post-buckling
            ### load set number
            ##self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            #self._analysis_code_fmt = b'f'
            ### real eigenvalue
            #self.eigr = self.add_data_parameter(data, 'eigr', b'f', 6, False)
            #self.data_names = self.apply_data_code_value('data_names', ['node_id', 'eigr'])
            #self.apply_data_code_value('analysis_method', 'eigr')
        #elif self.analysis_code == 9:  # complex eigenvalues
            ### mode number
            ##self.mode = self.add_data_parameter(data, 'mode', b'i', 5)
            #self._analysis_code_fmt = b'i'
            ### real eigenvalue
            #self.eigr = self.add_data_parameter(data, 'eigr', b'f', 6, False)
            ### imaginary eigenvalue
            #self.eigi = self.add_data_parameter(data, 'eigi', b'f', 7, False)
            #self.data_names = self.apply_data_code_value('data_names', ['node_id', 'eigr', 'eigi'])
            #self.apply_data_code_value('analysis_method', 'mode')
        #elif self.analysis_code == 10:  # nonlinear statics
            ### load step
            ##self.lftsfq = self.add_data_parameter(data, 'lftsfq', b'f', 5)
            #self._analysis_code_fmt = b'f'
            #self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            #self.apply_data_code_value('analysis_method', 'lftsfq')
        #elif self.analysis_code == 11:  # old geometric nonlinear statics
            ### load set number
            ##self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            #self.data_names = self.apply_data_code_value('data_names', ['node_id'])
        #elif self.analysis_code == 12:  # contran ? (may appear as aCode=6)  --> straight from DMAP...grrr...
            ### load set number
            ##self.lsdvmn = self.add_data_parameter(data, 'lsdvmn', b'i', 5)
            #self.data_names = self.apply_data_code_value('data_names', ['node_id'])
            #self.apply_data_code_value('analysis_method', 'lsdvmn')
        else:
            msg = 'invalid analysis_code...analysis_code=%s' % self.analysis_code
            raise RuntimeError(msg)

        self._fix_oug_format_code()
        if self.is_debug_file:
            self.binary_debug.write('  %-14s = %r %s\n' % ('approach_code', self.approach_code,
                                                           self.approach_code_str(self.approach_code)))
            self.binary_debug.write('  %-14s = %r\n' % ('tCode', self.tCode))
            self.binary_debug.write('  %-14s = %r\n' % ('isubcase', self.isubcase))
        self._read_title(data)
        self._write_debug_bits()
        assert isinstance(self.nonlinear_factor, integer_types), self.nonlinear_factor
        self.warn_skip_table()

    def _read_ougpc_4(self, data: bytes, ndata: int):
        """reads table 4 (the results table)"""
        assert self.table_code == 49, self.code_information()
        if self.read_mode == 1:
            return ndata
        #self.show_data(data)
        #print(f'data_type = {self.data_type}')
        assert self.data_type == 1, self.data_type

        n = 0
        ntotal = 16 * self.factor
        npanels = ndata // ntotal
        assert ndata % ntotal == 0, f'ndata={ndata} ntotal={ntotal} data_type={self.data_type}'
        if self.sort_method == 1:
            struct1 = Struct(self._endian + b'8s ff')
            for i in range(npanels):
                # Panel name (0 for TOTAL)
                edata = data[n:n+ntotal]
                name, real, imag = struct1.unpack(edata)
                #print(name, real, imag)
                n += ntotal
        else:
            struct1 = Struct(self._endian + b'ff ff')
            for i in range(npanels):
                # Panel name (0 for TOTAL)
                edata = data[n:n+ntotal]
                #self.show_data(edata)
                freq, null, real, imag = struct1.unpack(edata)
                #print(freq, null, real, imag)
                n += ntotal
        #strings = (b'0       \xed\xf0{AE\x9d\\APANEL3  O\xa1\x82A\x81\xc5eAPANEL5  a\xeb"\xbe\xbf/\xa4\xbePANEL6  \xda\xe2\xa1\xbe\x0c\x1a!\xbcPANEL2  \xe3~\r\xbetE\xab\xbdPANEL1  ep\x1a\xbd\x05@\xb8\xbd',)
        #ints    = (538976304, 538976288, 1098641645, 1096588613, 1162756432, 538981196, 1099080015, 1097188737, 1162756432, 538981708, -1105007775, -1096536129, 1162756432, 538981964, -1096686886, -1138681332, 1162756432, 538980940, -1106411805, -1112849036, 1162756432, 538980684, -1122340763, -1111998459)
        #floats  = (1.3563177106455426e-19, 1.3563156426940112e-19, 15.746319770812988, 13.788395881652832, 3300.08203125, 1.3569499868262628e-19, 16.328763961791992, 14.360718727111816, 3300.08203125, 1.357016161275267e-19, -0.15910102427005768, -0.3206767737865448, 3300.08203125, 1.3570492484997691e-19, -0.316183865070343, -0.009832870215177536, 3300.08203125, 1.3569168996017607e-19, -0.13817934691905975, -0.0836285650730133, 3300.08203125, 1.3568838123772585e-19, -0.037704844027757645, -0.08996585756540298)
        return ndata

    def _read_ougmc_4(self, data: bytes, ndata: int):
        if self.table_code == 44:   # Displacements
            if self.table_name in [b'OUGMC1', b'OUGMC2']:
                assert self.thermal == 0, self.code_information()
                result_name = 'modal_contribution.displacements'
            else:
                raise NotImplementedError(self.code_information())
        elif self.table_code == 48:   # spc_forces
            if self.table_name in [b'OQGMC1', b'OQGMC2']:
                assert self.thermal == 0, self.code_information()
                result_name = 'modal_contribution.spc_forces'
            else:
                raise NotImplementedError(self.code_information())
        else:
            raise NotImplementedError(self.code_information())

        n = 0
        if self.table_name in [b'OUGMC1', b'OQGMC1']:
            if self.read_mode == 1:
                return ndata
            from struct import Struct
            ntotal = 16 * self.factor  # 4*4
            nnodes = ndata // ntotal
            fmt = mapfmt(self._endian + b'i 3f', self.size)
            struct1 = Struct(fmt)
            for inode in range(nnodes):
                edata = data[n:n+ntotal]
                out = struct1.unpack(edata)
                #print(out)
                n += ntotal
        else:
            raise NotImplementedError(self.code_information())

        self.warn_skip_table()
        return n

    def _read_oug_4(self, data: bytes, ndata: int):
        """reads the SORT1 version of table 4 (the data table)"""
        table_name_bytes = self.table_name
        if self.table_code == 1:   # Displacements
            if table_name_bytes in [b'OUGV1', b'OUGV2',
                                    b'OUG1',
                                    b'BOUGV1',
                                    b'OUPV1', b'OUG1F']:
                # OUG1F - acoustic displacements?
                #msg = f'table_name={self.table_name} table_code={self.table_code}'
                #raise AssertionError(msg)
                n = self._read_oug_displacement(data, ndata, is_cid=False)
            elif table_name_bytes in [b'ROUGV1', b'ROUGV2', b'TOUGV1',
                                      b'OUGF1', b'OUGF2',
                                      b'BOUGF1', ]:
                self.to_nx(f' because table_name={self.table_name} was found')
                n = self._read_oug_displacement(data, ndata, is_cid=False)
            elif table_name_bytes == b'OUGV1PAT':
                n = self._read_oug_displacement(data, ndata, is_cid=True)
            elif table_name_bytes == b'OAG1':
                n = self._read_oug_acceleration(data, ndata)
            elif table_name_bytes == b'OCRUG':
                n = self._read_oug_displacement(data, ndata, is_cid=False)
            else:
                raise NotImplementedError(self.code_information())
        elif self.table_code == 7:
            n = self._read_oug_eigenvector(data, ndata)
        elif self.table_code == 10:
            n = self._read_oug_velocity(data, ndata)
        elif self.table_code == 11:
            n = self._read_oug_acceleration(data, ndata)

        elif self.table_code == 14:  # eigenvector (solution set)
            assert table_name_bytes in [b'OPHSA'], self.table_name
            self.to_nx(f' because table_name={self.table_name} was found')
            n = self._read_oug_eigenvector(data, ndata)
        elif self.table_code == 15:  # displacement (solution set)
            assert table_name_bytes in [b'OUXY1', b'OUXY2'], self.table_name
            self.to_nx(f' because table_name={self.table_name} was found')
            n = self._read_oug_displacement(data, ndata, is_cid=False)
        elif self.table_code == 16:  # velocity (solution set)
            assert table_name_bytes in [b'OUXY1', b'OUXY2'], self.table_name
            self.to_nx(f' because table_name={self.table_name} was found')
            n = self._read_oug_velocity(data, ndata)
        elif self.table_code == 17:  # acceleration (solution set)
            assert table_name_bytes in [b'OUXY1', b'OUXY2'], self.table_name
            self.to_nx(f' because table_name={self.table_name} was found')
            n = self._read_oug_acceleration(data, ndata)
        elif self.table_code == 44:   # Displacements
            assert table_name_bytes in [b'OUGMC1', b'OUGMC2'], self.table_name
            self.to_nx(f' because table_name={self.table_name} was found')
            n = self._read_oug_displacement(data, ndata, is_cid=False)
        else:
            raise NotImplementedError(self.code_information())
        return n

    #def _read_eigenvector_displacement_solution_set(self, data: bytes, ndata: int):
        #"""
        #table_code = 14
        #"""
        #raise NotImplementedError()

    #def _read_displacement_solution_set(self, data: bytes, ndata: int):
        #"""
        #table_code = 15
        #"""
        #raise NotImplementedError()

    #def _read_velocity_solution_set(self, data: bytes, ndata: int):
        #"""
        #table_code = 16
        #"""
        #raise NotImplementedError()

    #def _read_acceleration_solution_set(self, data: bytes, ndata: int):
        #"""
        #table_code = 17
        #"""
        #raise NotImplementedError()

    def _setup_op2_subcase(self, word: str) -> None:
        """
        Parameters
        ----------
        word : str
            displacement
            FLUX
        """
        if self.read_mode == 1:
            if self.isubcase not in self.case_control_deck.subcases:
                self.subcase = self.case_control_deck.create_new_subcase(self.isubcase)
            else:
                self.subcase = self.case_control_deck.subcases[self.isubcase]
            self.subcase.add_op2_data(self.data_code, word, self.log)

    def _read_oug_displacement(self, data, ndata, is_cid):
        """
        Table     Description
        -----     -----------
        OUG1      displacements in the global? frame
        OUGV1/2   displacements in the global frame
        OUGV1PAT  displacements in the global? frame
        BOUGV1    displacments in the basic frame
        ROUGV1/2  relative displacments in the global frame
        OUPV1     ???
        OUXY1/2   eigenvectors in the basic frame
        TOUGV1/2  temperature
        OCRUG     ???
        OUG1F     acoustic displacements
        OUGF1     acoustic displacements

        """
        self._setup_op2_subcase('displacement')

        if self.table_name in [b'ROUGV1', b'ROUGV2']:
            assert self.thermal in [0], self.code_information()
            result_name = 'displacements_ROUGV1'

        elif self.table_name in [b'OUG1', b'OUGV1', b'OUGV2', b'OUGV1PAT', b'BOUGV1']:
            # OUG1F - acoustic displacements
            assert self.thermal in [0, 1], self.code_information()
            # NX THERMAL
            # 1: heat transfer
            # 2: axisymmetric Fourier
            # 3: for cyclic symmetric;
            # 0: otherwise
            if self.thermal == 0:
                result_name = 'displacements'
            elif self.thermal == 1:
                result_name = 'temperatures'
            else:  # pragma: no cover
                msg = 'displacements; table_name=%s' % self.table_name
                raise NotImplementedError(msg)
        elif self.table_name in [b'OUXY1', b'OUXY2']:
            assert self.thermal == 0, self.code_information()
            result_name = 'solution_set.displacements'
        elif self.table_name == b'OUPV1':
            #result_name = 'temperatures'
            result_name0 = 'displacements' # is this right?
            prefix, postfix = _oug_get_prefix_postfix(self.thermal)
            result_name = prefix + result_name0 + postfix

        elif self.table_name in [b'TOUGV1', b'TOUGV2']:
            result_name = 'temperatures'
            assert self.thermal == 1, self.code_information()
        elif self.table_name in [b'OCRUG']:
            result_name = 'displacements'
            assert self.thermal == 0, self.code_information()
        elif self.table_name in [b'OUG1F', b'OUGF1', b'OUGF2', b'BOUGF1']:
            result_name = 'acoustic.displacements'  # acoustic displacements
            assert self.thermal == 0, self.code_information()
        else:  # pragma: no cover
            msg = 'displacements; table_name=%s' % self.table_name
            raise NotImplementedError(msg)

        if self._results.is_not_saved(result_name):
            return ndata
        self._results._found_result(result_name)
        storage_obj = self.get_result(result_name)
        if self.thermal == 0:
            #result_name = 'displacements'
            #storage_obj = self.displacements
            assert self.table_name in [b'BOUGV1', b'ROUGV1', b'ROUGV2', b'OUGV1', b'OUGV2',
                                       b'OUG1', b'OCRUG', b'OUGV1PAT', b'OUXY1', b'OUXY2',
                                       b'OUG1F',
                                       b'OUGF1', b'OUGF2',
                                       b'BOUGF1', ], self.table_name
            n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                            RealDisplacementArray, ComplexDisplacementArray,
                                            'node', random_code=self.random_code,
                                            is_cid=is_cid)
        elif self.thermal == 1:
            #result_name = 'temperatures'
            #storage_obj = self.temperatures
            assert self.table_name in [b'OUGV1', b'OUGV2', b'TOUGV1', b'TOUGV2', b'OUG1'], self.table_name
            n = self._read_scalar_table_vectorized(data, ndata, result_name, storage_obj,
                                                   RealTemperatureArray, None,
                                                   'node', random_code=self.random_code,
                                                   is_cid=is_cid)
        elif self.thermal == 2:
            assert self.table_name in [b'OUPV1'], self.table_name
            n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                            RealDisplacementArray, ComplexDisplacementArray,
                                            'node', random_code=self.random_code)
        elif self.thermal == 4:
            # F:\work\pyNastran\examples\Dropbox\move_tpl\ms103.op2
            assert self.table_name in [b'OUPV1'], self.table_name
            n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                            RealDisplacementArray, ComplexDisplacementArray,
                                            'node', random_code=self.random_code)
        elif self.thermal == 8:  # 4 ?
            assert self.table_name in [b'OUPV1'], self.table_name
            n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                            RealDisplacementArray, ComplexDisplacementArray,
                                            'node', random_code=self.random_code)
            #return self._not_implemented_or_skip(data, ndata, msg='thermal=4')
        else:
            raise RuntimeError(self.code_information())
            #n = self._not_implemented_or_skip(data, ndata, 'bad thermal=%r table' % self.thermal)
        #else:
            #raise NotImplementedError(self.thermal)
        return n

    def _read_oug_velocity(self, data: bytes, ndata: int):
        """
        table_code = 10
        """
        self._setup_op2_subcase('velocity')
        if self.table_name in [b'OUGV1', b'OUGV2', b'BOUGV1', b'OVG1']:
            assert self.thermal in [0, 1], self.code_information()
            result_name = 'velocities'
        elif self.table_name in [b'OUXY1', b'OUXY2']:
            self.to_nx(f' because table_name={self.table_name} was found')
            assert self.thermal == 0, self.code_information()
            result_name = 'solution_set.velocities'
        elif self.table_name in [b'ROUGV1', b'ROUGV2']:
            self.to_nx(f' because table_name={self.table_name} was found')
            result_name = 'velocities_ROUGV1'
            assert self.thermal == 0, self.code_information()
        elif self.table_name == b'OUPV1':
            result_name0 = 'velocities'
            prefix, postfix = _oug_get_prefix_postfix(self.thermal)
            result_name = prefix + result_name0 + postfix
            assert self.thermal in [2, 4], self.thermal
            else:
                msg = 'velocities; table_name=%s' % self.table_name
                raise NotImplementedError(msg)
        else:  # pragma: no cover
            msg = 'velocities; table_name=%s' % self.table_name
            raise NotImplementedError(msg)

        #result_name = 'velocities'
        #storage_obj = self.velocities
        if self._results.is_not_saved(result_name):
            return ndata
        self._results._found_result(result_name)
        storage_obj = self.get_result(result_name)
        if self.thermal == 0:
            n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                            RealVelocityArray, ComplexVelocityArray,
                                            'node', random_code=self.random_code)
        elif self.thermal == 1:
            n = self._read_scalar_table_vectorized(data, ndata, result_name, storage_obj,
                                                   RealThermalVelocityVectorArray, None,
                                                   'node', random_code=self.random_code)

        elif self.thermal == 2:
            n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                            RealVelocityArray, ComplexVelocityArray,
                                            'node', random_code=self.random_code)
        else:
            raise NotImplementedError(self.thermal)
        return n

    def _read_oug_acceleration(self, data: bytes, ndata: int):
        """
        table_code = 11
        """
        self._setup_op2_subcase('acceleration')

        result_name = None
        if self.table_name in [b'OUGV1', b'OUGV2', b'OAG1', b'BOUGV1']:
            result_name = 'accelerations'
            assert self.thermal == 0, self.code_information()
        elif self.table_name in [b'OUXY1', b'OUXY2']:
            self.to_nx(f' because table_name={self.table_name} was found')
            assert self.thermal == 0, self.code_information()
            result_name = 'solution_set.accelerations'
        elif self.table_name in [b'ROUGV1', b'ROUGV2']:
            self.to_nx(f' because table_name={self.table_name} was found')
            result_name = 'accelerations_ROUGV1'
            assert self.thermal == 0, self.code_information()
        elif self.table_name in [b'OAGPSD1', b'OAGPSD2',
                                 b'OAGRMS1', b'OAGRMS2',
                                 b'OACRM1', b'OAGCRM2',
                                 b'OAGNO1', b'OAGNO2']:
            assert self.thermal == 0, self.code_information()
            pass
        elif self.table_name == b'OUPV1':
            assert self.thermal in [0, 2, 4], self.thermal
            result_name0 = 'accelerations'
            prefix, postfix = _oug_get_prefix_postfix(self.thermal)
            result_name = prefix + result_name0 + postfix
        else:  # pragma: no cover
            msg = 'accelerations; table_name=%s' % self.table_name
            raise NotImplementedError(msg)

        if self.thermal == 0:
            if self.table_name in [b'OUGV1', b'OUGV2', b'ROUGV1', b'ROUGV2', b'OAG1', b'BOUGV1', b'OUXY1', b'OUXY2', b'OUPV1']:
                assert result_name is not None, self.table_name
                if self._results.is_not_saved(result_name):
                    return ndata
                storage_obj = self.get_result(result_name)
                n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                                RealAccelerationArray,
                                                ComplexAccelerationArray,
                                                'node', random_code=self.random_code)
            elif self.table_name in [b'OAGPSD1', b'OAGPSD2']:
                n = self._read_oug_psd(data, ndata)
            elif self.table_name in [b'OAGRMS1', b'OAGRMS2']:
                n = self._read_oug_rms(data, ndata)
            elif self.table_name in [b'OACRM1', b'OAGCRM2']:
                n = self._read_oug_crm(data, ndata)
            elif self.table_name in [b'OAGNO1', b'OAGNO2']:
                n = self._read_oug_no(data, ndata)
            else:
                raise NotImplementedError(self.code_information())
        elif self.thermal == 1:
            result_name = 'accelerations'
            storage_obj = self.accelerations
            if self._results.is_not_saved(result_name):
                return ndata
            self._results._found_result(result_name)
            raise NotImplementedError(self.code_information())
        elif self.thermal == 2:
            result_name = 'abs.accelerations'
            storage_obj = self.get_result(result_name)
            if self._results.is_not_saved(result_name):
                return ndata
            self._results._found_result(result_name)
            n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                            RealAccelerationArray, ComplexAccelerationArray,
                                            'node', random_code=self.random_code)
            #n = self._not_implemented_or_skip(data, ndata, msg='thermal=2')
        elif self.thermal == 4:
            result_name = 'srss.accelerations'
            storage_obj = self.get_result(result_name)
            if self._results.is_not_saved(result_name):
                return ndata
            self._results._found_result(result_name)
            n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                            RealAccelerationArray, ComplexAccelerationArray,
                                            'node', random_code=self.random_code)
            #n = self._not_implemented_or_skip(data, ndata, msg='thermal=4')
        else:
            raise NotImplementedError(self.thermal)
        return n

    def _read_oug_eigenvector(self, data: bytes, ndata: int):
        """
        table_code = 7
        """
        # NX THERMAL
        # 1: heat transfer
        # 2: axisymmetric Fourier
        # 3: for cyclic symmetric;
        # 0: otherwise
        assert self.thermal in [0, 2, 3], self.code_information()
        if self.table_name in [b'OUGV1', b'OUGV2', b'OUG1',
                               b'BOUGV1',
                               b'OPHIG', b'BOPHIG', ]:
            self._setup_op2_subcase('VECTOR')
            result_name = 'eigenvectors'
        elif self.table_name in [b'OUGF1', b'OUGF2',
                                 b'BOUGF1',
                                 b'BOPHIGF']:
            self._setup_op2_subcase('VECTOR')
            result_name = 'eigenvectors_fluid'

        elif self.table_name == b'OPHSA':
            self.to_nx(f' because table_name={self.table_name} was found')
            self._setup_op2_subcase('SVECTOR')
            assert self.thermal == 0, self.code_information()
            result_name = 'solution_set.eigenvectors'

        elif self.table_name == b'RADCONS':
            self.to_nx(f' because table_name={self.table_name} was found')
            self._setup_op2_subcase('VECTOR')
            result_name = 'RADCONS.eigenvectors'
        elif self.table_name == b'RADEFFM':
            self.to_nx(f' because table_name={self.table_name} was found')
            self._setup_op2_subcase('VECTOR')
            result_name = 'RADEFFM.eigenvectors'
        elif self.table_name == b'RADEATC':
            self.to_nx(f' because table_name={self.table_name} was found')
            self._setup_op2_subcase('VECTOR')
            result_name = 'RADEATC.eigenvectors'
        elif self.table_name in [b'ROUGV1', 'ROUGV2']:
            self.to_nx(f' because table_name={self.table_name} was found')
            self._setup_op2_subcase('VECTOR')
            result_name = 'ROUGV1.eigenvectors'
        else:  # pragma: no cover
            msg = 'eigenvectors; table_name=%s' % self.table_name
            raise NotImplementedError(msg)
        assert self.thermal in [0, 2, 3], self.code_information()

        if self._results.is_not_saved(result_name):
            return ndata
        self._results._found_result(result_name)
        storage_obj = self.get_result(result_name)

        # NX THERMAL
        # 1: heat transfer
        # 2: axisymmetric Fourier
        # 3: for cyclic symmetric;
        # 0: otherwise
        if self.thermal in [0, 2, 3]:
            n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                            RealEigenvectorArray, ComplexEigenvectorArray,
                                            'node', random_code=self.random_code)
        elif self.thermal == 1:
            n = self._not_implemented_or_skip(data, ndata, msg='thermal=1')
        else:
            raise NotImplementedError(self.thermal)
        return n

    def _read_oug_psd(self, data: bytes, ndata: int):
        """
        table_code = 601/610/611

        +-----+-------------+---------+
        | Bit |     0       |    1    |
        +-----+-------------+---------+
        |  0  | Not Random  | Random  |
        |  1  | SORT1       | SORT2   |
        |  2  | Real        | Complex |
        +-----+-------------+---------+

          sort_code = 0 -> sort_bits = [0,0,0]  #         sort1, real
          sort_code = 1 -> sort_bits = [0,0,1]  #         sort1, complex
          sort_code = 2 -> sort_bits = [0,1,0]  #         sort2, real
          sort_code = 3 -> sort_bits = [0,1,1]  #         sort2, complex
          sort_code = 4 -> sort_bits = [1,0,0]  # random, sort1, real
          sort_code = 5 -> sort_bits = [1,0,1]  # random, sort1, real
          sort_code = 6 -> sort_bits = [1,1,0]  # random, sort2, real
          sort_code = 7 -> sort_bits = [1,1,1]  # random, sort2, complex
          # random, sort2, complex <- [1, 1, 1]

          sort_bits[0] = 0 -> isSorted=True isRandom=False
          sort_bits[1] = 0 -> is_sort1=True is_sort2=False
          sort_bits[2] = 0 -> isReal=True   isReal/Imaginary=False
        """
        #self.sort_code = 6
        #self.sort_bits = [1, 1, 0]
        #if self.table_code < 50:
        #    self.table_code += 600

        if self.thermal == 0:
            if self.table_code == 1:
                # displacement
                assert self.table_name in [b'OUGPSD1', b'OUGPSD2'], 'self.table_name=%r' % self.table_name
                result_name = 'psd.displacements'
                obj = RealDisplacementArray
            elif self.table_code == 10:
                # velocity
                assert self.table_name in [b'OVGPSD1', b'OVGPSD2'], 'self.table_name=%r' % self.table_name
                result_name = 'psd.velocities'
                obj = RealVelocityArray
            elif self.table_code == 11:
                # acceleration
                assert self.table_name in [b'OAGPSD1', b'OAGPSD2'], 'self.table_name=%r' % self.table_name
                result_name = 'psd.accelerations'
                obj = RealAccelerationArray

            elif self.table_code == 601:
                # displacement
                assert self.table_name in [b'OUGPSD1', b'OUGPSD2'], 'self.table_name=%r' % self.table_name
                result_name = 'psd.displacements'
                obj = RealDisplacementArray
            elif self.table_code == 610:
                # velocity
                assert self.table_name in [b'OUGPSD1', b'OUGPSD2'], 'self.table_name=%r' % self.table_name
                result_name = 'psd.velocities'
                obj = RealVelocityArray
            elif self.table_code == 611:
                # acceleration
                assert self.table_name in [b'OUGPSD1', b'OUGPSD2'], 'self.table_name=%r' % self.table_name
                result_name = 'psd.accelerations'
                obj = RealAccelerationArray
            else:
                n = self._not_implemented_or_skip(data, ndata, self.code_information())
                return n

            if self._results.is_not_saved(result_name):
                return ndata
            self._results._found_result(result_name)

            storage_obj = self.get_result(result_name)
            n = self._read_random_table(data, ndata, result_name, storage_obj,
                                        obj, 'node',
                                        random_code=self.random_code)
        #elif self.thermal == 1:
            #result_name = 'accelerations'
            #storage_obj = self.accelerations
            #if self._results.is_not_saved(result_name):
                #return ndata
            #self._results._found_result(result_name)
            #n = self._read_table(data, ndata, result_name, storage_obj,
                                 #None, None,
                                 #None, None, 'node', random_code=self.random_code)
        #elif self.thermal == 2:
            #result_name = 'acceleration_scaled_response_spectra_abs'
            #storage_obj = self.acceleration_scaled_response_spectra_abs
            #if self._results.is_not_saved(result_name):
                #return ndata
            #self._results._found_result(result_name)
            #n = self._read_table(data, ndata, result_name, storage_obj,
                                 #RealAcceleration, ComplexAcceleration,
                                 #RealAccelerationArray, ComplexAccelerationArray,
                                 #'node', random_code=self.random_code)
            ##n = self._not_implemented_or_skip(data, ndata, msg='thermal=2')
        #elif self.thermal == 4:
            #result_name = 'acceleration_scaled_response_spectra_nrl'
            #storage_obj = self.acceleration_scaled_response_spectra_nrl
            #if self._results.is_not_saved(result_name):
                #return ndata
            #self._results._found_result(result_name)
            #n = self._read_table(data, ndata, result_name, storage_obj,
                                 #RealAcceleration, ComplexAcceleration,
                                 #RealAccelerationArray, ComplexAccelerationArray,
                                 #'node', random_code=self.random_code)
            ##n = self._not_implemented_or_skip(data, ndata, msg='thermal=4')
        else:
            raise NotImplementedError(self.thermal)
        return n

    def _read_oug_rms(self, data: bytes, ndata: int):
        """
        table_code = 801  # /610/611
        """
        #self.sort_code = 6
        #self.sort_bits = [1, 1, 0]
        #if self.table_code < 50:
        #    self.table_code += 800

        if self.thermal == 0:
            if self.table_code == 1:
                # displacement
                assert self.table_name in [b'OUGRMS1', b'OUGRMS2'], 'self.table_name=%r' % self.table_name
                result_name = 'rms.displacements'
                obj = RealDisplacementArray
            elif self.table_code == 10:
                # velocity
                assert self.table_name in [b'OVGRMS1', b'OVGRMS2'], 'self.table_name=%r' % self.table_name
                result_name = 'rms.velocities'
                obj = RealVelocityArray
            elif self.table_code == 11:
                # acceleration
                assert self.table_name in [b'OAGRMS1', b'OAGRMS2'], 'self.table_name=%r' % self.table_name
                result_name = 'rms.accelerations'
                obj = RealAccelerationArray
            elif self.table_code == 801:
                result_name = 'rms.displacements'
                assert self.table_name in [b'OUGRMS1', b'OUGRM2'], 'self.table_name=%r' % self.table_name
                obj = RealDisplacementArray
            elif self.table_code == 810:
                assert self.table_name in [b'OUGRMS1', b'OUGRM2'], 'self.table_name=%r' % self.table_name
                result_name = 'rms.velocities'
                obj = RealVelocityArray
            elif self.table_code == 811:
                assert self.table_name in [b'OUGRMS1', b'OUGRMS2'], 'self.table_name=%r' % self.table_name # , b'OAGRMS1', b'OAGRMS2'
                result_name = 'rms.accelerations'
                obj = RealAccelerationArray
            else:
                n = self._not_implemented_or_skip(data, ndata, self.code_information())
                #raise RuntimeError(self.code_information())
                return n

            if self._results.is_not_saved(result_name):
                return ndata
            self._results._found_result(result_name)

            storage_obj = self.get_result(result_name)
            n = self._read_random_table(data, ndata, result_name, storage_obj,
                                        obj, 'node',
                                        random_code=self.random_code)
            #n = self._read_table_sort1_real(data, ndata, result_name, storage_obj,
                                            #RealDisplacementArray, 'node',
                                            #random_code=self.random_code)
            #n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
                                            #RealDisplacementArray, ComplexDisplacementArray,
                                            #'node')

        #elif self.thermal == 1:
            #result_name = 'accelerations'
            #storage_obj = self.accelerations
            #if self._results.is_not_saved(result_name):
                #return ndata
            #self._results._found_result(result_name)
            #n = self._read_table(data, ndata, result_name, storage_obj,
                                 #None, None,
                                 #None, None, 'node', random_code=self.random_code)
        #elif self.thermal == 2:
            #result_name = 'acceleration_scaled_response_spectra_abs'
            #storage_obj = self.acceleration_scaled_response_spectra_abs
            #if self._results.is_not_saved(result_name):
                #return ndata
            #self._results._found_result(result_name)
            #n = self._read_table(data, ndata, result_name, storage_obj,
                                 #RealAcceleration, ComplexAcceleration,
                                 #RealAccelerationArray, ComplexAccelerationArray,
                                 #'node', random_code=self.random_code)
            ##n = self._not_implemented_or_skip(data, ndata, msg='thermal=2')
        #elif self.thermal == 4:
            #result_name = 'acceleration_scaled_response_spectra_nrl'
            #storage_obj = self.acceleration_scaled_response_spectra_nrl
            #if self._results.is_not_saved(result_name):
                #return ndata
            #self._results._found_result(result_name)
            #n = self._read_table(data, ndata, result_name, storage_obj,
                                 #RealAcceleration, ComplexAcceleration,
                                 #RealAccelerationArray, ComplexAccelerationArray,
                                 #'node', random_code=self.random_code)
            ##n = self._not_implemented_or_skip(data, ndata, msg='thermal=4')
        else:
            raise NotImplementedError(self.thermal)
        return n

    def _read_oug_no(self, data: bytes, ndata: int):
        """
        table_code = 901  # /610/611
        """
        if self.thermal == 0:
            if self.table_code == 1:
                # displacement
                assert self.table_name in [b'OUGNO1', b'OUGNO2'], 'self.table_name=%r' % self.table_name
                result_name = 'no.displacements'
                obj = RealDisplacementArray
            elif self.table_code == 10:
                # velocity
                assert self.table_name in [b'OVGNO1', b'OVGNO2'], 'self.table_name=%r' % self.table_name
                result_name = 'no.velocities'
                obj = RealVelocityArray
            elif self.table_code == 11:
                # acceleration
                assert self.table_name in [b'OAGNO1', b'OAGNO2'], 'self.table_name=%r' % self.table_name
                result_name = 'no.accelerations'
                obj = RealAccelerationArray

            elif self.table_code == 901:
                assert self.table_name in [b'OUGNO1', b'OUGNO2'], 'self.table_name=%r' % self.table_name
                result_name = 'no.displacements'
                obj = RealDisplacementArray
            elif self.table_code == 910:
                assert self.table_name in [b'OUGNO1', b'OUGNO2'], 'self.table_name=%r' % self.table_name
                result_name = 'no.velocities'
                obj = RealVelocityArray
            elif self.table_code == 911:
                assert self.table_name in [b'OUGNO1', b'OUGNO2', b'OAGNO1', b'OAGNO2'], 'self.table_name=%r' % self.table_name
                result_name = 'no.accelerations'
                obj = RealAccelerationArray
            else:
                n = self._not_implemented_or_skip(data, ndata, self.code_information())
                return n
            if self._results.is_not_saved(result_name):
                return ndata
            self._results._found_result(result_name)

            storage_obj = self.get_result(result_name)
            n = self._read_random_table(data, ndata, result_name, storage_obj,
                                        obj, 'node',
                                        random_code=self.random_code)

        #elif self.thermal == 1:
            #result_name = 'accelerations'
            #storage_obj = self.accelerations
            #if self._results.is_not_saved(result_name):
                #return ndata
            #self._results._found_result(result_name)
            #n = self._read_table(data, ndata, result_name, storage_obj,
                                 #None, None,
                                 #None, None, 'node', random_code=self.random_code)
        #elif self.thermal == 2:
            #result_name = 'acceleration_scaled_response_spectra_abs'
            #storage_obj = self.acceleration_scaled_response_spectra_abs
            #if self._results.is_not_saved(result_name):
                #return ndata
            #self._results._found_result(result_name)
            #n = self._read_table(data, ndata, result_name, storage_obj,
                                 #RealAcceleration, ComplexAcceleration,
                                 #RealAccelerationArray, ComplexAccelerationArray,
                                 #'node', random_code=self.random_code)
            ##n = self._not_implemented_or_skip(data, ndata, msg='thermal=2')
        #elif self.thermal == 4:
            #result_name = 'acceleration_scaled_response_spectra_nrl'
            #storage_obj = self.acceleration_scaled_response_spectra_nrl
            #if self._results.is_not_saved(result_name):
                #return ndata
            #self._results._found_result(result_name)
            #n = self._read_table(data, ndata, result_name, storage_obj,
                                 #RealAcceleration, ComplexAcceleration,
                                 #RealAccelerationArray, ComplexAccelerationArray,
                                 #'node', random_code=self.random_code)
            ##n = self._not_implemented_or_skip(data, ndata, msg='thermal=4')
        else:
            raise NotImplementedError(self.thermal)
        return n

    def _read_oug_ato(self, data: bytes, ndata: int):
        """
        table_code = 901  # /610/611
        """
        if self.thermal == 0:
            if self.table_code == 1:
                result_name = 'ato.displacements'
                obj = RealDisplacementArray
                assert self.table_name in [b'OUGATO1', b'OUGATO2'], 'self.table_name=%r' % self.table_name
            elif self.table_code == 10:
                result_name = 'ato.velocities'
                obj = RealVelocityArray
                assert self.table_name in [b'OVGATO1', b'OVGATO2'], 'self.table_name=%r' % self.table_name
            elif self.table_code == 11:
                result_name = 'ato.accelerations'
                obj = RealAccelerationArray
                assert self.table_name in [b'OAGATO1', b'OAGATO2'], 'self.table_name=%r' % self.table_name
            else:
                n = self._not_implemented_or_skip(data, ndata, self.code_information())
                return n
        else:
            raise NotImplementedError(self.thermal)

        if self._results.is_not_saved(result_name):
            return ndata
        self._results._found_result(result_name)
        storage_obj = self.get_result(result_name)
        n = self._read_random_table(data, ndata, result_name, storage_obj,
                                    obj, 'node',
                                    random_code=self.random_code)
        return n

    def _read_oug_crm(self, data: bytes, ndata: int):
        """
        table_code = 501  # /510/511
        """
        #self.sort_code = 6
        #self.sort_bits = [1, 1, 0]
        #if self.table_code < 50:
        #    self.table_code += 800

        if self.thermal == 0:
            if self.table_code == 1:
                assert self.table_name in [b'OUGCRM1', b'OUGCRM2'], 'self.table_name=%r' % self.table_name
                result_name = 'crm.displacements'
                obj = RealDisplacementArray
            elif self.table_code == 10:
                # velocity
                assert self.table_name in [b'OVGCRM1', b'OVGCRM2'], 'self.table_name=%r' % self.table_name
                result_name = 'crm.velocities'
                obj = RealVelocityArray
            elif self.table_code == 11:
                # acceleration
                assert self.table_name in [b'OAGCRM1', b'OAGCRM2'], 'self.table_name=%r' % self.table_name
                result_name = 'crm.accelerations'
                obj = RealAccelerationArray
            elif self.table_code == 501:
                assert self.table_name in [b'OUGCRM1', b'OUGCRM2'], 'self.table_name=%r' % self.table_name
                result_name = 'crm.displacements'
                obj = RealDisplacementArray
            elif self.table_code == 510:
                # velocity
                assert self.table_name in [b'OUGCRM1', b'OUGCRM2'], 'self.table_name=%r' % self.table_name
                result_name = 'crm.velocities'
                obj = RealVelocityArray
            elif self.table_code == 511:
                # acceleration
                assert self.table_name in [b'OUGCRM1', b'OUGCRM2'], 'self.table_name=%r' % self.table_name
                result_name = 'crm.accelerations'
                obj = RealAccelerationArray
            else:
                n = self._not_implemented_or_skip(data, ndata, self.code_information())
                #raise RuntimeError(self.code_information())
                return n

            if self._results.is_not_saved(result_name):
                return ndata
            self._results._found_result(result_name)

            storage_obj = self.get_result(result_name)
            n = self._read_random_table(data, ndata, result_name, storage_obj,
                                        obj, 'node',
                                        random_code=self.random_code)

                #n = self._read_table_sort1_real(data, ndata, result_name, storage_obj,
                                                #RealDisplacementArray, 'node',
                                                #random_code=self.random_code)
                #n = self._read_table_vectorized(data, ndata, result_name, storage_obj,
        else:
            raise NotImplementedError(self.thermal)
        return n


def _oug_get_prefix_postfix(thermal: int) -> Tuple[str, str]:
    prefix = ''
    postfix = ''
    if thermal == 0:
        pass
    if thermal == 2:
        prefix = 'abs.'
    elif thermal == 4:
        prefix = 'srss.'
    elif thermal == 8:
        prefix = 'nrl.'
    else:  # pragma: no cover
        msg = 'thermal=%s' % thermal
        raise NotImplementedError(msg)

    #assert thermal in [0, 2, 4, 8], self.code_information()
    #if op2.thermal == 0:
        #result_name = 'displacement' # is this right?
    #elif op2.thermal == 2:
        #result_name = 'abs.displacement' # displacement_scaled_response_spectra_abs
    #elif op2.thermal == 4:
        #result_name = 'srss.displacement' # displacement_scaled_response_spectra_srss
    #elif op2.thermal == 8:
        #result_name = 'nrl.displacement'  # displacement_scaled_response_spectra_nrl
    #else:  # pragma: no cover
        #msg = 'displacements; table_name=%s' % op2.table_name
        #raise NotImplementedError(msg)

    return prefix, postfix
