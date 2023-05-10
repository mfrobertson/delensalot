"""Scarf-geometry based inverse-variance filters, inclusive of CMB lensing remapping

    This module collects filter instances working on idealized skies with homogeneous or colored noise spectra



"""
import logging
log = logging.getLogger(__name__)
from logdecorator import log_on_start, log_on_end

import numpy as np
from delensalot.utils_hp import almxfl, Alm, synalm
from delensalot.utils import timer, cli
from lenspyx.remapping import utils_geom
from lenspyx import remapping
from scipy.interpolate import UnivariateSpline as spl
from delensalot.opfilt import opfilt_ee_wl, opfilt_base

pre_op_dense = None # not implemented
dot_op = opfilt_ee_wl.dot_op
fwd_op = opfilt_ee_wl.fwd_op
apply_fini = opfilt_ee_wl.apply_fini

def _extend_cl(cl, lmax):
    """Forces input to an array of size lmax + 1

    """
    if np.isscalar(cl):
        return np.ones(lmax + 1, dtype=float) * cl
    ret = np.zeros(lmax + 1, dtype=float)
    ret[:min(len(cl), lmax+1)]= np.copy(cl[:min(len(cl), lmax+1)])
    return ret

class alm_filter_nlev_wl(opfilt_base.scarf_alm_filter_wl):
    def __init__(self, nlev_p:float or np.ndarray, ffi:remapping.deflection, transf:np.ndarray, unlalm_info:tuple, lenalm_info:tuple,
                 transf_b:None or np.ndarray=None, nlev_b:None or float or np.ndarray=None, wee=True, verbose=False):
        r"""Version of alm_filter_ninv_wl for full-sky maps filtered with homogeneous noise levels


                Args:
                    nlev_p: CMB-E filtering noise level in uK-amin
                            (to input colored noise cls, can feed in an array. Size must match that of the transfer fct)
                    ffi: delensalot deflection instance
                    transf: CMB E-mode transfer function (beam, pixel window, mutlipole cuts, ...)
                    unlalm_info: lmax and mmax of unlensed CMB
                    lenalm_info: lmax and mmax of lensed CMB (greater or equal the transfer lmax)
                    transf_b(optional): CMB B-mode transfer function (if different from E)
                    nlev_b(optional): CMB-B filtering noise level in uK-amin
                             (to input colored noise cls, can feed in an array. Size must match that of the transfer fct)
                    wee: includes EE-like term in generalized QE if set

                Note:
                    All operations are in harmonic space.
                    Mode exclusions can be implemented setting the transfer fct to zero
                    (but the instance still expects the Elm and Blm arrays to have the same formal lmax)


        """
        lmax_sol, mmax_sol = unlalm_info
        lmax_len, mmax_len = lenalm_info
        lmax_transf = max(len(transf), len(transf if transf_b is None else transf_b)) - 1
        nlev_e = nlev_p
        nlev_b = nlev_p if nlev_b is None else nlev_b

        super().__init__(lmax_sol, mmax_sol, ffi)
        self.lmax_len = min(lmax_len, lmax_transf)
        self.mmax_len = min(mmax_len, self.lmax_len)

        transf_elm = transf
        transf_blm = transf_b if transf_b is not None else transf

        nlev_elm = _extend_cl(nlev_e, lmax_len)
        nlev_blm = _extend_cl(nlev_b, lmax_len)

        self.inoise_2_elm  = _extend_cl(transf_elm ** 2, lmax_len) * cli(nlev_elm ** 2) * (180 * 60 / np.pi) ** 2
        self.inoise_1_elm  = _extend_cl(transf_elm ** 1 ,lmax_len) * cli(nlev_elm ** 2) * (180 * 60 / np.pi) ** 2

        self.inoise_2_blm = _extend_cl(transf_blm ** 2, lmax_len) * cli(nlev_blm ** 2) * (180 * 60 / np.pi) ** 2
        self.inoise_1_blm = _extend_cl(transf_blm ** 1, lmax_len) * cli(nlev_blm ** 2) * (180 * 60 / np.pi) ** 2

        self.transf_elm  = _extend_cl(transf_elm, lmax_len)
        self.transf_blm  = _extend_cl(transf_blm, lmax_len)

        self.nlev_elm = nlev_elm
        self.nlev_blm = nlev_blm

        self.verbose = verbose
        self.wee = wee
        self.tim = timer(True, prefix='opfilt')

    def get_febl(self):
        return np.copy(self.inoise_2_elm), np.copy(self.inoise_2_blm)

    def set_ffi(self, ffi:remapping.deflection):
        self.ffi = ffi

    def dot_op(self):
        return dot_op(self.lmax_sol, self.mmax_sol)

    def apply_alm(self, elm:np.ndarray):
        """Applies operator Y^T N^{-1} Y (now  bl ** 2 / n, where D is lensing, bl the transfer function)

        """
        # Forward lensing here
        tim = self.tim
        tim.reset_t0()
        lmax_unl = Alm.getlmax(elm.size, self.mmax_sol)
        assert lmax_unl == self.lmax_sol, (lmax_unl, self.lmax_sol)
        eblm = self.ffi.lensgclm(np.array([elm, np.zeros_like(elm)]), self.mmax_sol, 2, self.lmax_len, self.mmax_len)
        tim.add('lensgclm fwd')

        almxfl(eblm[0], self.inoise_2_elm, self.mmax_len, inplace=True)
        almxfl(eblm[1], self.inoise_2_blm, self.mmax_len, inplace=True)
        tim.add('transf')

        # backward lensing with magn. mult. here
        eblm = self.ffi.lensgclm(eblm, self.mmax_len, 2, self.lmax_sol, self.mmax_sol, backwards=True)
        elm[:] = eblm[0]
        tim.add('lensgclm bwd')
        if self.verbose:
            print(tim)

    def apply_map(self, eblm:np.ndarray):
        """Applies noise operator in place"""
        almxfl(eblm[0], self.inoise_1_elm * cli(self.transf_elm), self.mmax_len, True)
        almxfl(eblm[1], self.inoise_1_blm * cli(self.transf_elm), self.mmax_len, True)

    def synalm(self, unlcmb_cls:dict, cmb_phas=None, get_unlelm=True):
        """Generate some dat maps consistent with noise filter fiducial ingredients

            Note:
                Feeding in directly the unlensed CMB phase can be useful for paired simulations.
                In this case the shape must match that of the filter unlensed alm array


        """
        elm = synalm(unlcmb_cls['ee'], self.lmax_sol, self.mmax_sol) if cmb_phas is None else cmb_phas
        assert Alm.getlmax(elm.size, self.mmax_sol) == self.lmax_sol, (Alm.getlmax(elm.size, self.mmax_sol), self.lmax_sol)
        eblm = self.ffi.lensgclm(np.array([elm, elm * 0]), self.mmax_sol, 2, self.lmax_len, self.mmax_len, backwards=False)
        almxfl(eblm[0], self.transf_elm, self.mmax_len, True)
        almxfl(eblm[1], self.transf_blm, self.mmax_len, True)
        eblm[0] += synalm((np.ones(self.lmax_len + 1) * (self.nlev_elm / 180 / 60 * np.pi) ** 2) * (self.transf_elm > 0), self.lmax_len, self.mmax_len)
        eblm[1] += synalm((np.ones(self.lmax_len + 1) * (self.nlev_blm / 180 / 60 * np.pi) ** 2) * (self.transf_blm > 0), self.lmax_len, self.mmax_len)
        return elm, eblm if get_unlelm else eblm

    def get_qlms(self, eblm_dat: np.ndarray or list, elm_wf: np.ndarray, q_pbgeom: utils_geom.pbdGeometry, alm_wf_leg2:None or np.ndarray =None):
        """Get lensing generaliazed QE consistent with filter assumptions

            Args:
                eblm_dat: input polarization maps (geom must match that of the filter)
                elm_wf: Wiener-filtered CMB maps (alm arrays)
                alm_wf_leg2: Wiener-filtered CMB maps of gradient leg, if different from ivf leg (alm arrays)
                q_pbgeom: scarf pbounded-geometry of for the position-space mutliplication of the legs

            All implementation signs are super-weird but end result should be correct...

        """
        assert Alm.getlmax(eblm_dat[0].size, self.mmax_len) == self.lmax_len, (Alm.getlmax(eblm_dat[0].size, self.mmax_len), self.lmax_len)
        assert Alm.getlmax(eblm_dat[1].size, self.mmax_len) == self.lmax_len, (Alm.getlmax(eblm_dat[1].size, self.mmax_len), self.lmax_len)
        assert Alm.getlmax(elm_wf.size, self.mmax_sol) == self.lmax_sol, (Alm.getlmax(elm_wf.size, self.mmax_sol), self.lmax_sol)

        ebwf = np.array([elm_wf, np.zeros_like(elm_wf)])
        repmap, impmap = self._get_irespmap(eblm_dat, ebwf, q_pbgeom)
        if alm_wf_leg2 is not None:
            assert Alm.getlmax(alm_wf_leg2.size, self.mmax_sol) == self.lmax_sol, (Alm.getlmax(alm_wf_leg2.size, self.mmax_sol), self.lmax_sol)
            ebwf[0, :] = alm_wf_leg2
        Gs, Cs = self._get_gpmap(ebwf, 3, q_pbgeom)  # 2 pos.space maps
        GC = (repmap - 1j * impmap) * (Gs + 1j * Cs)  # (-2 , +3)
        Gs, Cs = self._get_gpmap(ebwf, 1, q_pbgeom)
        GC -= (repmap + 1j * impmap) * (Gs - 1j * Cs)  # (+2 , -1)
        del repmap, impmap, Gs, Cs
        lmax_qlm, mmax_qlm = self.ffi.lmax_dlm, self.ffi.mmax_dlm
        G, C = q_pbgeom.geom.map2alm_spin([GC.real, GC.imag], 1, lmax_qlm, mmax_qlm, self.ffi.sht_tr, (-1., 1.))
        del GC
        fl = - np.sqrt(np.arange(lmax_qlm + 1, dtype=float) * np.arange(1, lmax_qlm + 2))
        almxfl(G, fl, mmax_qlm, True)
        almxfl(C, fl, mmax_qlm, True)
        return G, C

    def get_qlms_mf(self, mfkey, q_pbgeom:utils_geom.pbdGeometry, mchain, phas=None, cls_filt:dict or None=None):
        """Mean-field estimate using tricks of Carron Lewis appendix


        """
        if mfkey in [1]: # This should be B^t x, D dC D^t B^t Covi x, x random phases in alm space
            if phas is None:
                phas = np.array([synalm(np.ones(self.lmax_len + 1, dtype=float), self.lmax_len, self.mmax_len),
                                 synalm(np.ones(self.lmax_len + 1, dtype=float), self.lmax_len, self.mmax_len)])
            assert Alm.getlmax(phas[0].size, self.mmax_len) == self.lmax_len
            assert Alm.getlmax(phas[1].size, self.mmax_len) == self.lmax_len

            soltn = np.zeros(Alm.getsize(self.lmax_sol, self.mmax_sol), dtype=complex)
            mchain.solve(soltn, phas, dot_op=self.dot_op())

            almxfl(phas[0], 0.5 * self.transf_elm, self.mmax_len, True)
            almxfl(phas[1], 0.5 * self.transf_blm, self.mmax_len, True)
            repmap, impmap = q_pbgeom.geom.alm2map_spin(phas, 2, self.lmax_len, self.mmax_len, self.ffi.sht_tr, (-1., 1.))

            Gs, Cs = self._get_gpmap([soltn, np.zeros_like(soltn)], 3, q_pbgeom)  # 2 pos.space maps
            GC = (repmap - 1j * impmap) * (Gs + 1j * Cs)  # (-2 , +3)
            Gs, Cs = self._get_gpmap([soltn, np.zeros_like(soltn)], 1, q_pbgeom)
            GC -= (repmap + 1j * impmap) * (Gs - 1j * Cs)  # (+2 , -1)
            del repmap, impmap, Gs, Cs
        elif mfkey in [0]: # standard gQE, quite inefficient but simple
            assert phas is None, 'discarding this phase anyways'
            elm_pha, eblm_dat = self.synalm(cls_filt)
            eblm_dat = np.array(eblm_dat)
            elm_wf = np.zeros(Alm.getsize(self.lmax_sol, self.mmax_sol), dtype=complex)
            mchain.solve(elm_wf, eblm_dat, dot_op=self.dot_op())
            return self.get_qlms(eblm_dat, elm_wf, q_pbgeom)

        else:
            assert 0, mfkey + ' not implemented'
        lmax_qlm = self.ffi.lmax_dlm
        mmax_qlm = self.ffi.mmax_dlm
        G, C = q_pbgeom.geom.map2alm_spin([GC.real, GC.imag], 1, lmax_qlm, mmax_qlm, self.ffi.sht_tr, (-1., 1.))
        del GC
        fl = - np.sqrt(np.arange(lmax_qlm + 1, dtype=float) * np.arange(1, lmax_qlm + 2))
        almxfl(G, fl, mmax_qlm, True)
        almxfl(C, fl, mmax_qlm, True)
        return G, C


    def _get_irespmap(self, eblm_dat:np.ndarray, eblm_wf:np.ndarray or list, q_pbgeom:utils_geom.pbdGeometry):
        """Builds inverse variance weighted map to feed into the QE


            :math:`B^t N^{-1}(X^{\rm dat} - B D X^{WF})`


        """
        assert len(eblm_dat) == 2
        ebwf = self.ffi.lensgclm(eblm_wf, self.mmax_sol, 2, self.lmax_len, self.mmax_len, backwards=False)
        almxfl(ebwf[0], self.transf_elm, self.mmax_len, True)
        almxfl(ebwf[1], self.transf_blm, self.mmax_len, True)
        ebwf[:] = eblm_dat - ebwf
        almxfl(ebwf[0], self.inoise_1_elm * 0.5 * self.wee, self.mmax_len, True)  # Factor of 1/2 because of \dagger rather than ^{-1}
        almxfl(ebwf[1], self.inoise_1_blm * 0.5,            self.mmax_len, True)
        return q_pbgeom.geom.alm2map_spin(ebwf, 2, self.lmax_len, self.mmax_len, self.ffi.sht_tr, (-1., 1.))

    def _get_gpmap(self, eblm_wf:np.ndarray or list, spin:int, q_pbgeom:utils_geom.pbdGeometry):
        """Wiener-filtered gradient leg to feed into the QE


            :math:`\sum_{lm} (Elm +- iBlm) sqrt(l+2 (l-1)) _1 Ylm(n)
                                           sqrt(l-2 (l+3)) _3 Ylm(n)`

            Output is list with real and imaginary part of the spin 1 or 3 transforms.


        """
        assert len(eblm_wf) == 2
        assert  Alm.getlmax(eblm_wf[0].size, self.mmax_sol)== self.lmax_sol, ( Alm.getlmax(eblm_wf[0].size, self.mmax_sol), self.lmax_sol)
        assert spin in [1, 3], spin
        lmax = Alm.getlmax(eblm_wf[0].size, self.mmax_sol)
        i1, i2 = (2, -1) if spin == 1 else (-2, 3)
        fl = np.arange(i1, lmax + i1 + 1, dtype=float) * np.arange(i2, lmax + i2 + 1)
        fl[:spin] *= 0.
        fl = np.sqrt(fl)
        eblm = np.array([almxfl(eblm_wf[0], fl, self.mmax_sol, False), almxfl(eblm_wf[1], fl, self.mmax_sol, False)])
        ffi = self.ffi.change_geom(q_pbgeom) if q_pbgeom is not self.ffi.pbgeom else self.ffi
        return ffi.gclm2lenmap(eblm, self.mmax_sol, spin, False)

class pre_op_diag:
    """Cg-inversion diagonal preconditioner


    """
    def __init__(self, s_cls:dict, ninv_filt:alm_filter_nlev_wl):
        assert len(s_cls['ee']) > ninv_filt.lmax_sol, (ninv_filt.lmax_sol, len(s_cls['ee']))
        lmax_sol = ninv_filt.lmax_sol
        ninv_fel, ninv_fbl = ninv_filt.get_febl()
        if len(ninv_fel) - 1 < lmax_sol: # We extend the transfer fct to avoid predcon. with zero (~ Gauss beam)
            log.info("PRE_OP_DIAG: extending transfer fct from lmax %s to lmax %s"%(len(ninv_fel)-1, lmax_sol))
            assert np.all(ninv_fel >= 0)
            nz = np.where(ninv_fel > 0)
            spl_sq = spl(np.arange(len(ninv_fel), dtype=float)[nz], np.log(ninv_fel[nz]), k=2, ext='extrapolate')
            ninv_fel = np.exp(spl_sq(np.arange(lmax_sol + 1, dtype=float)))
        flmat = cli(s_cls['ee'][:lmax_sol + 1]) + ninv_fel[:lmax_sol + 1]
        self.flmat = cli(flmat) * (s_cls['ee'][:lmax_sol +1] > 0.)
        self.lmax = ninv_filt.lmax_sol
        self.mmax = ninv_filt.mmax_sol

    def __call__(self, eblm):
        return self.calc(eblm)

    def calc(self, elm):
        assert Alm.getsize(self.lmax, self.mmax) == elm.size, (self.lmax, self.mmax, Alm.getlmax(elm.size, self.mmax))
        return almxfl(elm, self.flmat, self.mmax, False)


def calc_prep(eblm:np.ndarray, s_cls:dict, ninv_filt:alm_filter_nlev_wl):
    """cg-inversion pre-operation

        This performs :math:`D_\phi^t B^t N^{-1} X^{\rm dat}`

        Args:
            eblm: input data polarisation elm and blm
            s_cls: CMB spectra dictionary (here only 'ee' key required)
            ninv_filt: inverse-variance filtering instance


    """
    assert isinstance(eblm, np.ndarray)
    assert Alm.getlmax(eblm[0].size, ninv_filt.mmax_len) == ninv_filt.lmax_len, (Alm.getlmax(eblm[0].size, ninv_filt.mmax_len), ninv_filt.lmax_len)
    eblmc = np.copy(eblm)
    almxfl(eblmc[0], ninv_filt.inoise_1_elm, ninv_filt.mmax_len, True)
    almxfl(eblmc[1], ninv_filt.inoise_1_blm, ninv_filt.mmax_len, True)
    elm, blm = ninv_filt.ffi.lensgclm(eblmc, ninv_filt.mmax_len, 2, ninv_filt.lmax_sol,ninv_filt.mmax_sol, backwards=True)
    almxfl(elm, s_cls['ee'] > 0., ninv_filt.mmax_sol, True)
    return elm