! Copyright (c) 2017-2019, Science and Technology Facilities Council
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
! THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
! AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
! IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
! DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
! FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
! DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
! SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
! CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
! OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
! OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

! Author R. Ford STFC Daresbury Lab

module testkern_multi_anyw2_mod
  !
  type, extends(kernel_type) :: testkern_multi_anyw2_type
     type(arg_type), dimension(3) :: meta_args = &
          (/ arg_type(gh_field,gh_write,any_w2), &
             arg_type(gh_field,gh_read, any_w2), &
             arg_type(gh_field,gh_read, any_w2)  &
           /)
     integer :: iterates_over = cells
   contains
     procedure, nopass :: code => testkern_multi_anyw2_code
  end type testkern_multi_anyw2_type
  !
contains
  !
  subroutine testkern_multi_anyw2_code(nlayers, field_1_any_w2, field_2_any_w2, field_3_any_w2, ndf_any_w2, undf_any_w2, map_any_w2)
      USE constants_mod, ONLY: r_def
      IMPLICIT NONE
      INTEGER, intent(in) :: nlayers
      INTEGER, intent(in) :: ndf_any_w2
      INTEGER, intent(in), dimension(ndf_any_w2) :: map_any_w2
      INTEGER, intent(in) :: undf_any_w2
      REAL(KIND=r_def), intent(out), dimension(undf_any_w2) :: field_1_any_w2
      REAL(KIND=r_def), intent(in), dimension(undf_any_w2) :: field_2_any_w2
      REAL(KIND=r_def), intent(in), dimension(undf_any_w2) :: field_3_any_w2
  end subroutine testkern_multi_anyw2_code
  !
end module testkern_multi_anyw2_mod
