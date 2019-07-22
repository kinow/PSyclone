
module profile_mod
  use iso_c_binding
  implicit none

  private
  
  type, public :: ProfileData
     character(:), allocatable :: module_name
     character(:), allocatable :: region_name
  end type ProfileData

  logical :: has_been_initialised = .false.

  integer :: col(7) = [ Z'0000ff00', Z'000000ff', Z'00ffff00', &
                        Z'00ff00ff', Z'0000ffff', Z'00ff0000', &
                        Z'00ffffff']
  character(len=256), target :: tempName

  type, bind(C):: nvtxEventAttributes
     integer(C_INT16_T):: version=1
     integer(C_INT16_T):: size=48 !
     integer(C_INT):: category=0
     integer(C_INT):: colorType=1 ! NVTX_COLOR_ARGB = 1
     integer(C_INT):: color
     integer(C_INT):: payloadType=0 ! NVTX_PAYLOAD_UNKNOWN = 0
     integer(C_INT):: reserved0
     integer(C_INT64_T):: payload   ! union uint,int,double
     integer(C_INT):: messageType=1  ! NVTX_MESSAGE_TYPE_ASCII     = 1 
     type(C_PTR):: message  ! ascii char
  end type nvtxEventAttributes

  interface nvtxRangePush
     ! push range with custom label and standard color
     subroutine nvtxRangePushA(name) bind(C, name='nvtxRangePushA')
       use iso_c_binding
       character(kind=C_CHAR, len=1) :: name
     end subroutine nvtxRangePushA

     ! push range with custom label and custom color
     subroutine nvtxRangePushEx(event) bind(C, name='nvtxRangePushEx')
       use iso_c_binding
       import:: nvtxEventAttributes
       type(nvtxEventAttributes):: event
     end subroutine nvtxRangePushEx
  end interface nvtxRangePush

  interface nvtxRangePop
     subroutine nvtxRangePop() bind(C, name='nvtxRangePop')
     end subroutine nvtxRangePop
  end interface nvtxRangePop

  public ProfileInit, ProfileFinalise, ProfileStart, ProfileEnd

contains
  ! ---------------------------------------------------------------------------
  !> An optional initialisation subroutine. It is not called directly from
  !> any PSyclone created code, but for most existing profiling libraries the
  !> application will have to call it. In this dummy library it is called once
  !> from ProfileStart.
  subroutine ProfileInit()
    implicit none
    print *,"ProfileInit called"
    has_been_initialised = .true.
  end subroutine ProfileInit

  ! ---------------------------------------------------------------------------
  !> Starts a profiling area. The module and region name can be used to create
  !> a unique name for each region.
  !> Parameters: 
  !> module_name:  Name of the module in which the region is
  !> region_name:  Name of the region (could be name of an invoke, or
  !>               subroutine name).
  !> profile_data: Persistent data used by the profiling library.
  subroutine ProfileStart(module_name, region_name, profile_data)
    implicit none

    character*(*) :: module_name, region_name
    type(ProfileData) :: profile_data

    call nvtxStartRange(TRIM(module_name)//":"//region_name)
    
  end subroutine ProfileStart

  ! ---------------------------------------------------------------------------
  !> Ends a profiling area. It takes a ProfileData type that corresponds to
  !> to the ProfileStart call.
  !> profile_data: Persistent data used by the profiling library.
  ! 
  subroutine ProfileEnd(profile_data)
    implicit none
    type(ProfileData) :: profile_data
    
    call nvtxEndRange()
    
  end subroutine ProfileEnd

  ! ---------------------------------------------------------------------------
  !> The finalise function prints the results. This subroutine must be called
  !> for most profiling libraries, otherwise no results will be produced.
  subroutine ProfileFinalise()
    implicit none
    has_been_initialised = .false.
  end subroutine ProfileFinalise

subroutine nvtxStartRange(name, id)
  character(kind=c_char, len=*), intent(in) :: name
  integer, optional, intent(in) :: id
  type(nvtxEventAttributes):: event

  tempName=trim(name)//c_null_char

  if ( .not. present(id)) then
    call nvtxRangePush(tempName)
  else
    event%color=col(mod(id,7)+1)
    event%message=c_loc(tempName)
    call nvtxRangePushEx(event)
  end if
end subroutine

subroutine nvtxEndRange
  call nvtxRangePop
end subroutine

end module profile_mod
