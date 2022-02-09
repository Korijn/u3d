project(vtku3dexporter)
cmake_minimum_required(VERSION 3.5)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(WRAP_PYTHON "Build Python wrappers" ON)

# Use INSTALL_PYTHON_MODULE_DIR to manipulate where your lib and
# bin files will go. Useful for building wheels.
if(NOT INSTALL_PYTHON_MODULE_DIR)
    set(INSTALL_PYTHON_MODULE_DIR ".")
endif()

if(NOT LIB_DESTINATION)
    set(LIB_DESTINATION "${INSTALL_PYTHON_MODULE_DIR}")
endif()
if(NOT BIN_DESTINATION)
    set(BIN_DESTINATION "${INSTALL_PYTHON_MODULE_DIR}/bin")
endif()
if(NOT INCLUDE_DESTINATION)
    set(INCLUDE_DESTINATION "include/${PROJECT_NAME}")
endif()

message( STATUS "CMAKE_INSTALL_PREFIX:    " ${CMAKE_INSTALL_PREFIX} )
message( STATUS "LIB_DESTINATION:         " ${LIB_DESTINATION} )

# Include the source directory to make sure that out-of-source
# builds can find the proper headers.
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# Find U3D
find_library(U3D_LIB NAMES IDTF)
if(NOT U3D_LIB)
    message(FATAL_ERROR "Could not find U3D library")
endif()
message(STATUS "Found U3D library at: ${U3D_LIB}")

find_path(U3D_INCLUDE_DIR u3d/SceneConverterLib.h)
if(NOT U3D_INCLUDE_DIR)
    message(FATAL_ERROR "Could not find U3D include dir")
endif()
message(STATUS "Found U3D include dir: ${U3D_INCLUDE_DIR}")
include_directories(${U3D_INCLUDE_DIR}/u3d)

# Find VTK
find_package(VTK REQUIRED
    vtkIOExport
    vtkRenderingCore
    vtkWrappingPythonCore)
message(STATUS "Found VTK libraries: ${VTK_LIBRARIES}")
message(STATUS "Found UseVTK.cmake: ${VTK_USE_FILE}")
include(${VTK_USE_FILE})
set(VTK_MODULES_USED vtkIOExport)

# Remove the unexisting libpython file from VTK_LIBRARIES
# Otherwise, build will fail
list(FILTER VTK_LIBRARIES EXCLUDE REGEX libpython|\.lib)
message(STATUS "Filtered VTK libraries: ${VTK_LIBRARIES}")

# Create vtkU3DExporter shared library
set(LIBS ${VTK_LIBRARIES} ${U3D_LIB})
set(EXPORTER_SRC vtkU3DExporter.cxx vtkU3DExporter.h)
add_library(${PROJECT_NAME} SHARED ${EXPORTER_SRC})
target_link_libraries(${PROJECT_NAME}
    ${LIBS})
if(WIN32)
    target_link_libraries(${PROJECT_NAME}
        winmm)
endif()
install(TARGETS ${PROJECT_NAME}
    RUNTIME DESTINATION ${BIN_DESTINATION}
    ARCHIVE DESTINATION ${LIB_DESTINATION}
    LIBRARY DESTINATION ${LIB_DESTINATION}
)
install(DIRECTORY .
    DESTINATION ${INCLUDE_DESTINATION}
    FILES_MATCHING PATTERN "*.h"
    PATTERN "CMake" EXCLUDE
)
message(STATUS "Added library: " "${PROJECT_NAME}")

if(WRAP_PYTHON)
    # Find Python
    find_package(PythonLibs REQUIRED)
    message(STATUS "Found Python include dir: " ${PYTHON_INCLUDE_DIRS} )
    message(STATUS "Found Python library: " ${PYTHON_LIBRARIES} )
    include_directories("${PYTHON_INCLUDE_DIRS}")

    # Generate VTK Python wrappers
    include(vtkWrapPython)
    # despite the name, this works for any Python version (tested up to 3.5)
    VTK_WRAP_PYTHON3(${PROJECT_NAME}Python PYTHON_SRCS "${EXPORTER_SRC}")
    message(STATUS "Generated Python wrappers: " "${PYTHON_SRCS}")

    # Create PythonD library (brings everything together)
    add_library("${PROJECT_NAME}PythonD" ${PYTHON_SRCS} "${EXPORTER_SRC}")
    set_target_properties("${PROJECT_NAME}PythonD" PROPERTIES POSITION_INDEPENDENT_CODE ON)
    if(WIN32)
        target_link_libraries("${PROJECT_NAME}PythonD"
            winmm)
    endif()
    target_link_libraries("${PROJECT_NAME}PythonD"
        ${LIBS}
        vtkWrappingPythonCore
        ${VTK_PYTHON_LIBRARIES})
    install(TARGETS "${PROJECT_NAME}PythonD"
        RUNTIME DESTINATION ${BIN_DESTINATION}
        ARCHIVE DESTINATION ${LIB_DESTINATION}
        LIBRARY DESTINATION ${LIB_DESTINATION}
    )

    # Create Python library (exposes to Python through a pyd)
    add_library("${PROJECT_NAME}Python" MODULE "${PROJECT_NAME}PythonInit.cxx" "${PROJECT_NAME}PythonInitImpl.cxx")
    # collect the used pythonD libs in VTK_PYTHOND_LIBS
    set(VTK_PYTHOND_LIBS)
    foreach(TMP_LIB ${VTK_MODULES_USED})
        set(VTK_PYTHOND_LIBS ${VTK_PYTHOND_LIBS} ${TMP_LIB}PythonD)
    endforeach()

    # link 'em up
    # On linux, don't link the PYTHON_LIBRARIES
    if(UNIX AND NOT APPLE)
        target_link_libraries("${PROJECT_NAME}Python"
            "${PROJECT_NAME}PythonD"
            ${VTK_PYTHOND_LIBS})
    else()
        target_link_libraries("${PROJECT_NAME}Python"
            "${PROJECT_NAME}PythonD"
            ${PYTHON_LIBRARIES}
            ${VTK_PYTHOND_LIBS})
    endif()
    # prettify the output
    set_target_properties("${PROJECT_NAME}Python" PROPERTIES PREFIX "")
    if(WIN32 AND NOT CYGWIN)
        set_target_properties("${PROJECT_NAME}Python" PROPERTIES SUFFIX ".pyd")
    endif()
    # install command for the pyd
    install(TARGETS "${PROJECT_NAME}Python"
        LIBRARY DESTINATION "${INSTALL_PYTHON_MODULE_DIR}/${PROJECT_NAME}"
    )
    # install __init__.py to make it importable
    file(WRITE __init__.py "\
from __future__ import absolute_import\n\
# first importing vtk solves some import problems\n\
import vtk\n\
\n\
try:\n\
    # use relative import for installed modules\n\
    from .${PROJECT_NAME}Python import *\n\
except ImportError:\n\
    # during build and testing, the modules will be elsewhere,\n\
    # e.g. in lib directory or Release/Debug config directories\n\
    from ${PROJECT_NAME}Python import *\n\
")
    install(FILES __init__.py
        DESTINATION "${INSTALL_PYTHON_MODULE_DIR}/${PROJECT_NAME}"
    )


endif()
