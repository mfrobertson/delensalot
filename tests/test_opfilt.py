import numpy as np
import os
from time import time
import scarf
from lenscarf import remapping
from lenscarf import utils_config, utils_hp, utils
from lenscarf import cachers
from lenscarf.opfilt import opfilt_pp
from lenscarf.utils_scarf import Geom
from plancklens.utils import camb_clfile
import healpy as hp

lmax_dlm = 4096
lmax_unl = 4000
lmax_len = 4000
sht_threads = 8
fftw_threads = 8
fwhm = 2.3
targetres_amin=2.
lensjob, pbds = utils_config.cmbs4_08b_healpix()
lensgeom = lensjob.geom
ninvgeom = lensjob.geom

IPVMAP = '/global/cscratch1/sd/jcarron/cmbs4/temp/s08b/cILC2021_00/ipvmap.fits'
if not os.path.exists(IPVMAP):
    IPVMAP = '/Users/jcarron/OneDrive - unige.ch/cmbs4/inputs/ipvmap.fits'



# build slice for zbounded hp:
hp_geom = scarf.healpix_geometry(2048, 1)
hp_start = hp_geom.ofs[np.where(hp_geom.theta == np.min(ninvgeom.theta))[0]][0]
hp_end = hp_start + Geom.npix(ninvgeom).astype(hp_start.dtype) # Somehow otherwise makes a float out of int64 and uint64 ???

# deflection instance:
cldd = camb_clfile('../lenscarf/data/cls/FFP10_wdipole_lenspotentialCls.dat')['pp'][:lmax_dlm + 1]
cldd *= np.sqrt(np.arange(lmax_dlm + 1) *  np.arange(1, lmax_dlm + 2))
dlm = hp.synalm(cldd, new=True)

#cacher = cachers.cacher_npy('/Users/jcarron/OneDrive - unige.ch/lenscarf/temp/test_opfilt')
cacher = cachers.cacher_mem()
d = remapping.deflection(lensgeom, targetres_amin, pbds, dlm, sht_threads, fftw_threads, cacher=cacher)


t0 = time()
d._init_d1()
print('init d1: %.2fs'%(time() - t0))

t0 = time()
d._bwd_angles()
print('inverse deflection: %.2fs'%(time() - t0))
# ninv filter:
transf = utils_hp.gauss_beam(fwhm, lmax_len)
n_inv = [np.nan_to_num(utils.read_map(IPVMAP)[hp_start:hp_end])]
opfilt = opfilt_pp.alm_filter_ninv_wl(ninvgeom, n_inv, d,  transf, (lmax_len, lmax_len), (lmax_unl, lmax_unl), sht_threads)

elm = np.zeros(utils_hp.Alm.getsize(lmax_unl, lmax_unl), dtype=complex)
opfilt.apply_alm(elm)
print("2nd version without plans etc")
opfilt.apply_alm(elm)

"""NERSC  THREADS 16
                       scarf ecp job setup:  [00h:00m:00s:000ms] 
                             scarf alm2map:  [00h:00m:01s:986ms] 
                             fftw planning:  [00h:00m:00s:003ms] 
                                  fftw fwd:  [00h:00m:00s:421ms] 
                 bicubic prefilt, fftw bwd:  [00h:00m:00s:605ms] 
                             Interpolation:  [00h:00m:01s:551ms] 
                     Polarization rotation:  [00h:00m:00s:334ms] 
 gclm2lensedmap spin 2 lmax glm 4096 lmax dlm 4096 Total :  [00h:00m:05s:334ms] 
 [00:00:05] gclm2lensedmap spin 2 lmax glm 4000 lmax dlm 4096 > 00%
(2048, 4096) [00:03:25] (7, 0.00187220)
 [00:00:05] gclm2lensedmap spin 2 lmax glm 4096 lmax dlm 4096 > 00%
                       scarf ecp job setup:  [00h:00m:00s:000ms] 
                             scarf alm2map:  [00h:00m:01s:884ms] 
                             fftw planning:  [00h:00m:00s:003ms] 
                                  fftw fwd:  [00h:00m:00s:420ms] 
                 bicubic prefilt, fftw bwd:  [00h:00m:00s:600ms] 
                             Interpolation:  [00h:00m:01s:551ms] 
                     Polarization rotation:  [00h:00m:00s:334ms] 
 gclm2lensedmap spin 2 lmax glm 4000 lmax dlm 4096 Total :  [00h:00m:05s:224ms] 
 """