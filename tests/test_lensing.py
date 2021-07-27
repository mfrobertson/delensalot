from lenscarf import cachers, remapping
import numpy as np
from lenscarf import utils_scarf as sj
import healpy as hp
from lenscarf import utils_config
from plancklens.utils import camb_clfile


# PBOUNDS = (np.pi, 2* np.pi)
#j = sj.scarfjob()
#j.set_thingauss_geometry(3999, 2, zbounds=(0.9, 1.))
#j, PBOUNDS = utils_config.cmbs4_08b_healpix()
j, PBOUNDS, zbounds_len, zbounds_ninv = utils_config.full_sky_healpix()

#print(PBOUNDS, np.min(j.geom.cth), np.max(j.geom.cth))

lmaxin = 3999
lmaxout = 2999
mmax_dlm = lmaxin
clee = camb_clfile('../lenscarf/data/cls/FFP10_wdipole_lensedCls.dat')['ee'][:lmaxin + 1]
clpp = camb_clfile('../lenscarf/data/cls/FFP10_wdipole_lenspotentialCls.dat')['pp'][:lmaxin + 1]

glm = hp.synalm(clee, new=True)
plm = hp.synalm(clpp, new=True)


dlm = hp.almxfl(plm, np.sqrt(np.arange(lmaxin + 1) * np.arange(1, lmaxin + 2)))
d_geom = sj.pbdGeometry(j.geom, sj.pbounds(PBOUNDS[0], PBOUNDS[1]))
d = remapping.deflection(d_geom, 1.7, dlm, mmax_dlm, 8, 8, cacher=cachers.cacher_mem(), verbose=True)

d.lensgclm(glm, mmax_dlm, 0, lmaxout, lmaxout)
d.tim.reset()
d.lensgclm(glm, mmax_dlm, 0, lmaxout, lmaxout)
d.tim.reset()
d.lensgclm([glm, glm * 0], mmax_dlm, 2, lmaxout, lmaxout)
d.tim.reset()
d.lensgclm([glm, glm * 0], mmax_dlm, 2, lmaxout, lmaxout)
d.tim.reset()
