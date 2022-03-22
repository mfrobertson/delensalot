C     -*- fortran -*-
C     This file is autogenerated with f2py (version:2)
C     It contains Fortran 77 wrappers to fortran functions.

      subroutine f2pywrapcubicfilter (cubicfilterf2pywrap, x, c0, 
     &c1, c2, c3)
      external cubicfilter
      double precision x
      double precision c0
      double precision c1
      double precision c2
      double precision c3
      double precision cubicfilterf2pywrap, cubicfilter
      cubicfilterf2pywrap = cubicfilter(x, c0, c1, c2, c3)
      end


      subroutine f2pywraptex2d (tex2df2pywrap, ftl_map, i, j, nx, 
     &ny)
      external tex2d
      integer i
      integer j
      integer nx
      integer ny
      double precision ftl_map(ny,nx)
      double precision tex2df2pywrap, tex2d
      tex2df2pywrap = tex2d(ftl_map, i, j, nx, ny)
      end


      subroutine f2pywrapeval (evalf2pywrap, ftl_map, fx, fy, nx, 
     &ny)
      external eval
      double precision fx
      double precision fy
      integer nx
      integer ny
      double precision ftl_map(ny,nx)
      double precision evalf2pywrap, eval
      evalf2pywrap = eval(ftl_map, fx, fy, nx, ny)
      end


      subroutine f2pywrapeval_unchkd (eval_unchkdf2pywrap, ftl_map
     &, fx, fy, nx, ny)
      external eval_unchkd
      double precision fx
      double precision fy
      integer nx
      integer ny
      double precision ftl_map(ny,nx)
      double precision eval_unchkdf2pywrap, eval_unchkd
      eval_unchkdf2pywrap = eval_unchkd(ftl_map, fx, fy, nx, ny)
      end

