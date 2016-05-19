# -----------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
# -----------------------------------------------------------------------------
# Author R. Ford and A. R. Porter, STFC Daresbury Lab

''' Tests of transformations with the Dynamo 0.3 API '''

import os
import pytest
from parse import parse
from psyGen import PSyFactory, GenerationError
from transformations import TransformationError, \
    OMPParallelTrans, \
    Dynamo0p3ColourTrans, \
    Dynamo0p3OMPLoopTrans, \
    DynamoOMPParallelLoopTrans, \
    DynamoLoopFuseTrans, \
    KernelModuleInlineTrans

# The version of the API that the tests in this file
# exercise.
TEST_API = "dynamo0.3"
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_files", "dynamo0p3")


def test_colour_trans_declarations():
    '''Check that we generate the correct variable declarations when
    doing a colouring transformation. We check when distributed memory
    is both off and on '''
    # test of the colouring transformation of a single loop
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "1_single_invoke.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_type')
        schedule = invoke.schedule
        ctrans = Dynamo0p3ColourTrans()

        if dist_mem:
            index = 3
        else:
            index = 0

        # Colour the loop
        cschedule, _ = ctrans.apply(schedule.children[index])

        # Replace the original loop schedule with the transformed one
        invoke.schedule = cschedule

        # Store the results of applying this code transformation as
        # a string
        gen = str(psy.gen)
        # Fortran is not case sensitive
        gen = gen.lower()
        print gen

        # Check that we've declared the loop-related variables
        # and colour-map pointers
        assert "integer ncolour" in gen
        assert "integer colour" in gen
        assert "integer, pointer :: cmap(:,:), ncp_colour(:)" in gen


def test_colour_trans():
    '''test of the colouring transformation of a single loop. We test
    when distributed memory is both off and on'''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "1_single_invoke.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_type')
        schedule = invoke.schedule
        ctrans = Dynamo0p3ColourTrans()

        if dist_mem:
            index = 3
        else:
            index = 0

        # Colour the loop
        cschedule, _ = ctrans.apply(schedule.children[index])

        # Replace the original loop schedule with the transformed one
        invoke.schedule = cschedule

        # Store the results of applying this code transformation as
        # a string
        gen = str(psy.gen)
        # Fortran is not case sensitive
        gen = gen.lower()
        print gen
        # Check that we're calling the API to get the no. of colours
        assert "f1_proxy%vspace%get_colours(" in gen

        col_loop_idx = -1
        cell_loop_idx = -1
        for idx, line in enumerate(gen.split('\n')):
            if "do colour=1,ncolour" in line:
                col_loop_idx = idx
            if "do cell=1,ncp_colour(colour)" in line:
                cell_loop_idx = idx

        assert cell_loop_idx - col_loop_idx == 1

        # Check that we're using the colour map when getting the cell dof maps
        assert "get_cell_dofmap(cmap(colour, cell))" in gen

        if dist_mem:
            # Check that we get the right number of set_dirty halo calls in
            # the correct location
            dirty_str = (
                "      end do \n"
                "      !\n"
                "      ! set halos dirty for fields modified in the "
                "above loop\n"
                "      !\n"
                "      call f1_proxy%set_dirty()\n")
            assert dirty_str in gen
            assert gen.count("set_dirty()") == 1


def test_colour_trans_operator():
    '''test of the colouring transformation of a single loop with an
    operator. We check that the first argument is a colourmap lookup,
    not a direct cell index. We test when distributed memory is both
    off and on. '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "10_operator.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_operator_type')
        schedule = invoke.schedule
        ctrans = Dynamo0p3ColourTrans()

        if dist_mem:
            index = 3
        else:
            index = 0

        # Colour the loop
        schedule, _ = ctrans.apply(schedule.children[index])

        # Store the results of applying this code transformation as a
        # string
        gen = str(psy.gen)
        print gen

        # check the first argument is a colourmap lookup
        assert "CALL testkern_operator_code(cmap(colour, cell), nlayers" in gen


def test_colouring_not_a_loop():
    '''Test that we raise an appropriate error if we attempt to colour
    something that is not a loop. We test when distributed memory is
    on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "1_single_invoke.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_type')
        schedule = invoke.schedule
        ctrans = Dynamo0p3ColourTrans()

        # Erroneously attempt to colour the schedule rather than the loop
        with pytest.raises(TransformationError) as excinfo:
            _, _ = ctrans.apply(schedule)
        assert "Error in DynamoColour transformation" in str(excinfo.value)
        assert "The supplied node is not a loop" in str(excinfo.value)


def test_omp_name():
    ''' Test the name property of the Dynamo0p3OMPLoopTrans class '''
    olooptrans = Dynamo0p3OMPLoopTrans()
    oname = olooptrans.name
    assert oname == "Dynamo0p3OMPLoopTrans"


def test_omp_str():
    ''' Test the str method of the Dynamo0p3OMPLoopTrans class '''
    olooptrans = Dynamo0p3OMPLoopTrans()
    oname = str(olooptrans)
    assert oname == "Add an OpenMP DO directive to a Dynamo 0.3 loop"


def test_omp_not_a_loop():
    '''Test that we raise an appropriate error if we attempt to apply an
    OpenMP DO transformation to something that is not a loop. We test
    when distributed memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "1_single_invoke.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_type')
        schedule = invoke.schedule
        otrans = Dynamo0p3OMPLoopTrans()

        # Erroneously attempt to apply OpenMP to the schedule rather than
        # the loop
        with pytest.raises(TransformationError) as excinfo:
            _, _ = otrans.apply(schedule)
        assert "Error in Dynamo0p3OMPLoopTrans trans" in str(excinfo.value)
        assert "The node is not a loop" in str(excinfo.value)


def test_omp_do_not_over_cells():
    '''Test that we raise an appropriate error if we attempt to apply an
    OpenMP DO transformation to a loop that is not over cells. We test
    when distributed memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "1.4_single_invoke.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_type')
        schedule = invoke.schedule
        otrans = Dynamo0p3OMPLoopTrans()

        if dist_mem:
            index = 3
        else:
            index = 0

        with pytest.raises(TransformationError) as excinfo:
            _, _ = otrans.apply(schedule.children[index])
        assert "Error in Dynamo0p3OMPLoopTrans trans" in str(excinfo.value)
        assert "The iteration space is not 'cells'" in str(excinfo.value)


def test_omp_parallel_do_not_over_cells():
    '''Test that we raise an appropriate error if we attempt to apply an
    OpenMP PARALLEL DO transformation to a loop that is not over
    cells. We test when distributed memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "1.4_single_invoke.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_type')
        schedule = invoke.schedule
        otrans = DynamoOMPParallelLoopTrans()

        if dist_mem:
            index = 3
        else:
            index = 0

        with pytest.raises(TransformationError) as excinfo:
            _, _ = otrans.apply(schedule.children[index])
        assert "Error in DynamoOMPParallelLoopTrans tra" in str(excinfo.value)
        assert "The iteration space is not 'cells'" in str(excinfo.value)


def test_omp_parallel_not_a_loop():
    '''Test that we raise an appropriate error if we attempt to apply an
    OpenMP PARALLEL DO transformation to something that is not a
    loop. We test when distributed memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "1_single_invoke.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_type')
        schedule = invoke.schedule
        otrans = DynamoOMPParallelLoopTrans()

        # Erroneously attempt to apply OpenMP to the schedule rather than
        # the loop
        with pytest.raises(TransformationError) as excinfo:
            _, _ = otrans.apply(schedule)
        assert "Error in DynamoOMPParallelLoopTrans tra" in str(excinfo.value)
        assert "The node is not a loop" in str(excinfo.value)


def test_colour_name():
    ''' Test the name property of the Dynamo0p3ColourTrans class '''
    ctrans = Dynamo0p3ColourTrans()
    cname = ctrans.name
    assert cname == "Dynamo0p3LoopColourTrans"


def test_colour_str():
    ''' Test the str method of the Dynamo0p3ColourTrans class '''
    ctrans = Dynamo0p3ColourTrans()
    cstr = str(ctrans)
    assert cstr == "Split a Dynamo 0.3 loop into colours"


def test_omp_colour_trans():
    '''Test the OpenMP transformation applied to a coloured loop. We test
    when distributed memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "1_single_invoke.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_type')
        schedule = invoke.schedule

        ctrans = Dynamo0p3ColourTrans()
        otrans = DynamoOMPParallelLoopTrans()

        if dist_mem:
            index = 3
        else:
            index = 0

        # Colour the loop
        cschedule, _ = ctrans.apply(schedule.children[index])

        # Then apply OpenMP to the inner loop
        schedule, _ = otrans.apply(cschedule.children[index].children[0])

        invoke.schedule = schedule
        code = str(psy.gen)

        col_loop_idx = -1
        omp_idx = -1
        cell_loop_idx = -1
        for idx, line in enumerate(code.split('\n')):
            if "DO colour=1,ncolour" in line:
                col_loop_idx = idx
            if "DO cell=1,ncp_colour(colour)" in line:
                cell_loop_idx = idx
            if "!$omp parallel do" in line:
                omp_idx = idx

        assert cell_loop_idx - omp_idx == 1
        assert omp_idx - col_loop_idx == 1

        # Check that the list of private variables is correct
        assert "private(cell,map_w1,map_w2,map_w3)" in code


def test_omp_colour_orient_trans():
    '''Test the OpenMP transformation applied to a coloured loop when the
    kernel expects orientation information. We test when distributed
    memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "9_orientation.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_orientation_type')
        schedule = invoke.schedule

        ctrans = Dynamo0p3ColourTrans()
        otrans = DynamoOMPParallelLoopTrans()

        if dist_mem:
            index = 4
        else:
            index = 0

        # Colour the loop
        cschedule, _ = ctrans.apply(schedule.children[index])

        # Then apply OpenMP to the inner loop
        schedule, _ = otrans.apply(cschedule.children[index].children[0])

        invoke.schedule = schedule
        code = str(psy.gen)

        # Check that we're using the colour map when getting the orientation
        assert "get_cell_orientation(cmap(colour, cell))" in code

        # Check that the list of private variables is correct
        assert "private(cell,map_w3,map_w2,map_w0,orientation_w2)" in code


def test_omp_parallel_colouring_needed():
    '''Test that we raise an error when applying an OpenMP PARALLEL DO
    transformation to a loop that requires colouring (i.e. has a field
    with 'INC' access) but is not coloured. We test when distributed
    memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "11_any_space.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        if dist_mem:
            index = 5
        else:
            index = 0
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_any_space_1_type')
        schedule = invoke.schedule
        otrans = DynamoOMPParallelLoopTrans()
        # Apply OpenMP to the loop
        with pytest.raises(TransformationError) as excinfo:
            schedule, _ = otrans.apply(schedule.children[index])
        assert "Error in DynamoOMPParallelLoopTrans" in str(excinfo.value)
        assert "kernel has an argument with INC access" in str(excinfo.value)
        assert "Colouring is required" in str(excinfo.value)


def test_omp_colouring_needed():
    '''Test that we raise an error when applying an OpenMP DO
    transformation to a loop that requires colouring (i.e. has a field
    with 'INC' access) but is not coloured. We test when distributed
    memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "11_any_space.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        if dist_mem:
            index = 5
        else:
            index = 0
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_any_space_1_type')
        schedule = invoke.schedule

        otrans = Dynamo0p3OMPLoopTrans()
        # Apply OpenMP to the loop
        with pytest.raises(TransformationError) as excinfo:
            schedule, _ = otrans.apply(schedule.children[index])
        assert "Error in Dynamo0p3OMPLoopTrans transfo" in str(excinfo.value)
        assert "kernel has an argument with INC access" in str(excinfo.value)
        assert "Colouring is required" in str(excinfo.value)


def test_check_seq_colours_omp_parallel_do():
    '''Test that we raise an error if the user attempts to apply an OpenMP
    PARALLEL DO transformation to a loop over colours (since any such
    loop must be sequential). We test when distributed memory is on or
    off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "9_orientation.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_orientation_type')
        schedule = invoke.schedule
        if dist_mem:
            index = 4
        else:
            index = 0

        ctrans = Dynamo0p3ColourTrans()
        otrans = DynamoOMPParallelLoopTrans()

        # Colour the loop
        cschedule, _ = ctrans.apply(schedule.children[index])

        # Then erroneously attempt to apply OpenMP to the loop over
        # colours
        with pytest.raises(TransformationError) as excinfo:
            schedule, _ = otrans.apply(cschedule.children[index])
        assert "Error in DynamoOMPParallelLoopTrans" in str(excinfo.value)
        assert "requested loop is over colours" in str(excinfo.value)
        assert "must be computed serially" in str(excinfo.value)


def test_check_seq_colours_omp_do():
    '''Test that we raise an error if the user attempts to apply an OpenMP
    DO transformation to a loop over colours (since any such loop must
    be sequential). We test when distributed memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "9_orientation.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_orientation_type')
        schedule = invoke.schedule
        if dist_mem:
            index = 4
        else:
            index = 0

        ctrans = Dynamo0p3ColourTrans()
        otrans = Dynamo0p3OMPLoopTrans()

        # Colour the loop
        cschedule, _ = ctrans.apply(schedule.children[index])

        # Then erroneously attempt to apply OpenMP to the loop over
        # colours
        with pytest.raises(TransformationError) as excinfo:
            schedule, _ = otrans.apply(cschedule.children[index])
        assert "Error in Dynamo0p3OMPLoopTrans" in str(excinfo.value)
        assert "target loop is over colours" in str(excinfo.value)
        assert "must be computed serially" in str(excinfo.value)


def test_colouring_after_openmp():
    '''Test that we raise an error if the user attempts to colour a loop
    that is already within an OpenMP parallel region. We test when
    distributed memory is on or off '''
    # For this test we must use a kernel that doesn't actually require
    # colouring as otherwise PSyclone won't let us apply the OpenMP
    # transformation first!
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "9_orientation.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_orientation_type')
        schedule = invoke.schedule

        ctrans = Dynamo0p3ColourTrans()
        otrans = DynamoOMPParallelLoopTrans()

        if dist_mem:
            index = 4
        else:
            index = 0

        # Apply OpenMP to the loop
        schedule, _ = otrans.apply(schedule.children[index])

        # Now attempt to colour the loop within this OpenMP region
        with pytest.raises(TransformationError) as excinfo:
            schedule, _ = ctrans.apply(schedule.children[index].children[0])
        assert "Cannot have a loop over colours" in str(excinfo.value)
        assert "within an OpenMP parallel region" in str(excinfo.value)


def test_colouring_multi_kernel():
    '''Test that we correctly generate all the map-lookups etc.  when an
    invoke contains more than one kernel. We test when distributed
    memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4.6_multikernel_invokes.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0')
        schedule = invoke.schedule

        ctrans = Dynamo0p3ColourTrans()
        otrans = DynamoOMPParallelLoopTrans()

        if dist_mem:
            # We have halo exchanges inbetween the two loops which we
            # are going to get rid of for simplicity. Fields b, d and
            # the 3e's are already covered before the first loop so
            # can be removed
            del schedule.children[8:13]
            # f is required but can be moved before the first loop
            schedule.children.insert(6, schedule.children.pop(7))
            # In the future we will have transformations to move
            # elements around with checks for validity.
            index = 7
        else:
            index = 0

        # colour each loop
        schedule, _ = ctrans.apply(schedule.children[index])
        schedule, _ = ctrans.apply(schedule.children[index+1])

        # Apply OpenMP to each of the colour loops
        schedule, _ = otrans.apply(schedule.children[index].children[0])
        schedule, _ = otrans.apply(schedule.children[index+1].children[0])

        gen = str(psy.gen)
        print gen

        # Check that we're calling the API to get the no. of colours
        assert "a_proxy%vspace%get_colours(" in gen
        assert "f_proxy%vspace%get_colours(" in gen
        assert gen.count("_proxy%vspace%get_colours(") == 2
        assert "private(cell,map_w2,map_w3,map_w0)" in gen
        assert gen.count("private(cell,map_w2,map_w3,map_w0)") == 2


def test_omp_region_omp_do():
    '''Test that we correctly generate code for the case of a single OMP
    DO within an OMP PARALLEL region without colouring. We test when
    distributed memory is on or off '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "1_single_invoke.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0_testkern_type')
        schedule = invoke.schedule
        olooptrans = Dynamo0p3OMPLoopTrans()
        ptrans = OMPParallelTrans()

        if dist_mem:
            index = 3
        else:
            index = 0

        # Put an OMP PARALLEL around this loop
        child = schedule.children[index]
        oschedule, _ = ptrans.apply(child)

        # Put an OMP DO around this loop
        schedule, _ = olooptrans.apply(oschedule.children[index].children[0])

        # Replace the original loop schedule with the transformed one
        invoke.schedule = schedule

        # Store the results of applying this code transformation as
        # a string
        code = str(psy.gen)

        print code

        omp_do_idx = -1
        omp_para_idx = -1
        cell_loop_idx = -1
        omp_enddo_idx = -1
        if dist_mem:
            loop_str = "DO cell=1,mesh%get_last_halo_cell(1)"
        else:
            loop_str = "DO cell=1,f1_proxy%vspace%get_ncell()"
        for idx, line in enumerate(code.split('\n')):
            if loop_str in line:
                cell_loop_idx = idx
            if "!$omp do" in line:
                omp_do_idx = idx
            if "!$omp parallel default" in line:
                omp_para_idx = idx
            if "!$omp end do" in line:
                omp_enddo_idx = idx
            if "END DO" in line:
                cell_end_loop_idx = idx

        assert (omp_do_idx - omp_para_idx) == 1
        assert (cell_loop_idx - omp_do_idx) == 1
        assert (omp_enddo_idx - cell_end_loop_idx) == 1


def test_multi_kernel_single_omp_region():
    ''' Test that we correctly generate all the map-lookups etc.
    when an invoke contains more than one kernel that are all contained
    within a single OMP region for a single node (no MPI)'''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4_multikernel_invokes.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0')
        schedule = invoke.schedule

        if dist_mem:
            # We have halo exchanges inbetween the two loops which we
            # are going to get rid of for simplicity. Fields f2, m1 and m2
            # are already covered before the first loop so
            # can be removed
            del schedule.children[4:7]
            index = 3
        else:
            index = 0

        otrans = Dynamo0p3OMPLoopTrans()
        rtrans = OMPParallelTrans()

        # Apply OpenMP to each of the loops
        schedule, _ = otrans.apply(schedule.children[index])
        schedule, _ = otrans.apply(schedule.children[index+1])

        # Enclose all of these OpenMP'd loops within a single region
        schedule, _ = rtrans.apply(schedule.children[index:index+2])

        code = str(psy.gen)
        print code

        omp_do_idx = -1
        omp_end_do_idx = -1
        omp_para_idx = -1
        omp_end_para_idx = -1
        cell_loop_idx = -1
        end_do_idx = -1
        if dist_mem:
            loop_str = "DO cell=1,mesh%get_last_halo_cell(1)"
        else:
            loop_str = "DO cell=1,f1_proxy%vspace%get_ncell()"
        for idx, line in enumerate(code.split('\n')):
            if (cell_loop_idx == -1) and (loop_str in line):
                cell_loop_idx = idx
            if (omp_do_idx == -1) and ("!$omp do" in line):
                omp_do_idx = idx
            if "!$omp end do" in line:
                omp_end_do_idx = idx
            if "!$omp parallel default(shared), " +\
               "private(cell,map_w1,map_w2,map_w3)" in line:
                omp_para_idx = idx
            if "END DO" in line:
                end_do_idx = idx
            if "!$omp end parallel" in line:
                omp_end_para_idx = idx

        assert (omp_do_idx - omp_para_idx) == 1
        assert (cell_loop_idx - omp_do_idx) == 1
        assert (omp_end_para_idx - omp_end_do_idx) > 0
        assert (omp_end_do_idx - end_do_idx) == 1


def test_multi_different_kernel_omp():
    '''Test that we correctly generate the OpenMP private lists when we
    have more than one kernel of a different type (requiring a different
    private list) within an invoke. Test with and without DM.'''

    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4.7_multikernel_invokes.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0')
        schedule = invoke.schedule

        if dist_mem:
            index1 = 6
            index2 = 10
        else:
            index1 = 0
            index2 = 1

        ctrans = Dynamo0p3ColourTrans()
        otrans = DynamoOMPParallelLoopTrans()

        # colour each loop
        schedule, _ = ctrans.apply(schedule.children[index1])
        schedule, _ = ctrans.apply(schedule.children[index2])

        # Apply OpenMP to each of the colour loops
        schedule, _ = otrans.apply(schedule.children[index1].children[0])
        schedule, _ = otrans.apply(schedule.children[index2].children[0])

        code = str(psy.gen)
        print code

        assert "private(cell,map_w2,map_w3,map_w0)" in code
        assert "private(cell,map_w1,map_w2,map_w3)" in code


def test_loop_fuse_different_spaces():
    ''' Test that we raise an appropriate error if the user attempts
    to fuse loops that are on different spaces '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4.7_multikernel_invokes.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0')
        schedule = invoke.schedule

        ftrans = DynamoLoopFuseTrans()
        if dist_mem:
            # b halo exchange between loops can be removed as access
            # in both loops is read and it is already covered by the
            # first loop
            del schedule.children[7]
            # c and g halo exchange between loops can be moved before
            # 1st loop as they are not accessed in first loop
            schedule.children.insert(6, schedule.children.pop(7))
            schedule.children.insert(7, schedule.children.pop(8))
            index = 8
        else:
            index = 0

        with pytest.raises(TransformationError) as excinfo:
            _, _ = ftrans.apply(schedule.children[index],
                                schedule.children[index+1])
        assert "Error in DynamoLoopFuse transformation" in str(excinfo.value)
        assert "Cannot fuse loops" in str(excinfo.value)
        assert "over different spaces: w2 w1" in str(excinfo.value)


def test_loop_fuse_unexpected_error():
    ''' Test that we catch an unexpected error when loop fusing '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4_multikernel_invokes.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0')
        schedule = invoke.schedule

        if dist_mem:
            # remove unecessary halos between loops. At the moment we have no
            # intra halo analysis so we add them before all loops just in
            # case.
            del schedule.children[4:7]
            index = 3
        else:
            index = 0

        ftrans = DynamoLoopFuseTrans()

        # cause an unexpected error
        schedule.children[index].children = None

        with pytest.raises(TransformationError) as excinfo:
            _, _ = ftrans.apply(schedule.children[index],
                                schedule.children[index+1])
        assert 'Unexpected exception' in str(excinfo.value)


def test_loop_fuse():
    ''' Test that we are able to fuse two loops together '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4_multikernel_invokes.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0')
        schedule = invoke.schedule

        if dist_mem:
            # remove unecessary halos between loops. At the moment we have no
            # intra halo analysis so we add them before all loops just in
            # case.
            del schedule.children[4:7]
            index = 3
        else:
            index = 0

        ftrans = DynamoLoopFuseTrans()

        # fuse the loops
        schedule, _ = ftrans.apply(schedule.children[index],
                                   schedule.children[index+1])

        gen = str(psy.gen)

        cell_loop_idx = -1
        end_loop_idx = -1
        call_idx1 = -1
        call_idx2 = -1
        if dist_mem:
            loop_str = "DO cell=1,mesh%get_last_halo_cell(1)"
        else:
            loop_str = "DO cell=1,f1_proxy%vspace%get_ncell()"
        for idx, line in enumerate(gen.split('\n')):
            if loop_str in line:
                cell_loop_idx = idx
            if "CALL testkern_code" in line:
                if call_idx1 == -1:
                    call_idx1 = idx
                else:
                    call_idx2 = idx
            if "END DO" in line:
                end_loop_idx = idx

        assert cell_loop_idx != -1
        assert cell_loop_idx < call_idx1
        assert call_idx1 < call_idx2
        assert call_idx2 < end_loop_idx


def test_loop_fuse_set_dirty():
    ''' Test that we are able to fuse two loops together and produce
    the expected set_dirty() calls '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4_multikernel_invokes.f90"),
                    api=TEST_API)
    psy = PSyFactory(TEST_API).create(info)
    invoke = psy.invokes.get('invoke_0')
    schedule = invoke.schedule
    ftrans = DynamoLoopFuseTrans()
    schedule.view()
    # remove unecessary halos between loops. At the moment we have no
    # intra halo analysis so we add them before all loops just in
    # case.
    del schedule.children[4:7]
    schedule.view()
    # Fuse the loops
    schedule, _ = ftrans.apply(schedule.children[3],
                               schedule.children[4])
    schedule.view()
    gen = str(psy.gen)
    print gen
    assert gen.count("set_dirty()") == 1


def test_loop_fuse_omp():
    '''Test that we can loop-fuse two loop nests and enclose them in an
       OpenMP parallel region'''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4_multikernel_invokes.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0')
        schedule = invoke.schedule

        if dist_mem:
            # remove unecessary halos between loops. At the moment we have no
            # intra halo analysis so we add them before all loops just in
            # case.
            del schedule.children[4:7]
            index = 3
        else:
            index = 0

        ftrans = DynamoLoopFuseTrans()
        otrans = DynamoOMPParallelLoopTrans()

        schedule, _ = ftrans.apply(schedule.children[index],
                                   schedule.children[index+1])

        schedule, _ = otrans.apply(schedule.children[index])

        code = str(psy.gen)
        print code

        # Check generated code
        omp_para_idx = -1
        omp_endpara_idx = -1
        cell_do_idx = -1
        cell_enddo_idx = -1
        call1_idx = -1
        call2_idx = -1
        if dist_mem:
            loop_str = "DO cell=1,mesh%get_last_halo_cell(1)"
        else:
            loop_str = "DO cell=1,f1_proxy%vspace%get_ncell()"
        for idx, line in enumerate(code.split('\n')):
            if loop_str in line:
                cell_do_idx = idx
            if "!$omp parallel do default(shared), " +\
               "private(cell,map_w1,map_w2,map_w3), schedule(static)" in line:
                omp_para_idx = idx
            if "CALL testkern_code" in line:
                if call1_idx == -1:
                    call1_idx = idx
                else:
                    call2_idx = idx
            if "END DO" in line:
                cell_enddo_idx = idx
            if "!$omp end parallel do" in line:
                omp_endpara_idx = idx

        assert cell_do_idx - omp_para_idx == 1
        assert call1_idx > cell_do_idx
        assert call2_idx > call1_idx
        assert cell_enddo_idx > call2_idx
        assert omp_endpara_idx - cell_enddo_idx == 1


def test_fuse_colour_loops():
    '''Test that we can fuse colour loops , enclose them in an OpenMP
    parallel region and preceed each by an OpenMP PARALLEL DO for
    both sequential and distributed-memory code '''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4.6_multikernel_invokes.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0')
        schedule = invoke.schedule

        ctrans = Dynamo0p3ColourTrans()
        otrans = Dynamo0p3OMPLoopTrans()
        rtrans = OMPParallelTrans()
        ftrans = DynamoLoopFuseTrans()

        if dist_mem:
            # We have halo exchanges inbetween the two loops which we
            # are going to get rid of for simplicity. Fields b, d and
            # the 3e's are already covered before the first loop so
            # can be removed
            del schedule.children[8:13]
            # f is required but can be moved before the first loop
            schedule.children.insert(6, schedule.children.pop(7))
            # In the future we will have transformations to move
            # elements around with checks for validity.
            index = 7
        else:
            index = 0

        # colour each loop
        schedule, _ = ctrans.apply(schedule.children[index])
        schedule, _ = ctrans.apply(schedule.children[index+1])

        # fuse the sequential colours loop
        schedule, _ = ftrans.apply(schedule.children[index],
                                   schedule.children[index+1])

        # Enclose the colour loops within an OMP parallel region
        schedule, _ = rtrans.apply(schedule.children[index].children)

        # Put an OMP DO around each of the colour loops
        for loop in schedule.children[index].children[0].children:
            schedule, _ = otrans.apply(loop)

        code = str(psy.gen)
        print code

        # Test that the generated code is as expected
        omp_para_idx = -1
        omp_do_idx1 = -1
        omp_do_idx2 = -1
        cell_loop_idx1 = -1
        cell_loop_idx2 = -1
        end_loop_idx1 = -1
        end_loop_idx2 = -1
        end_loop_idx3 = -1
        call_idx1 = -1
        call_idx2 = -1
        for idx, line in enumerate(code.split('\n')):
            if "END DO" in line:
                if end_loop_idx1 == -1:
                    end_loop_idx1 = idx
                elif end_loop_idx2 == -1:
                    end_loop_idx2 = idx
                else:
                    end_loop_idx3 = idx
            if "DO cell=1,ncp_colour(colour)" in line:
                if cell_loop_idx1 == -1:
                    cell_loop_idx1 = idx
                else:
                    cell_loop_idx2 = idx
            if "DO colour=1,ncolour" in line:
                col_loop_idx = idx
            if "CALL ru_code(nlayers," in line:
                if call_idx1 == -1:
                    call_idx1 = idx
                else:
                    call_idx2 = idx
            if "!$omp parallel default(shared), " +\
               "private(cell,map_w2,map_w3,map_w0)" in line:
                omp_para_idx = idx
            if "!$omp do schedule(static)" in line:
                if omp_do_idx1 == -1:
                    omp_do_idx1 = idx
                else:
                    omp_do_idx2 = idx

        assert (omp_para_idx - col_loop_idx) == 1
        assert (omp_do_idx1 - omp_para_idx) == 1
        assert (cell_loop_idx1 - omp_do_idx1) == 1
        assert (cell_loop_idx2 - omp_do_idx2) == 1
        assert (end_loop_idx3 - end_loop_idx2) == 3
        assert call_idx2 > call_idx1
        assert call_idx1 < end_loop_idx1
        assert call_idx2 < end_loop_idx2

        if dist_mem:
            set_dirty_str = (
                "      ! Set halos dirty for fields modified in the above "
                "loop\n"
                "      !\n"
                "      CALL a_proxy%set_dirty()\n"
                "      CALL f_proxy%set_dirty()\n")
            assert set_dirty_str in code
            assert code.count("set_dirty()") == 2


def test_omp_parallel_and_halo_exchange_error():
    '''Tests that we raise an error if we try to apply an omp parallel
    transformation to a list containing halo_exchange calls. If this is
    allowed then it is likely that we will get incorrect results, or that
    the code will fail. Fixing this problem is the subject of ticket #526'''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4_multikernel_invokes.f90"),
                    api=TEST_API)
    psy = PSyFactory(TEST_API, distributed_memory=True).create(info)
    invoke = psy.invokes.get('invoke_0')
    schedule = invoke.schedule

    otrans = Dynamo0p3OMPLoopTrans()
    rtrans = OMPParallelTrans()

    # Apply OpenMP to each of the loops
    schedule, _ = otrans.apply(schedule.children[3])
    schedule, _ = otrans.apply(schedule.children[7])

    # Enclose the invoke code within a single region
    with pytest.raises(TransformationError) as excinfo:
        schedule, _ = rtrans.apply(schedule.children)
    assert "A halo exchange within a parallel region is not supported" \
        in str(excinfo.value)


def test_module_inline():
    '''Tests that correct results are obtained when a kernel is inlined
    into the psy-layer in the dynamo0.3 API. More in-depth tests can be
    found in the gocean1p0_transformations.py file'''
    _, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "4.6_multikernel_invokes.f90"),
                    api=TEST_API)
    for dist_mem in [False, True]:
        psy = PSyFactory(TEST_API, distributed_memory=dist_mem).create(info)
        invoke = psy.invokes.get('invoke_0')
        schedule = invoke.schedule
        if dist_mem:
            schedule.view()
            index = 13
        else:
            index = 1
        kern_call = schedule.children[index].children[0]
        inline_trans = KernelModuleInlineTrans()
        schedule, _ = inline_trans.apply(kern_call)
        gen = str(psy.gen)
        # check that the subroutine has been inlined
        assert 'SUBROUTINE ru_code()' in gen
        # check that the associated psy "use" does not exist
        assert 'USE ru_kernel_mod, only : ru_code' not in gen


def test_scalar_sum_and_OpenMP_unsupported():
    ''' Test that we fail if OpenMP and global sums are specified '''
    _, info = parse(os.path.join(BASE_PATH, "16.3_real_scalar_sum.f90"),
                    api=TEST_API, distributed_memory=False)
    psy = PSyFactory(TEST_API, distributed_memory=False).create(info)
    invoke = psy.invokes.invoke_list[0]
    schedule = invoke.schedule
    otrans = DynamoOMPParallelLoopTrans()
    # Apply OpenMP parallelisation to the loop
    schedule, _ = otrans.apply(schedule.children[0])
    invoke.schedule = schedule
    # We should get an error when we try to generate the code
    with pytest.raises(GenerationError) as excinfo:
        _ = str(psy.gen)
    assert "OpenMP reductions are not yet supported" in str(excinfo.value)
