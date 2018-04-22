import FreeCAD, FreeCADGui, Draft, ImportGui 
if FreeCAD.GuiUp:
    from PySide import QtCore, QtGui
import re
import math

import os,sys

import __builtin__

from collections import namedtuple

Mesh = namedtuple('Mesh', ['points', 'faces', 'color', 'transp'])

#return all objects in Active Document
def getAllObjects():
    return FreeCAD.ActiveDocument.Objects
    
def removeAllButFirst():
    objs = getAllObjects()[1:]
    
    for i in objs:
        FreeCAD.ActiveDocument.removeObject(i.Name)
        
def fuseAll(App, Gui, objects = None):
    docName = App.ActiveDocument.Name
    
    if not objects:
        objects = getAllObjects()
    
    say("Fusing",len(objects),"objects")
    
    while len(objects) > 1:
        say("Fusing:",objects[0].Name,objects[1].Name)
        fuseObjects(App, Gui, docName, objects[0].Name, objects[1].Name)
        objects = getAllObjects()
        
def fuseObjects(App, Gui,
                           docName, part1, part2, name=None):

    # Fuse two objects
    App.ActiveDocument=None
    Gui.ActiveDocument=None
    App.setActiveDocument(docName)
    App.ActiveDocument=App.getDocument(docName)
    Gui.ActiveDocument=Gui.getDocument(docName)
    App.activeDocument().addObject("Part::MultiFuse","Fusion")
    App.activeDocument().Fusion.Shapes = [App.ActiveDocument.getObject(part1), App.ActiveDocument.getObject(part2)]
    Gui.ActiveDocument.Fusion.ShapeColor=Gui.ActiveDocument.getObject(part1).ShapeColor
    Gui.ActiveDocument.Fusion.DisplayMode=Gui.ActiveDocument.getObject(part1).DisplayMode
    App.ActiveDocument.recompute()

    App.ActiveDocument.addObject('Part::Feature','Fusion').Shape=App.ActiveDocument.Fusion.Shape
    
    if not name:
        name = docName
        
    App.ActiveDocument.ActiveObject.Label=name

    Gui.ActiveDocument.ActiveObject.ShapeColor=Gui.ActiveDocument.Fusion.ShapeColor
    Gui.ActiveDocument.ActiveObject.LineColor=Gui.ActiveDocument.Fusion.LineColor
    Gui.ActiveDocument.ActiveObject.PointColor=Gui.ActiveDocument.Fusion.PointColor
    Gui.ActiveDocument.ActiveObject.DiffuseColor=Gui.ActiveDocument.Fusion.DiffuseColor
    App.ActiveDocument.recompute()

    ## ## TBD refine Shape to reduce size maui
    ## App.ActiveDocument.addObject('Part::Feature','Fusion').Shape=App.ActiveDocument.Fusion.Shape.removeSplitter()
    ## App.ActiveDocument.ActiveObject.Label=App.ActiveDocument.Fusion.Label
    ## Gui.ActiveDocument.Fusion.hide()
    ##
    ## Gui.ActiveDocument.ActiveObject.ShapeColor=Gui.ActiveDocument.Fusion.ShapeColor
    ## Gui.ActiveDocument.ActiveObject.LineColor=Gui.ActiveDocument.Fusion.LineColor
    ## Gui.ActiveDocument.ActiveObject.PointColor=Gui.ActiveDocument.Fusion.PointColor
    ## Gui.ActiveDocument.ActiveObject.DiffuseColor=Gui.ActiveDocument.Fusion.DiffuseColor
    ## App.ActiveDocument.recompute()
    ## App.ActiveDocument.ActiveObject.Label=docName
    #######################################################
    # Remove the part1 part2 objects
    App.getDocument(docName).removeObject(part1)
    App.getDocument(docName).removeObject(part2)

    # Remove the fusion itself
    App.getDocument(docName).removeObject("Fusion")
    ## App.getDocument(docName).removeObject("Fusion001")

    return 0   
    
#return all selected objects in Active Document
def getSelectedObjects():
    return [selected.Object for selected in FreeCADGui.Selection.getSelectionEx()]
    
#return combined meshes of all objects in Active Document
def getAllMeshes():
    meshes = []
    
    for obj in getAllObjects():
        meshes += objectToMesh(obj)
        
    return meshes

#Export a VRML model file with the selected meshes
def exportVRMLMeshes(meshes, filepath):
    """Export given list of Mesh objects to a VRML file.

    `Mesh` structure is defined at root."""
    
    with __builtin__.open(filepath, 'w') as f:
        # write the standard VRML header
        f.write("#VRML V2.0 utf8\n\n")
        for mesh in meshes:
            f.write("Shape { geometry IndexedFaceSet \n{ coordIndex [")
            # write coordinate indexes for each face
            f.write(','.join("%d,%d,%d,-1" % f for f in mesh.faces))
            f.write("]\n") # closes coordIndex
            f.write("coord Coordinate { point [")
            # write coordinate points for each vertex
            #f.write(','.join('%.3f %.3f %.3f' % (p.x, p.y, p.z) for p in mesh.points))
            f.write(','.join('%.3f %.3f %.3f' % (p.x, p.y, p.z) for p in mesh.points))
            f.write("]\n}") # closes Coordinate
            #shape_col=(1.0, 0.0, 0.0)#, 0.0)
            f.write("}\n") # closes points
            #say(mesh.color)
            shape_col=mesh.color[:-1] #remove last item
            #say(shape_col)
            shape_transparency=mesh.transp
            f.write("appearance Appearance{material Material{diffuseColor %f %f %f\n" % shape_col)
            f.write("transparency %f}}" % shape_transparency)
            f.write("}\n") # closes Shape
        say(filepath,"written")
        
#return a 'view' of the object, with attributes such as color/transparency
def getObjectView(object):
    return FreeCADGui.ActiveDocument.getObject(object.Name)
    
#convert an object to a list of mesh    
def objectToMesh(object, scale=None):
    view = getObjectView(object)
    shape = object.Shape
    
    deviation = 0.03
    
    color = view.DiffuseColor
    transparency = view.Transparency
    
    #list of meshes
    meshes = []
    
    #if there are fewer colors than faces, apply one color to all faces
    if len(color) < len(shape.Faces):
        applyDiffuse = False
    else:
        applyDiffuse = True
    
    for i,face in enumerate(shape.Faces):
        
        if applyDiffuse: #apply individual face colors
            col = color[i]
        else: #apply one color to all faces
            col = color[0]
            
        meshes.append(faceToMesh(face,col,transparency,deviation,scale))
    
    return meshes
    
#Convert a face to a mesh
def faceToMesh(face, color, transp, mesh_deviation, scale=None):
    #mesh_deviation=0.1 #the smaller the best quality, 1 coarse
    #say(mesh_deviation+'\n')
    mesh_data = face.tessellate(mesh_deviation)
    points = mesh_data[0]
    
    if scale:
        points = map(lambda p: p*scale, points)
        
    newMesh = Mesh(points = points,
                faces = mesh_data[1],
                color = color,
                transp=transp)
    
    return newMesh
    
#display a console message
def say(*arg):
    FreeCAD.Console.PrintMessage(" ".join(map(str,arg)) + "\n")

#display a warning message
def sayw(*arg):
    FreeCAD.Console.PrintWarning(" ".join(map(str,arg)) + "\n")
    
#display an error message
def sayerr(*arg):
    FreeCAD.Console.PrintError(" ".join(map(str,arg)) + "\n")
    
#display a message in a message box
def saymsg(title, *arg):
    QtGui.QMessageBox.information(None,title," ".join(arg)+"\r\n")

#clear the console
def clear_console():
    #clearing previous messages
    mw=FreeCADGui.getMainWindow()
    c=mw.findChild(QtGui.QPlainTextEdit, "Python console")
    c.clear()
    r=mw.findChild(QtGui.QTextEdit, "Report view")
    r.clear()
    
#find a STEP file for a given wrl file
def getKicadStepFile(modelDir, wrl_name):
    
    dirs = []
    
    steps = [
    ".step",
    ".STEP",
    ".stp",
    ".STP"
    ]
    
    #get rid of bad path separators
    wrl_name = wrl_name.replace("/",os.path.sep)
    wrl_name = wrl_name.replace("\\",os.path.sep)
    
    model_dir, model_file = os.path.split(wrl_name)
    
    if model_file.lower().endswith(".wrl"):
        model_file = model_file[:-4]
    
    if os.path.isabs(model_dir):
        dirs.append(model_dir)
        
    dirs.append(os.path.join(modelDir,model_dir))
    
    say("Dirs:",dirs)
    
    #try all the directories
    for d in dirs:
        #try all the extensions
        for ext in steps:
            step_name = model_file + ext
            
            step_file = os.path.abspath(os.path.join(d, step_name))

            if os.path.isfile(step_file):
            
                say("STEP:",step_file)
                return step_file
                
                
    say("STEP: No match for", wrl_name)
                
    return None
    
#rotate around a given axis
#centered around zero
def rotate(objs,angle,axes):

    origin = FreeCAD.Vector(0,0,0)
    x,y,z = axes
    axis = FreeCAD.Vector(x,y,z)
    
    Draft.rotate(objs,
                angle,
                origin,
                axis=axis,
                copy=False)
                
                
#scale ALL objects around center (down to inches for KiCAD)
def scale(objs, scaling):

    if type(scaling) in [int, float]:
        x = scaling
        y = scaling
        z = scaling
    else:
        x,y,z = scaling

    scale = FreeCAD.Vector(x,y,z)
    origin = FreeCAD.Vector(0,0,0)

    Draft.scale(objs, delta=scale, center=origin, legacy=True, copy=False)
         
#move all objects 
def move(objs,x,y,z):
    Draft.move(objs,FreeCAD.Vector(x,y,z))
    
#center objects
def alignXMid(objs):
    box = getBounds(objs)
    
    d = (box.XMax + box.XMin) / 2
    
    move(objs, -d, 0, 0)
    
def alignYMid(objs):
    box = getBounds(objs)
    
    d = (box.YMax + box.YMin) / 2
    
    move(objs, 0, -d, 0)
    
def alignZMid(objs):
    box = getBounds(objs)
    
    d = (box.ZMax + box.ZMin) / 2
    
    move(objs, 0, 0, -d)
    
def alignXMin(objs):
    box = getBounds(objs)
    
    move(objs, -box.XMin, 0, 0)
    
def alignYMin(objs):
    box = getBounds(objs)
    
    move(objs, 0, -box.YMin, 0)
    
def alignZMin(objs):
    box = getBounds(objs)
    
    move(objs, 0, 0, -box.ZMin)
    
def alignXMax(objs):
    box = getBounds(objs)
    
    move(objs, -box.XMax, 0, 0)
    
def alignYMax(objs):
    box = getBounds(objs)
    
    move(objs, 0, -box.YMax, 0)
    
def alignZMax(objs):
    box = getBounds(objs)
    
    move(objs, 0, 0, -box.ZMax)
    
#get the consolidated bounding box for a group of objects
def getBounds(objs):

    box = FreeCAD.BoundBox()
    
    if len(objs) == 0:
        return None
        
    #copy across the values
    b = objs[0].Shape.BoundBox
    box.XMax = b.XMax
    box.YMax = b.YMax
    box.ZMax = b.ZMax
    
    box.XMin = b.XMin
    box.YMin = b.YMin
    box.ZMin = b.ZMin
    
    for obj in objs[1:]:
        b = obj.Shape.BoundBox
        
        #x axis comparison
        box.XMin = min(box.XMin,b.XMin)
        box.XMax = max(box.XMax,b.XMax)
        
        #y axis comparison
        box.YMin = min(box.YMin,b.YMin)
        box.YMax = max(box.YMax,b.YMax)
        
        #z axis comparison
        box.ZMin = min(box.ZMin,b.ZMin)
        box.ZMax = max(box.ZMax,b.ZMax)
    
    return box
    
    
    
#calculate the required pin-offset based on filename
def getPinOffset(filename):
    
    res = re.search("(\d*)x([\.\d]*)mm",filename)
    
    if res and len(res.groups()) == 2:
        n, pitch = res.groups()
        
        try:
            n = int(n)
            pitch = float(pitch)
            
            if n%2 == 0: #even pins
                return (math.floor(n/2) - 0.5) * pitch
            else: #odd pins
                return math.floor(n/2) * pitch
            
        except:
            sayerr("getPinOffset - error parsing filename",filename)
            pass
            
    return 0
    
#get the abs-path for the 3D file provided
def getStepFile():
    step = sys.argv[1]
    filePath = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(step):
        step = os.path.join(filePath,step)
    return step
    
#create a .wrl file path based on the provided 3D file
def getWRLFile():
    return ".".join(getStepFile().split(".")[:-1]) + ".wrl"
    
#Save objects to a STEP file
def exportStep(objs, filename):
    ImportGui.export(objs,filename)
    
#get a path to a temp copy of the provided step file
def getTempStepFile():
    step = os.path.split(getStepFile())
    
    return os.path.join(step[0],"tmp_" + step[1])
    