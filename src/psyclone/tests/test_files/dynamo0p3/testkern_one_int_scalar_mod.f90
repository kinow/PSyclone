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
!-------------------------------------------------------------------------------
! Author R. Ford STFC Daresbury Lab, C.M. Maynard Met Office/University of Reading

module testkern_one_int_scalar_mod
  use argument_mod
  use kernel_mod
  use constants_mod
  
  type, public, extends(kernel_type) :: testkern_one_int_scalar_type
     private
     type(arg_type), dimension(5) :: meta_args = &
          (/ arg_type(gh_field,   gh_write,w1), &
             arg_type(gh_integer, gh_read    ), &
             arg_type(gh_field,   gh_read, w2), &
             arg_type(gh_field,   gh_read, w2), &
             arg_type(gh_field,   gh_read, w3)  &
           /)
     integer :: iterates_over = cells
   contains
     procedure, public, nopass :: code => testkern_code
  end type testkern_one_int_scalar_type
contains

  subroutine testkern_code(nlayers, afield1, iflag, afield2, afield3, afield4, &
       ndf_w1, undf_w1, map_w1, ndf_w2, undf_w2, map_w2,                       &
       ndf_w3, undf_w3, map_w3 )
    implicit none
    integer(kind=i_def),               intent(in)  :: nlayers 
    real(kind=r_def), dimension(:),    intent(out) :: afield1
    integer(kind=i_def),               intent(in)  :: iflag
    real(kind=r_def), dimension(:),    intent(in)  :: afield2, afield3, afield4
    integer(kind=i_def),               intent(in)  :: ndf_w1, undf_w1
    integer(kind=i_def), dimension(:), intent(in)  :: map_w1
    integer(kind=i_def),               intent(in)  :: ndf_w2, undf_w2
    integer(kind=i_def), dimension(:), intent(in)  :: map_w2
    integer(kind=i_def),               intent(in)  :: ndf_w3, undf_w3
    integer(kind=i_def), dimension(:), intent(in)  :: map_w3    
  end subroutine testkern_code

end module testkern_one_int_scalar_mod
