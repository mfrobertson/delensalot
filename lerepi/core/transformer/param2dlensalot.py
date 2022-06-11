#!/usr/bin/env python

"""param2dlensalot.py: transformer module to build dlensalot model from parameter file
"""
__author__ = "S. Belkner, J. Carron, L. Legrand"


import os, sys
from os.path import join as opj
import importlib
import traceback

import logging
log = logging.getLogger(__name__)
from logdecorator import log_on_start, log_on_end

import numpy as np
import healpy as hp
import hashlib

# TODO Only want initialisation at this level for lenscarf and plancklens objects, so queries work (lazy loading)
import plancklens
from plancklens.helpers import mpi
from plancklens import qest, qecl, utils
from plancklens.filt import filt_util, filt_cinv
from plancklens.qcinv import cd_solve
from plancklens.qcinv import opfilt_pp

from lenscarf import utils_scarf
import lenscarf.core.handler as lenscarf_handler
from lenscarf.utils import cli
from lenscarf.iterators import steps
from lenscarf.utils_hp import gauss_beam
from lenscarf.opfilt import utils_cinv_p as cinv_p_OBD
from lenscarf.opfilt.bmodes_ninv import template_dense

from lerepi.config.config_helper import data_functions as df
from lerepi.core.visitor import transform
from lerepi.core.metamodel.dlensalot import DLENSALOT_Concept, DLENSALOT_Model


class p2T_Transformer:
    """Directory is built upon runtime, so accessing it here

    Returns:
        _type_: _description_
    """
    @log_on_start(logging.INFO, "Start of build()")
    @log_on_end(logging.INFO, "Finished build()")
    def build(self, cf):
        _nsims_mf = 0 if cf.iteration.V == 'noMF' else cf.iteration.nsims_mf
        _suffix = cf.data.sims.split('/')[1]+'_%s'%(cf.data.fg)
        if cf.noisemodel.typ == 'OBD':
            _suffix += '_OBD'
        elif cf.noisemodel.typ == 'trunc':
            _suffix += '_OBDtrunc'+str(cf.noisemodel.lmin_blm)
        elif cf.noisemodel.typ == 'None' or cf.noisemodel.typ == None:
            _suffix += '_noOBD'

        _suffix += '_MF%s'%(_nsims_mf) if _nsims_mf > 0 else ''
        if cf.data.TEMP_suffix != '':
            _suffix += '_'+cf.data.TEMP_suffix
        TEMP =  opj(os.environ['SCRATCH'], cf.data.sims.split('/')[0], _suffix)

        return TEMP


    @log_on_start(logging.INFO, "Start of build_del_suffix()")
    @log_on_end(logging.INFO, "Finished build_del_suffix()")
    def build_del_suffix(self, dl):

        return os.path.join(dl.TEMP, dl.analysis_path, 'plotdata')


    @log_on_start(logging.INFO, "Start of build_OBD()")
    @log_on_end(logging.INFO, "Finished build_OBD()")
    def build_OBD(self, TEMP):

        return os.path.join(TEMP, 'OBD_matrix')


class p2lensrec_Transformer:
    """_summary_
    """

    @log_on_start(logging.INFO, "Start of build()")
    @log_on_end(logging.INFO, "Finished build()")
    def build(self, cf):
        @log_on_start(logging.INFO, "Start of _process_dataparams()")
        @log_on_end(logging.INFO, "Finished _process_dataparams()")
        def _process_dataparams(dl, data):
            dl.TEMP = transform(cf, p2T_Transformer())
            dl.nside = data.nside
            # TODO simplify the following two attributes
            dl.nsims_mf = 0 if cf.iteration.V == 'noMF' else cf.iteration.nsims_mf
            dl.mc_sims_mf_it0 = np.arange(dl.nsims_mf)
            dl.fg = data.fg

            _ui = data.sims.split('/')
            _sims_module_name = 'lerepi.config.'+_ui[0]+'.data.data_'+_ui[1]
            _sims_class_name = _ui[-1]
            _sims_module = importlib.import_module(_sims_module_name)
            dl.sims = getattr(_sims_module, _sims_class_name)(dl.fg)

            dl.masks = p2OBD_Transformer.get_masks(cf)

            dl.beam = data.BEAM
            dl.lmax_transf = data.lmax_transf
            dl.transf = data.transf(dl.beam / 180. / 60. * np.pi, lmax=dl.lmax_transf)

            if data.zbounds[0] == 'nmr_relative':
                dl.zbounds = df.get_zbounds(hp.read_map(cf.noisemodel.noisemodel_rhits), data.zbounds[1])
            elif data.zbounds[0] == float or data.zbounds[0] == int:
                dl.zbounds = data.zbounds
            else:
                log.error('Not sure what to do with this zbounds: {}'.format(data.zbounds))
                traceback.print_stack()
                sys.exit()
            if data.zbounds_len[0] == 'extend':
                dl.zbounds_len = df.extend_zbounds(dl.zbounds, degrees=data.zbounds_len[1])
            elif data.zbounds_len[0] == float or data.zbounds_len[0] == int:
                dl.zbounds_len = data.zbounds_len
            else:
                log.error('Not sure what to do with this zbounds_len: {}'.format(data.zbounds_len))
                traceback.print_stack()
                sys.exit()
            dl.pb_ctr, dl.pb_extent = data.pbounds

            cls_path = opj(os.path.dirname(plancklens.__file__), 'data', 'cls')
            dl.cls_unl = utils.camb_clfile(opj(cls_path, 'FFP10_wdipole_lenspotentialCls.dat'))
            dl.cls_len = utils.camb_clfile(opj(cls_path, 'FFP10_wdipole_lensedCls.dat'))


        @log_on_start(logging.INFO, "Start of _process_iterationparams()")
        @log_on_end(logging.INFO, "Finished _process_iterationparams()")
        def _process_iterationparams(dl, iteration):
            dl.version = iteration.V
            dl.k = iteration.K  
            dl.itmax = iteration.ITMAX
            dl.imin = iteration.IMIN
            dl.imax = iteration.IMAX
            dl.lmax_filt = iteration.lmax_filt
            
            dl.lmax_qlm = iteration.lmax_qlm
            dl.mmax_qlm = iteration.mmax_qlm
            
            dl.lmax_ivf = iteration.lmax_ivf
            dl.lmin_ivf = iteration.lmin_ivf
            dl.mmax_ivf = iteration.mmax_ivf

            dl.mmin_ivf = iteration.mmin_ivf
            dl.lmax_unl = iteration.lmax_unl
            dl.mmax_unl = iteration.mmax_unl

            dl.tol = iteration.TOL
            dl.tol_iter = lambda itr : 10 ** (- dl.tol) if itr <= 10 else 10 ** (-(dl.tol+1)) 
            dl.soltn_cond = iteration.soltn_cond # Uses (or not) previous E-mode solution as input to search for current iteration one
            dl.cg_tol = iteration.CG_TOL

            dl.cpp = np.copy(dl.cls_unl['pp'][:dl.lmax_qlm + 1])
            dl.cpp[:iteration.Lmin] *= 0. # TODO *0 or *1e-5?

            dl.lensres = iteration.LENSRES
            dl.tr = int(os.environ.get('OMP_NUM_THREADS', iteration.OMP_NUM_THREADS))
            dl.iterator = iteration.ITERATOR

            if iteration.STANDARD_TRANSFERFUNCTION == True:
                dl.nlev_t = p2OBD_Transformer.get_nlevt(cf)
                dl.nlev_p = p2OBD_Transformer.get_nlevp(cf)
                
                # Fiducial model of the transfer function
                dl.transf_tlm = gauss_beam(dl.beam/180 / 60 * np.pi, lmax=iteration.lmax_ivf) * (np.arange(iteration.lmax_ivf + 1) >= dl.lmin_tlm)
                dl.transf_elm = gauss_beam(dl.beam/180 / 60 * np.pi, lmax=iteration.lmax_ivf) * (np.arange(iteration.lmax_ivf + 1) >= dl.lmin_elm)
                dl.transf_blm = gauss_beam(dl.beam/180 / 60 * np.pi, lmax=iteration.lmax_ivf) * (np.arange(iteration.lmax_ivf + 1) >= dl.lmin_blm)

                # Isotropic approximation to the filtering (used eg for response calculations)
                dl.ftl =  cli(dl.cls_len['tt'][:iteration.lmax_ivf + 1] + (dl.nlev_t / 180 / 60 * np.pi) ** 2 * cli(dl.transf_tlm ** 2)) * (dl.transf_tlm > 0)
                dl.fel =  cli(dl.cls_len['ee'][:iteration.lmax_ivf + 1] + (dl.nlev_p / 180 / 60 * np.pi) ** 2 * cli(dl.transf_elm ** 2)) * (dl.transf_elm > 0)
                dl.fbl =  cli(dl.cls_len['bb'][:iteration.lmax_ivf + 1] + (dl.nlev_p / 180 / 60 * np.pi) ** 2 * cli(dl.transf_blm ** 2)) * (dl.transf_blm > 0)

                # Same using unlensed spectra (used for unlensed response used to initiate the MAP curvature matrix)
                dl.ftl_unl =  cli(dl.cls_unl['tt'][:iteration.lmax_ivf + 1] + (dl.nlev_t / 180 / 60 * np.pi) ** 2 * cli(dl.transf_tlm ** 2)) * (dl.transf_tlm > 0)
                dl.fel_unl =  cli(dl.cls_unl['ee'][:iteration.lmax_ivf + 1] + (dl.nlev_p / 180 / 60 * np.pi) ** 2 * cli(dl.transf_elm ** 2)) * (dl.transf_elm > 0)
                dl.fbl_unl =  cli(dl.cls_unl['bb'][:iteration.lmax_ivf + 1] + (dl.nlev_p / 180 / 60 * np.pi) ** 2 * cli(dl.transf_blm ** 2)) * (dl.transf_blm > 0)

            if iteration.FILTER == 'cinv_sepTP':
                dl.ninv_t = p2OBD_Transformer.get_ninvt(cf)
                dl.ninv_p = p2OBD_Transformer.get_ninvp(cf)
                # TODO cinv_t and cinv_p trigger computation. Perhaps move this to the lerepi job-level. Could be done via introducing a DLENSALOT_Filter model component
                dl.cinv_t = filt_cinv.cinv_t(opj(dl.TEMP, 'cinv_t'), iteration.lmax_ivf,dl.nside, dl.cls_len, dl.transf_tlm, dl.ninv_t,
                                marge_monopole=True, marge_dipole=True, marge_maps=[])
                # TODO this could move to _OBDparams()
                if dl.OBD_type == 'OBD':
                    transf_elm_loc = gauss_beam(dl.beam/180 / 60 * np.pi, lmax=iteration.lmax_ivf)
                    dl.cinv_p = cinv_p_OBD.cinv_p(opj(dl.TEMP, 'cinv_p'), dl.lmax_ivf, dl.nside, dl.cls_len, transf_elm_loc[:dl.lmax_ivf+1], dl.ninv_p, geom=dl.ninvjob_qe_geometry,
                        chain_descr=dl.chain_descr(iteration.lmax_ivf, iteration.CG_TOL), bmarg_lmax=dl.BMARG_LCUT, zbounds=dl.zbounds, _bmarg_lib_dir=dl.BMARG_LIBDIR, _bmarg_rescal=dl.BMARG_RESCALE, sht_threads=cf.iteration.OMP_NUM_THREADS)
                elif dl.OBD_type == 'trunc' or dl.OBD_type == None or dl.OBD_type == 'None':
                    dl.cinv_p = filt_cinv.cinv_p(opj(dl.TEMP, 'cinv_p'), dl.lmax_ivf, dl.nside, dl.cls_len, dl.transf_elm, dl.ninv_p,
                        chain_descr=dl.chain_descr(iteration.lmax_ivf, iteration.CG_TOL), transf_blm=dl.transf_blm, marge_qmaps=(), marge_umaps=())
                else:
                    log.error("Don't understand your OBD_typ input. Exiting..")
                    traceback.print_stack()
                    sys.exit()
                dl.ivfs_raw = filt_cinv.library_cinv_sepTP(opj(dl.TEMP, 'ivfs'), dl.sims, dl.cinv_t, dl.cinv_p, dl.cls_len)
                dl.ftl_rs = np.ones(iteration.lmax_ivf + 1, dtype=float) * (np.arange(iteration.lmax_ivf + 1) >= dl.lmin_tlm)
                dl.fel_rs = np.ones(iteration.lmax_ivf + 1, dtype=float) * (np.arange(iteration.lmax_ivf + 1) >= dl.lmin_elm)
                dl.fbl_rs = np.ones(iteration.lmax_ivf + 1, dtype=float) * (np.arange(iteration.lmax_ivf + 1) >= dl.lmin_blm)
                dl.ivfs   = filt_util.library_ftl(dl.ivfs_raw, iteration.lmax_ivf, dl.ftl_rs, dl.fel_rs, dl.fbl_rs)
                print('5')
                    
            if iteration.QE_LENSING_CL_ANALYSIS == True:
                dl.ss_dict = { k : v for k, v in zip( np.concatenate( [ range(i*60, (i+1)*60) for i in range(0,5) ] ),
                                        np.concatenate( [ np.roll( range(i*60, (i+1)*60), -1 ) for i in range(0,5) ] ) ) }
                dl.ds_dict = { k : -1 for k in range(300)} # This remap all sim. indices to the data maps to build QEs with always the data in one leg

                dl.ivfs_d = filt_util.library_shuffle(dl.ivfs, iteration.ds_dict)
                dl.ivfs_s = filt_util.library_shuffle(dl.ivfs, iteration.ss_dict)

                dl.qlms_ds = qest.library_sepTP(opj(dl.TEMP, 'qlms_ds'), iteration.ivfs, iteration.ivfs_d, dl.cls_len['te'], dl.nside, lmax_qlm=iteration.lmax_qlm)
                dl.qlms_ss = qest.library_sepTP(opj(dl.TEMP, 'qlms_ss'), iteration.ivfs, iteration.ivfs_s, dl.cls_len['te'], dl.nside, lmax_qlm=iteration.lmax_qlm)

                dl.mc_sims_bias = np.arange(60, dtype=int)
                dl.mc_sims_var  = np.arange(60, 300, dtype=int)

                dl.qcls_ds = qecl.library(opj(dl.TEMP, 'qcls_ds'), dl.qlms_ds, dl.qlms_ds, np.array([]))  # for QE RDN0 calculations
                dl.qcls_ss = qecl.library(opj(dl.TEMP, 'qcls_ss'), dl.qlms_ss, dl.qlms_ss, np.array([]))  # for QE RDN0 / MCN0 calculations
                dl.qcls_dd = qecl.library(opj(dl.TEMP, 'qcls_dd'), dl.qlms_dd, dl.qlms_dd, dl.mc_sims_bias)

            if iteration.FILTER_QE == 'sepTP':
                # ---- QE libraries from plancklens to calculate unnormalized QE (qlms)
                dl.qlms_dd = qest.library_sepTP(opj(dl.TEMP, 'qlms_dd'), dl.ivfs, dl.ivfs, dl.cls_len['te'], dl.nside, lmax_qlm=iteration.lmax_qlm)
            else:
                assert 0, 'Implement if needed'

        @log_on_start(logging.INFO, "Start of _process_geometryparams()")
        @log_on_end(logging.INFO, "Finished _process_geometryparams()")
        def _process_geometryparams(dl, geometry):
            if geometry.zbounds[0] == 'nmr_relative':
                zbounds_loc = df.get_zbounds(hp.read_map(cf.noisemodel.noisemodel_rhits), geometry.zbounds[1])
            elif geometry.zbounds[0] == float or geometry.zbounds[0] == int:
                zbounds_loc = geometry.zbounds
            else:
                log.error('Not sure what to do with this zbounds: {}'.format(geometry.zbounds))
                traceback.print_stack()
                sys.exit()
            if geometry.zbounds_len[0] == 'extend':
                zbounds_len_loc = df.extend_zbounds(zbounds_loc, degrees=geometry.zbounds_len[1])
            elif geometry.zbounds_len[0] == float or geometry.zbounds_len[0] == int:
                zbounds_len_loc = geometry.zbounds_len
            else:
                log.error('Not sure what to do with this zbounds_len: {}'.format(geometry.zbounds_len))
                traceback.print_stack()
                sys.exit()

            if geometry.lenjob_geometry == 'thin_gauss':
                dl.lenjob_geometry = utils_scarf.Geom.get_thingauss_geometry(geometry.lmax_unl, 2, zbounds=zbounds_len_loc)
            if geometry.lenjob_pbgeometry == 'pbdGeometry':
                dl.lenjob_pbgeometry = utils_scarf.pbdGeometry(dl.lenjob_geometry, utils_scarf.pbounds(geometry.pbounds[0], geometry.pbounds[1]))
            if geometry.ninvjob_geometry == 'healpix_geometry':
                # ninv MAP geometry. Could be merged with QE, if next comment resolved
                # TODO zbounds_loc must be identical to data.zbounds
                dl.ninvjob_geometry = utils_scarf.Geom.get_healpix_geometry(geometry.nside, zbounds=zbounds_loc)
            if geometry.ninvjob_qe_geometry == 'healpix_geometry_qe':
                # TODO for QE, isOBD only works with zbounds=(-1,1). Perhaps missing ztrunc on qumaps
                # Introduced new geometry for now, until either plancklens supports ztrunc, or ztrunced simlib (not sure if it already does)
                dl.ninvjob_qe_geometry = utils_scarf.Geom.get_healpix_geometry(geometry.nside, zbounds=(-1,1))
            elif geometry.ninvjob_qe_geometry == 'healpix_geometry':
                dl.ninvjob_qe_geometry = utils_scarf.Geom.get_healpix_geometry(geometry.nside, zbounds=zbounds_loc)


        @log_on_start(logging.INFO, "Start of _process_chaindescparams()")
        @log_on_end(logging.INFO, "Finished _process_chaindescparams()")
        def _process_chaindescparams(dl, cd):
            # TODO hacky solution. Redo if needed
            if cd.p6 == 'tr_cg':
                _p6 = cd_solve.tr_cg
            if cd.p7 == 'cache_mem':
                _p7 = cd_solve.cache_mem()
            dl.chain_descr = lambda p2, p5 : [
                [cd.p0, cd.p1, p2, cd.p3, cd.p4, p5, _p6, _p7]]


        @log_on_start(logging.INFO, "Start of _process_stepperparams()")
        @log_on_end(logging.INFO, "Finished _process_stepperparams()")
        def _process_stepperparams(dl, st):
            if st.typ == 'harmonicbump':
                dl.stepper = steps.harmonicbump(st.lmax_qlm, st.mmax_qlm, xa=st.xa, xb=st.xb)


        @log_on_start(logging.INFO, "Start of _process_OBDparams()")
        @log_on_end(logging.INFO, "Finished _process_OBDparams()")
        def _process_OBDparams(dl, ob):
            dl.OBD_type = ob.typ
            dl.BMARG_LCUT = ob.BMARG_LCUT
            dl.BMARG_LIBDIR = ob.BMARG_LIBDIR
            dl.BMARG_RESCALE = ob.BMARG_RESCALE
            if dl.OBD_type == 'OBD':
                # TODO need to check if tniti exists, and if tniti is the correct one
                if cf.data.tpl == 'template_dense':
                    def tpl_kwargs(lmax_marg, geom, sht_threads, _lib_dir=None, rescal=1.):
                        return locals()
                    dl.tpl = template_dense
                    dl.tpl_kwargs = tpl_kwargs(ob.BMARG_LCUT, dl.ninvjob_geometry, cf.iteration.OMP_NUM_THREADS, _lib_dir=dl.BMARG_LIBDIR, rescal=dl.BMARG_RESCALE) 
                else:
                    assert 0, "Implement if needed"
                # TODO need to initialise as function expect it, but do I want this? Shouldn't be needed
                dl.lmin_tlm = ob.lmin_tlm
                dl.lmin_elm = ob.lmin_elm
                dl.lmin_blm = ob.lmin_blm
            elif dl.OBD_type == 'trunc':
                dl.tpl = None
                dl.tpl_kwargs = dict()
                dl.lmin_tlm = ob.lmin_tlm
                dl.lmin_elm = ob.lmin_elm
                dl.lmin_blm = ob.lmin_blm
            elif dl.OBD_type == None or dl.OBD_type == 'None':
                dl.tpl = None
                dl.tpl_kwargs = dict()
                # TODO are 0s a good value? 
                dl.lmin_tlm = 0
                dl.lmin_elm = 0
                dl.lmin_blm = 0
            else:
                log.error("Don't understand your OBD_type input. Exiting..")
                traceback.print_stack()
                sys.exit()


        dl = DLENSALOT_Concept()
        _process_geometryparams(dl, cf.geometry)
        _process_OBDparams(dl, cf.noisemodel)
        _process_dataparams(dl, cf.data)
        _process_chaindescparams(dl, cf.chain_descriptor)
        _process_iterationparams(dl, cf.iteration)
        _process_stepperparams(dl, cf.stepper)

        if mpi.rank == 0:
            log.info("I am going to work with the following values: {}".format(dl.__dict__))

        return dl


class p2OBD_Transformer:
    """Extracts all parameters needed for building consistent OBD
    """
    @log_on_start(logging.INFO, "Start of get_nlrh_map()")
    @log_on_end(logging.INFO, "Finished get_nlrh_map()")
    def get_nlrh_map(cf):
        noisemodel_rhits_map = df.get_nlev_mask(cf.noisemodel.ratio, hp.read_map(cf.noisemodel.noisemodel_rhits))
        noisemodel_rhits_map[noisemodel_rhits_map == np.inf] = cf.noisemodel.inf

        return noisemodel_rhits_map


    # @log_on_start(logging.INFO, "Start of get_nlevt()")
    # @log_on_end(logging.INFO, "Finished get_nlevt()")
    def get_nlevt(cf):
        nlev_t = cf.data.CENTRALNLEV_UKAMIN/np.sqrt(2) if cf.noisemodel.nlev_t == None else cf.noisemodel.nlev_t

        return nlev_t


    # @log_on_start(logging.INFO, "Start of get_nlevp()")
    # @log_on_end(logging.INFO, "Finished get_nlevp()")
    def get_nlevp(cf):
        nlev_p = cf.noisemodel.CENTRALNLEV_UKAMIN if cf.noisemodel.nlev_p == None else cf.noisemodel.nlev_p

        return nlev_p


    @log_on_start(logging.INFO, "Start of get_ninvt()")
    @log_on_end(logging.INFO, "Finished get_ninvt()")
    def get_ninvt(cf):
        nlev_t = p2OBD_Transformer.get_nlevp(cf)
        masks, noisemodel_rhits_map =  p2OBD_Transformer.get_masks(cf)
        noisemodel_norm = np.max(noisemodel_rhits_map)
        t_transf = gauss_beam(cf.data.BEAM/180 / 60 * np.pi, lmax=cf.iteration.lmax_ivf)
        ninv_desc = [[np.array([hp.nside2pixarea(cf.data.nside, degrees=True) * 60 ** 2 / nlev_t ** 2])/noisemodel_norm] + masks]
        ninv_t = opfilt_pp.alm_filter_ninv(ninv_desc, t_transf, marge_qmaps=(), marge_umaps=()).get_ninv()

        return ninv_t


    @log_on_start(logging.INFO, "Start of get_ninvp()")
    @log_on_end(logging.INFO, "Finished get_ninvp()")
    def get_ninvp(cf):
        nlev_p = p2OBD_Transformer.get_nlevp(cf)
        masks, noisemodel_rhits_map =  p2OBD_Transformer.get_masks(cf)
        noisemodel_norm = np.max(noisemodel_rhits_map)
        b_transf = gauss_beam(cf.data.BEAM/180 / 60 * np.pi, lmax=cf.iteration.lmax_ivf) # TODO ninv_p doesn't depend on this anyway, right?
        ninv_desc = [[np.array([hp.nside2pixarea(cf.data.nside, degrees=True) * 60 ** 2 / nlev_p ** 2])/noisemodel_norm] + masks]
        ninv_p = opfilt_pp.alm_filter_ninv(ninv_desc, b_transf, marge_qmaps=(), marge_umaps=()).get_ninv()

        return ninv_p


    # @log_on_start(logging.INFO, "Start of get_masks()")
    # @log_on_end(logging.INFO, "Finished get_masks()")
    def get_masks(cf):
        masks = []
        if cf.noisemodel.noisemodel_rhits is not None:
            msk = p2OBD_Transformer.get_nlrh_map(cf)
            masks.append(msk)
        if cf.noisemodel.mask[0] == 'nlev':
            noisemodel_rhits_map = msk.copy()
            _mask = df.get_nlev_mask(cf.noisemodel.mask[1], noisemodel_rhits_map)
            _mask = np.where(_mask>0., 1., 0.)
            masks.append(_mask)

        return masks, msk


    def build(self, cf):
        @log_on_start(logging.INFO, "Start of _process_builOBDparams()")
        @log_on_end(logging.INFO, "Finished _process_builOBDparams()")
        def _process_builOBDparams(dl, nm):
            _TEMP = transform(cf, p2T_Transformer())
            dl.TEMP = transform(_TEMP, p2T_Transformer())
            if os.path.isfile(opj(nm.BMARG_LIBDIR,'tniti.npy')):
                # TODO need to test if it is the right tniti.npy
                log.warning("tniti.npy in destination dir {} already exists.".format(nm.BMARG_LIBDIR))
            if os.path.isfile(opj(dl.TEMP,'tniti.npy')):
                # TODO need to test if it is the right tniti.npy
                log.warning("tniti.npy in buildpath dir {} already exists.".format(dl.TEMP))
                log.warning("Exiting. Please check your settings.")
                sys.exit()
            else:
                dl.BMARG_LCUT = nm.BMARG_LCUT
                dl.nside = cf.data.nside
                dl.nlev_dep = nm.nlev_dep
                dl.CENTRALNLEV_UKAMIN = nm.CENTRALNLEV_UKAMIN
                dl.geom = utils_scarf.Geom.get_healpix_geometry(dl.nside)
                dl.masks, dl.rhits_map = p2OBD_Transformer.get_masks(cf)
                dl.nlev_p = p2OBD_Transformer.get_nlevp(cf)
                dl.ninv_p = p2OBD_Transformer.get_ninvp(cf)


        dl = DLENSALOT_Concept()
        _process_builOBDparams(dl, cf.noisemodel)

        return dl


class p2q_Transformer:
    """Extracts all parameters needed for building consistent OBD
    """
    def build(self, cf):
        
        pass


class p2d_Transformer:
    """Directory is built upon runtime, so accessing it here

    Returns:
        _type_: _description_
    """
    @log_on_start(logging.INFO, "Start of build()")
    @log_on_end(logging.INFO, "Finished build()")
    def build(self, cf):
        # TODO make this an option for the user. If needed, user can define their own edges via configfile.
        fs_edges = np.arange(2,3000, 20)
        ioreco_edges = np.array([2, 30, 200, 300, 500, 700, 1000, 1500, 2000, 3000, 4000, 5000])
        cmbs4_edges = np.array([2, 30, 60, 90, 120, 150, 180, 200, 300, 500, 700, 1000, 1500, 2000, 3000, 4000, 5000])
        def _process_delensingparams(dl, de):
            dl.k = cf.iteration.K # Lensing key, either p_p, ptt, p_eb
            dl.version = cf.iteration.V # version, can be 'noMF'
            if de.edges == 'ioreco':
                dl.edges = ioreco_edges
            elif de.edges == 'cmbs4':
                dl.edges = cmbs4_edges
            elif de.edges == 'fs':
                dl.edges = fs_edges
            dl.edges_center = (dl.edges[1:]+dl.edges[:-1])/2.
            dl.imin = de.IMIN
            dl.imax = de.IMAX
            dl.itmax = de.ITMAX
            dl.fg = de.fg
 
            _ui = de.base_mask.split('/')
            _sims_module_name = 'lerepi.config.'+_ui[0]+'.data.data_'+_ui[1]
            _sims_class_name = _ui[-1]
            _sims_module = importlib.import_module(_sims_module_name)
            de.sims = getattr(_sims_module, _sims_class_name)(dl.fg)

            mask_path = de.sims.p2mask
            dl.base_mask = np.nan_to_num(hp.read_map(mask_path))
            dl.TEMP = transform(cf, p2T_Transformer())
            dl.analysis_path = dl.TEMP.split('/')[-1]
            dl.TEMP_DELENSED_SPECTRUM = transform(dl, p2T_Transformer())

            dl.nlevels = de.nlevels
            dl.nside = de.nside
            dl.lmax_cl = de.lmax_cl
            dl.lmax_lib = 3*dl.lmax_cl-1
            dl.beam = de.beam
            dl.lmax_transf = de.lmax_transf
            if de.transf == 'gauss':
                dl.transf = hp.gauss_beam(dl.beam / 180. / 60. * np.pi, lmax=dl.lmax_transf)

            if de.Cl_fid == 'ffp10':
                dl.cls_path = opj(os.path.dirname(plancklens.__file__), 'data', 'cls')
                dl.cls_len = utils.camb_clfile(opj(dl.cls_path, 'FFP10_wdipole_lensedCls.dat'))
                dl.clg_templ = dl.cls_len['ee']
                dl.clc_templ = dl.cls_len['bb']
                dl.clg_templ[0] = 1e-32
                dl.clg_templ[1] = 1e-32

            dl.sha_edges = hashlib.sha256()
            dl.sha_edges.update(str(dl.edges).encode())
            dl.dirid = dl.sha_edges.hexdigest()[:4]


        dl = DLENSALOT_Concept()
        _process_delensingparams(dl, cf.map_delensing)

        return dl


class p2i_Transformer:
    """Directory is built upon runtime, so accessing it here

    Returns:
        _type_: _description_
    """
    @log_on_start(logging.INFO, "Start of build()")
    @log_on_end(logging.INFO, "Finished build()")
    def buil(cf):
        pass


class p2j_Transformer:
    """Extracts parameters needed for the specific D.Lensalot jobs
    Implement if needed
    """
    def build(self, pf):
        jobs = []
        # TODO if the pf.X objects were distinguishable by X2X_Transformer, could replace the seemingly redundant if checks here.
        if pf.job.build_OBD:
            jobs.append(((pf, p2OBD_Transformer()), lenscarf_handler.OBD_builder))
        if pf.job.QE_lensrec:
            jobs.append(((pf, p2lensrec_Transformer()), lenscarf_handler.QE_lr))
        if pf.job.MAP_lensrec:
            jobs.append(((pf, p2lensrec_Transformer()), lenscarf_handler.MAP_lr))
        if pf.job.Btemplate_per_iteration:
            jobs.append(((pf, p2lensrec_Transformer()), lenscarf_handler.B_template_construction))
        if pf.job.map_delensing:
            jobs.append(((pf, p2d_Transformer()), lenscarf_handler.map_delensing))
        if pf.job.inspect_result:
            # TODO maybe use this to return something interactive? Like a webservice with all plots dynamic? Like a dashboard..
            jobs.append(((pf, p2i_Transformer()), lenscarf_handler.inspect_result))
        return jobs


@transform.case(DLENSALOT_Model, p2j_Transformer)
def f1(expr, transformer): # pylint: disable=missing-function-docstring
    return transformer.build(expr)

@transform.case(DLENSALOT_Model, p2T_Transformer)
def f2a(expr, transformer): # pylint: disable=missing-function-docstring
    return transformer.build(expr)

@transform.case(DLENSALOT_Concept, p2T_Transformer)
def f2b(expr, transformer): # pylint: disable=missing-function-docstring
    return transformer.build_del_suffix(expr)

@transform.case(str, p2T_Transformer)
def f2c(expr, transformer): # pylint: disable=missing-function-docstring
    return transformer.build_OBD(expr)

@transform.case(DLENSALOT_Model, p2lensrec_Transformer)
def f3(expr, transformer): # pylint: disable=missing-function-docstring
    return transformer.build(expr)

@transform.case(DLENSALOT_Model, p2OBD_Transformer)
def f4(expr, transformer): # pylint: disable=missing-function-docstring
    return transformer.build(expr)

@transform.case(DLENSALOT_Model, p2d_Transformer)
def f5(expr, transformer): # pylint: disable=missing-function-docstring
    return transformer.build(expr)

@transform.case(DLENSALOT_Model, p2i_Transformer)
def f6(expr, transformer): # pylint: disable=missing-function-docstring
    # TODO this could be a solution to connect to a future 'inspect' module,
    # or 'prepare_inspect'..
    assert 0, "Implement if needed"
    return transformer.build(expr)

@transform.case(DLENSALOT_Model, p2q_Transformer)
def f7(expr, transformer): # pylint: disable=missing-function-docstring
    # TODO this could be a solution to connect to a future 'query' module. 
    assert 0, "Implement if needed"
    return transformer.build(expr)