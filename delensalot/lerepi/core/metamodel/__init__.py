import os
import plancklens
from plancklens import utils
from os.path import join as opj
import numpy as np

from delensalot.lerepi.core.metamodel.dlensalot_mm import DLENSALOT_Model as DLENSALOT_Model_mm, DLENSALOT_Concept, DLENSALOT_Chaindescriptor, DLENSALOT_Stepper

DEFAULT_NotAValue = -123456789
DEFAULT_NotValid = 9876543210123456789

DL_DEFAULT_T = {
    'meta': {
        'version': "0.1"
    },
    'data': {
        'beam': 10,
        'nlev_t': 10,
        'nlev_p': 10,
    }
}

DL_DEFAULT_P = {
    'meta': {
        'version': "0.2"
    },
    'data': {
        'beam': 10,
        'nlev_t': 10,
        'nlev_p': 10,
    }
}

DL_DEFAULT_CMBS4_FS_P = {
    'meta': {
        'version': "0.2"
    },
    'data': {
        'beam': 1.,
        'nlev_t': 1.,
        'nlev_p': 1.,
        'epsilon': 1e-5,
        'nside': 2048,
        'class_parameters': {
            'lmax': 4096,
            'cls_unl': utils.camb_clfile(opj(opj(os.path.dirname(plancklens.__file__), 'data', 'cls'), 'FFP10_wdipole_lenspotentialCls.dat')),
            'lib_dir': opj(os.environ['SCRATCH'], 'sims', 'generic', 'nside2048', 'lmax4096', 'nlevp_sqrt(2)')
        },
        'lmax_transf' : 4500,
        'transferfunction': 'gauss_no_pixwin'
    },
    'analysis': { 
        'key' : 'p_p',
        'version' : 'noMF',
        'simidxs' : np.arange(0,1),
        'TEMP_suffix' : 'mfda_wdefault',
        'Lmin' : 1, 
        'lm_max_ivf' : (4000, 4000),
        'lmin_teb' : (2, 2, 200)
    },
    'qerec':{
        'chain': DLENSALOT_Chaindescriptor(
            p0 = 0,
            p1 = ["diag_cl"],
            p2 = None,
            p3 = 2048,
            p4 = np.inf,
            p5 = None,
            p6 = 'tr_cg',
            p7 = 'cache_mem'
        )
    },
    'itrec': {
        'stepper': DLENSALOT_Stepper(
            typ = 'harmonicbump',
            lmax_qlm = 4000,
            mmax_qlm = 4000,
            a  = 0.5,
            b  = 0.499,
            xa = 400,
            xb = 1500
        )
    }
}



DL_DEFAULT = dict({
    "T": DL_DEFAULT_T,
    "P": DL_DEFAULT_P,
    "default": DL_DEFAULT_P,
    "P_FS_CMBS4": DL_DEFAULT_CMBS4_FS_P,
    })



DL_DEFAULT_TEMPLATE  = {
    'defaults_to': DEFAULT_NotValid,
    'meta': {
        'version': DEFAULT_NotValid,
        },
    'job': {
        'jobs': DEFAULT_NotValid,
    },
    'analysis': {
        'Lmin': DEFAULT_NotValid, 
        'TEMP_suffix': DEFAULT_NotValid, 
        'beam': DEFAULT_NotValid, 
        'cls_len': DEFAULT_NotValid, 
        'cls_unl': DEFAULT_NotValid, 
        'cpp': DEFAULT_NotValid, 
        'key': DEFAULT_NotValid, 
        'lm_max_ivf': DEFAULT_NotValid, 
        'lm_max_len': DEFAULT_NotValid, 
        'lmin_teb': DEFAULT_NotValid, 
        'mask': DEFAULT_NotValid, 
        'pbounds': DEFAULT_NotValid, 
        'simidxs': DEFAULT_NotValid, 
        'simidxs_mf': DEFAULT_NotValid, 
        'version': DEFAULT_NotValid, 
        'zbounds': DEFAULT_NotValid, 
        'zbounds_len': DEFAULT_NotValid, 
    },
    'data': {
        'beam': DEFAULT_NotValid, 
        'class_': DEFAULT_NotValid, 
        'class_parameters': DEFAULT_NotValid, 
        'lmax_transf': DEFAULT_NotValid, 
        'module_': DEFAULT_NotValid, 
        'nlev_p': DEFAULT_NotValid, 
        'nlev_t': DEFAULT_NotValid, 
        'nside': DEFAULT_NotValid, 
        'package_': DEFAULT_NotValid, 
        'transf_dat': DEFAULT_NotValid, 
        'transferfunction': DEFAULT_NotValid,
        'epsilon': DEFAULT_NotValid
    },
    'noisemodel': {
        'OBD': DEFAULT_NotValid, 
        'ninvjob_geometry': DEFAULT_NotValid, 
        'nlev_p': DEFAULT_NotValid, 
        'nlev_t': DEFAULT_NotValid, 
        'rhits_normalised': DEFAULT_NotValid, 
        'sky_coverage': DEFAULT_NotValid, 
        'spectrum_type': DEFAULT_NotValid
    },
    'qerec': {
        'blt_pert': DEFAULT_NotValid, 
        'cg_tol': DEFAULT_NotValid, 
        'chain': DEFAULT_NotValid, 
        'cl_analysis': DEFAULT_NotValid, 
        'filter_directional': DEFAULT_NotValid, 
        'lm_max_qlm': DEFAULT_NotValid, 
        'ninvjob_qe_geometry': DEFAULT_NotValid, 
        'qlm_type': DEFAULT_NotValid, 
        'tasks': DEFAULT_NotValid
    },
    'itrec': {
        'cg_tol': DEFAULT_NotValid, 
        'filter_directional': DEFAULT_NotValid, 
        'iterator_typ': DEFAULT_NotValid, 
        'itmax': DEFAULT_NotValid, 
        'lenjob_geometry': DEFAULT_NotValid, 
        'lenjob_pbgeometry': DEFAULT_NotValid, 
        'lm_max_qlm': DEFAULT_NotValid, 
        'lm_max_unl': DEFAULT_NotValid, 
        'mfvar': DEFAULT_NotValid, 
        'soltn_cond': DEFAULT_NotValid, 
        'stepper': DEFAULT_NotValid, 
        'tasks': DEFAULT_NotValid
    },
    'madel': {
        'Cl_fid': DEFAULT_NotValid, 
        'binning': DEFAULT_NotValid, 
        'dlm_mod': DEFAULT_NotValid, 
        'edges': DEFAULT_NotValid, 
        'iterations': DEFAULT_NotValid, 
        'libdir_it': DEFAULT_NotValid, 
        'lmax': DEFAULT_NotValid, 
        'masks': DEFAULT_NotValid, 
        'spectrum_calculator': DEFAULT_NotValid
    },
    'config': {
        'outdir_plot_rel': DEFAULT_NotValid, 
        'outdir_plot_root': DEFAULT_NotValid
    },
    'computing': {
        'OMP_NUM_THREADS'
    },
    'obd': {
        'beam': DEFAULT_NotValid, 
        'libdir': DEFAULT_NotValid, 
        'lmax': DEFAULT_NotValid, 
        'nlev_dep': DEFAULT_NotValid, 
        'nside': DEFAULT_NotValid, 
        'rescale': DEFAULT_NotValid, 
        'tpl': DEFAULT_NotValid
    }
}

def get_default(default_key):
    return DL_DEFAULT[default_key]
