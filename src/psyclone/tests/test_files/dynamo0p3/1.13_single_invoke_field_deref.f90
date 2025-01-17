!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown,
! Met Office and NERC 2014.
! However, it has been created with the help of the GungHo Consortium,
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
! Author R. Ford STFC Daresbury Lab

program single_invoke

  ! Description: single function specified in an invoke call
  use testkern, only: testkern_type
  use inf,      only: field_type, estate_type
  implicit none
  type(field_type) :: f1,m1
  type(estate_type) :: est
  real(r_def) :: a

  call invoke( testkern_type(a,f1,est%f2,m1,est%m2) )

end program single_invoke
