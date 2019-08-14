! -----------------------------------------------------------------------------
! BSD 3-Clause License
!
! Copyright (c) 2019, Science and Technology Facilities Council
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
! Author I. Kavcic Met Office

module testkern_anyd_disc_only_mod

  use argument_mod
  use kernel_mod
  use constants_mod

  implicit none

  ! Description: discontinuous field readwriter (any_discontinuous_space_1)
  ! and reader (w3)
  type, extends(kernel_type) :: testkern_anyd_disc_only_type
     type(arg_type), dimension(2) :: meta_args =                          &
          (/ arg_type(gh_field, gh_readwrite, any_discontinuous_space_1), &
             arg_type(gh_field, gh_read,      w3)                         &
           /)
     integer :: iterates_over = cells
   contains
     procedure, nopass :: code => testkern_anyd_disc_only_code
  end type testkern_anyd_disc_only_type

contains

  subroutine testkern_anyd_disc_only_code(nlayers,          &
                                          field1, field2,   &
                                          ndf_anydspace_1,  &
                                          undf_anydspace_1, &
                                          map_anydspace_1,  &
                                          ndf_w3, undf_w3, map_w3)


    implicit none

    integer(kind=i_def), intent(in) :: nlayers
    integer(kind=i_def), intent(in) :: ndf_anydspace_1
    integer(kind=i_def), intent(in) :: ndf_w3
    integer(kind=i_def), intent(in) :: undf_anydspace_1, undf_w3
    integer(kind=i_def), intent(in), dimension(ndf_anydspace_1) :: map_anydspace_1
    integer(kind=i_def), intent(in), dimension(ndf_w3)          :: map_w3
    real(kind=r_def), intent(inout), dimension(undf_anydspace_1) :: field1
    real(kind=r_def), intent(in), dimension(undf_w3)             :: field2

  end subroutine testkern_anyd_disc_only_code

end module testkern_anyd_disc_only_mod