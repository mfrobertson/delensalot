import numpy as np
from lenscarf import utils_hp, remapping, cachers, utils_scarf, utils_dlm, utils_remapping
from lenscarf.utils_scarf import pbdGeometry, pbounds, scarfjob, Geom
from plancklens.utils import camb_clfile, cli
from scipy.special import spherical_jn
def get_jacobian(d:remapping.deflection):
    """

        Note:
            close to the poles the healpix geom is horrible (alm2map and map2alm not commuting unless 'iter' is high)

            Ok if not doing backward transforms

    """
    sjob = utils_scarf.scarfjob()
    sjob.set_geometry(d.geom)
    sjob.set_triangular_alm_info(d.lmax_dlm, d.mmax_dlm)
    sjob.set_nthreads(8)

    dclm = np.zeros_like(d.dlm) if d.dclm is None else d.dclm
    d1, d2 = d.geom.alm2map_spin([d.dlm, dclm], 1, d.lmax_dlm, d.mmax_dlm, d.sht_tr, [-1., 1.])
    k, (g1, g2), o = utils_dlm.dlm2kggo(sjob, dlm, dclm=dclm)

    dnorm = np.sqrt(d1 ** 2 + d2 ** 2)
    Mapprox = (1. - k) ** 2 + o ** 2 - g1 ** 2 - g2 ** 2
    Mtrue = spherical_jn(0, dnorm) * Mapprox - dnorm * spherical_jn(1, dnorm) * (1. - k - g1 * (d1 ** 2 - d2 ** 2) - g2 * ( 2 * d1 * d2))
    return Mapprox, Mtrue, k,  dnorm

if __name__ == '__main__':
    lmax_dlm, mmax_dlm, targetres_amin, sht_threads, fftw_threads = (4000, 4000, 1.7, 8, 8)
    cacher = cachers.cacher_mem()
    lenjob = scarfjob()
    #lenjob.set_thingauss_geometry(lmax_dlm, 2)
    lenjob.set_healpix_geometry(2048)
    # deflection instance:
    cldd = camb_clfile('../lenscarf/data/cls/FFP10_wdipole_lenspotentialCls.dat')['pp'][:lmax_dlm + 1]
    cldd *= np.sqrt(np.arange(lmax_dlm + 1) *  np.arange(1, lmax_dlm + 2))
    #dlm = hp.synalm(cldd, lmax=lmax_dlm, mmax=mmax_dlm) # get segfault with nontrivial mmax and new=True ?!
    dlm = utils_hp.synalm(cldd, lmax_dlm, mmax_dlm)
    d_geom = pbdGeometry(lenjob.geom, pbounds(np.pi, 2 * np.pi))
    d = remapping.deflection(d_geom, targetres_amin, dlm, mmax_dlm, sht_threads, fftw_threads, cacher=cacher)
    fl = 0.25 * np.sqrt(np.arange(d.lmax_dlm + 1) * np.arange(1, d.lmax_dlm + 2))
    sjob = utils_scarf.scarfjob()
    sjob.set_geometry(d.geom)
    sjob.set_triangular_alm_info(d.lmax_dlm, d.mmax_dlm)
    sjob.set_nthreads(sht_threads)

    Ma, Mt, k, dnorm = get_jacobian(d) # New calc.
    print(np.max(np.abs(Ma)), np.max(np.abs(Ma / Mt -1.)), np.max(np.abs( (Ma - 0.5 * dnorm ** 2)/ Mt-1)), np.max(np.abs( (1 - 2 * k) / Mt-1.)))
#(1.034787329002264,
# 1.8536532619961577e-07,
# 2.601621584830127e-09,
# 0.00029699305732244774)