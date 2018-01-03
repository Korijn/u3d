# vtkU3DExporter

Build and test instructions:

    conda env create
    conda activate vtku3dexporter
    mkdir build
    cd build
    ccmake ..
    make
    PYTHONPATH=$(pwd) python ../test.py

Please see `test.py` for an example of how to set a name for
a vtkActor to make it show up in the u3d file.

