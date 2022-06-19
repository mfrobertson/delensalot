import os
from os.path import join as opj
import numpy as np
import healpy as hp

from lerepi.core.metamodel.dlensalot_v2 import *

from plancklens.sims import phas, planck2018_sims


dlensalot_model = DLENSALOT_Model(
    job = DLENSALOT_Job(
        build_OBD = False,
        QE_lensrec = False,
        MAP_lensrec = True,
        Btemplate_per_iteration = True,
        map_delensing = True,
        inspect_result = False,
        OMP_NUM_THREADS = 16
    ),
    analysis = DLENSALOT_Analysis(
        TEMP_suffix = '',
        K = 'p_p',
        V = 'mf07',
        ITMAX = 12,
        nsims_mf = 100,
        zbounds =  ('nmr_relative', np.inf),
        zbounds_len = ('extend', 5.),   
        pbounds = [1.97, 5.71],
        LENSRES = 1.7, # Deflection operations will be performed at this resolution
        Lmin = 4, 
        lmax_filt = 4000,
        lmax_unl = 4000,
        mmax_unl = 4000,
        lmax_ivf = 3000,
        mmax_ivf = 3000,
        lmin_ivf = 10,
        mmin_ivf = 10,
        STANDARD_TRANSFERFUNCTION = True # Change only if exotic transferfunctions is desired
    ),
    data = DLENSALOT_Data(
        IMIN = 0,
        IMAX = 99,
        package_ = 'plancklens',
        module_ = 'sims.maps',
        class_ = 'cmb_maps_nlev',
        class_parameters = {
            'sims_cmb_len': planck2018_sims.cmb_len_ffp10(),
            'cl_transf': hp.gauss_beam(1.0 / 180 / 60 * np.pi, lmax=4096),
            'nlev_t': 0.5/np.sqrt(2),
            'nlev_p': 0.5,
            'nside': 2048,
            'pix_lib_phas': phas.pix_lib_phas(opj(os.environ['HOME'], 'pixphas_nside2048'), 3, (hp.nside2npix(2048),))
        },
        beam = 1.0,
        lmax_transf = 4000,
        nside = 2048
    ),
    noisemodel = DLENSALOT_Noisemodel(
        typ = 'OBD',
        BMARG_LIBDIR = '/global/project/projectdirs/cmbs4/awg/lowellbb/reanalysis/mapphi_intermediate/s08b/',
        BMARG_LCUT = 200,
        BMARG_RESCALE = (0.42/0.350500)**2,
        ninvjob_geometry = 'healpix_geometry',
        lmin_tlm = 30,
        lmin_elm = 30,
        lmin_blm = 30,
        CENTRALNLEV_UKAMIN = 0.42,
        nlev_t = 0.42/np.sqrt(2),
        nlev_p = 0.42,
        nlev_dep = 10000.,
        inf = 1e4,
        mask = ('nlev', np.inf),
        rhits_normalised = ('/global/project/projectdirs/cmbs4/awg/lowellbb/reanalysis/mapphi_intermediate/s08b/masks/08b_rhits_positive_nonan.fits', np.inf),
        tpl = 'template_dense'
    ),
    qerec = DLENSALOT_Qerec(
        FILTER_QE = 'sepTP', # Change only if other than sepTP for QE is desired
        CG_TOL = 1e-3,
        ninvjob_qe_geometry = 'healpix_geometry_qe',
        lmax_qlm = 4000,
        mmax_qlm = 4000,
        QE_LENSING_CL_ANALYSIS = False, # Change only if a full, Planck-like QE lensing power spectrum analysis is desired
        chain = DLENSALOT_Chaindescriptor(
            p0 = 0,
            p1 = ["diag_cl"],
            p2 = None,
            p3 = 2048,
            p4 = np.inf,
            p5 = None,
            p6 = 'tr_cg',
            p7 = 'cache_mem'
        )
    ),
    itrec = DLENSALOT_Itrec(
        FILTER = 'opfilt_ee_wl.alm_filter_ninv_wl',
        TOL = 3,
        lenjob_geometry = 'thin_gauss',
        lenjob_pbgeometry = 'pbdGeometry',
        iterator_typ = 'constmf', # Either pertmf or const_mf
        mfvar = '/global/cscratch1/sd/sebibel/cmbs4/08b_00_OBD_MF100_example/qlms_dd/simMF_k1p_p_135b0ca72339ac4eb092666cd7acb262a8ea2d30.fits',
        soltn_cond = lambda it: True,
        stepper = DLENSALOT_Stepper(
            typ = 'harmonicbump',
            xa = 400,
            xb = 1500
        )
    ),
    madel = DLENSALOT_Mapdelensing(
        edges = 'ioreco',
        ITMAX = [10,12],
        droplist = np.array([]),
        nlevels = [2, 5],
        lmax_cl = 2048,
    )
)
