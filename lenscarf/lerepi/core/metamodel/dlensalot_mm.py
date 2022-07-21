#!/usr/bin/env python

"""dlensalot_mm.py: Contains the metamodel of the Dlensalot formalism.
"""
__author__ = "S. Belkner, J. Carron, L. Legrand"

import abc
import attr

import numpy as np


class DLENSALOT_Concept:
    """An abstract element base type for the Dlensalot formalism."""
    __metaclass__ = abc.ABCMeta


    def __str__(self):
        _str = ''
        for k, v in self.__dict__.items():
            _str+="\t{}:\t{}\n".format(k,v)
        return _str


@attr.s
class DLENSALOT_Meta(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        version:
    """
    version = attr.ib(default=-1)


@attr.s
class DLENSALOT_Computing(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        QE_delensing:
    """
    OMP_NUM_THREADS = attr.ib(default=-1)


@attr.s
class DLENSALOT_Job(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        QE_delensing:
    """
    QE_lensrec = attr.ib(default=-1)
    MAP_lensrec = attr.ib(default=-1)
    inspect_result = attr.ib(default=-1)
    map_delensing = attr.ib(default=-1)
    build_OBD = attr.ib(default=-1)


@attr.s
class DLENSALOT_Model(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        data: 
    """
    meta = attr.ib(default=-1)
    job = attr.ib(default=-1)
    analysis = attr.ib(default=-1)
    data  = attr.ib(default=[])
    noisemodel = attr.ib(default=[])
    qerec = attr.ib(default=[])
    itrec = attr.ib(default=-1)
    madel = attr.ib(default=-1)


@attr.s
class DLENSALOT_Analysis(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        DATA_LIBDIR: path to the data
    """
    key = attr.ib(default=np.nan)
    version = attr.ib(default=np.nan)
    simidxs_mf = attr.ib(default=[])
    TEMP_suffix = attr.ib(default=None)
    lens_res = attr.ib(default=np.nan)
    zbounds =  attr.ib(default=(-1,1))
    zbounds_len = attr.ib(default=(-1,1))
    pbounds = attr.ib(default=(-1,1))


@attr.s
class DLENSALOT_Data(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        DATA_LIBDIR: path to the data
    """
    simidxs = attr.ib(default=[])
    class_parameters = attr.ib(default=None)
    package_ = attr.ib(default=None)
    module_ = attr.ib(default=None)
    class_ = attr.ib(default=None)
    data_type = attr.ib(default=None)
    data_field = attr.ib(default=None)
    beam = attr.ib(default=None)
    nside = attr.ib(default=np.nan)
    transferfunction = attr.ib(default=True)


@attr.s
class DLENSALOT_Noisemodel(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        typ:
    """
    lowell_treat = attr.ib(default=None) # OBD, trunc, None
    OBD = attr.ib(default=None)
    lmin_tlm = attr.ib(default=np.nan)
    lmin_elm = attr.ib(default=np.nan)
    lmin_blm = attr.ib(default=np.nan)
    nlev_t = attr.ib(default=[])
    nlev_p = attr.ib(default=[])
    rhits_normalised = attr.ib(default=None)
    mask = attr.ib(default=None)
    ninvjob_geometry = attr.ib(default=None)


@attr.s
class DLENSALOT_Qerec(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        typ:
    """
    simidxs = attr.ib(default=[])
    simidxs_mf = attr.ib(default=[])
    Lmin = attr.ib(default=np.nan)
    ivfs = attr.ib(default=None)
    qlms = attr.ib(default=None)
    cg_tol = attr.ib(default=np.nan)
    ninvjob_qe_geometry = attr.ib(default=None)
    lmax_qlm = attr.ib(default=np.nan)
    mmax_qlm = attr.ib(default=np.nan)
    chain = attr.ib(default=None)
    cl_analysis = attr.ib(default=False)


@attr.s
class DLENSALOT_Itrec(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        typ:
    """
    tasks = attr.ib(default=None)
    simidxs = attr.ib(default=[])
    itmax = attr.ib(default=np.nan)
    filter = attr.ib(default=None)
    cg_tol = attr.ib(default=np.nan)
    lenjob_geometry = attr.ib(default=None)
    lenjob_pbgeometry = attr.ib(default=None)
    iterator_typ = attr.ib(default=None)
    mfvar = attr.ib(default=None)
    soltn_cond = attr.ib(default=None)
    stepper = attr.ib(default=None)
    


@attr.s
class DLENSALOT_Mapdelensing(DLENSALOT_Concept):
    """_summary_

    Args:
        DLENSALOT_Concept (_type_): _description_
    """
    edges = attr.ib(default=-1)
    dlm_mod = attr.ib(default=False)
    iterations = attr.ib(default=-1)
    masks = attr.ib(default=None)
    lmax = attr.ib(default=-1)
    Cl_fid = attr.ib(default=-1)
    libdir_it = attr.ib(default=None)
    binning = attr.ib(default=-1)
    spectrum_calculator = attr.ib(default=None)


@attr.s
class DLENSALOT_Filter(DLENSALOT_Concept):
    """_summary_

    Args:
        DLENSALOT_Concept (_type_): _description_
    """
    lmax_filt = attr.ib(default=np.nan)
    lmax_len = attr.ib(default=np.nan)
    mmax_len = attr.ib(default=np.nan)
    lmax_unl = attr.ib(default=np.nan)
    mmax_unl = attr.ib(default=np.nan)


@attr.s
class DLENSALOT_Chaindescriptor(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        p0: 
    """
    p0 = attr.ib(default=-1)
    p1 = attr.ib(default=-1)
    p2 = attr.ib(default=-1)
    p3 = attr.ib(default=-1)
    p4 = attr.ib(default=-1)
    p5 = attr.ib(default=-1)
    p6 = attr.ib(default=-1)
    p7 = attr.ib(default=-1)


@attr.s
class DLENSALOT_Stepper(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        typ:
    """
    typ = attr.ib(default=-1)
    lmax_qlm = attr.ib(default=-1)
    mmax_qlm = attr.ib(default=-1)
    xa = attr.ib(default=-1)
    xb = attr.ib(default=-1)


class DLENSALOT_OBD(DLENSALOT_Concept):
    """A root model element type of the Dlensalot formalism.

    Attributes:
        BMARG_LIBDIR:
    """
    libdir = attr.ib(default=None)
    rescale = attr.ib(default=None)
    tpl = attr.ib(default=None)
    nlev_dep = attr.ib(default=np.nan)
