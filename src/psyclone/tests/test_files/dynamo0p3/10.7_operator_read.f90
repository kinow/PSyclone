! -----------------------------------------------------------------------------
! BSD 3-Clause License
!
! Copyright (c) 2017-2019, Science and Technology Facilities Council
! All rights reserved.
!
! Redistribution and use in source and binary forms, with or without
! modification, are permitted provided that the following conditions are met:
!
! * Redistributions of source code must retain the above copyright notice, this
!   list of conditions and the following disclaimer.
!
! * Redistributions in binary form must reproduce the above copyright notice,
!   this list of conditions and the following disclaimer in the documentation
!   and/or other materials provided with the distribution.
!
! * Neither the name of the copyright holder nor the names of its
!   contributors may be used to endorse or promote products derived from
!   this software without specific prior written permission.
!
! THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
! "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
! LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
! FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
! COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
! INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
! BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
! LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
! CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
! LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
! ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
! POSSIBILITY OF SUCH DAMAGE.
! -----------------------------------------------------------------------------
! Authors R. W. Ford and A. R. Porter, STFC Daresbury Lab
! Modified I. Kavcic, Met Office

program operator_example

  use field_mod,                  only : field_type
  use function_space_mod,         only : function_space_type, W0
  use quadrature_mod,             only : quadrature_type, QR3
  use operator_mod,               only : operator_type
  use testkern_operator_read_mod, only : testkern_operator_read_type

  type(quadrature_type), pointer :: qr => null()
  type(field_type)               :: chi(3)
  type(operator_type)            :: mm_w0
  type(function_space_type)      :: fs
  real(r_def)                    :: a

  a = 1.0_r_def
  mm_w0 = operator_type(fs%get_instance(W0),fs%get_instance(W0))
  qr => qr%get_instance(QR3,9,3)

  call invoke(testkern_operator_read_type(mm_w0, chi, a, qr))

end program operator_example
