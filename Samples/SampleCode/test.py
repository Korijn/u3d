import os
import tempfile
import vtk
from vtk.util.keys import StringKey
from vtk.vtkCommonCore import vtkInformationIterator
import vtku3dexporter


def write_u3d(file_path, actors):
    render_window = vtk.vtkRenderWindow()
    render_window.OffScreenRenderingOn()
    renderer = vtk.vtkRenderer()
    render_window.AddRenderer(renderer)

    for actor in actors:
        renderer.AddActor(actor)

    renderer.ResetCamera()

    u3d_exporter = vtku3dexporter.vtkU3DExporter()
    u3d_exporter.SetFileName(file_path)
    u3d_exporter.SetInput(render_window)
    u3d_exporter.Write()


def create_actor_from_stl(path):
    assert os.path.exists(path)
    reader = vtk.vtkSTLReader()
    reader.SetFileName(path)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor


def set_name_for_actor(name, actor):
    """
    Sets the name in the PropertyKeys of a vtkActor
    """
    key = StringKey.MakeKey("MeshName", "root")
    i = vtk.vtkInformation()
    i.Set(key, name)
    actor.SetPropertyKeys(i)


def get_name_for_actor(actor, keyName="MeshName"):
    """
    Returns the name from the PropertyKeys of a vtkActor
    """
    information = actor.GetPropertyKeys()
    if information is None:
        return None

    iterator = vtkInformationIterator()
    iterator.SetInformation(information)
    iterator.InitTraversal()
    while (not iterator.IsDoneWithTraversal()):
        key = iterator.GetCurrentKey()
        if key.GetName() == keyName:
            return information.Get(key)
            break
        iterator.GoToNextItem()
    return None


if __name__ == "__main__":
    # Create cube
    cube = vtk.vtkCubeSource()

    # Mapper
    cubeMapper = vtk.vtkPolyDataMapper()
    cubeMapper.SetInputData(cube.GetOutput())

    # Actor
    cubeActor = vtk.vtkActor()
    cubeActor.SetMapper(cubeMapper)
    assert get_name_for_actor(cubeActor) is None

    stlPath = os.path.join(os.path.dirname(__file__), "test.stl")
    stlActor = create_actor_from_stl(stlPath)
    set_name_for_actor("a9p", stlActor)
    assert get_name_for_actor(stlActor) == "a9p"

    # Get the file_path and delete if it already exists
    dir_path = tempfile.gettempdir()
    filename = "test_report"
    file_path = os.path.join(dir_path, filename)

    if os.path.exists("{}.u3d".format(file_path)):
        print("Removing old file...")
        os.remove("{}.u3d".format(file_path))

    # Write the u3d file to the file path
    print("Writing file to {}.u3d".format(file_path))
    write_u3d(file_path, [cubeActor, stlActor])

    print("Testing that u3d was generated...")
    # Check that we have successfully created a U3D file
    if not os.path.exists("{}.u3d".format(file_path)):
        raise Exception("Failed to create the U3D file")

    print("Testing that the name of the actor is in the logs...")
    assert " a9p\n" in open("{}.u3d.DebugInfo.txt".format(file_path)).read()

    print("Test successful")
