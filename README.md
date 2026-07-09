# pyfluent-automation-2D
An automation for ANSYS Fluent with PyFluent library designed for Python, for 2D cases.

## What Is Required
ANSYS Fluent 2025 R2 was used while developing the python script, previous versions may have compatibility issues.
PyFluent is used for the automation with Python 3.14, a detailed instalation can be seen in the link below. 
https://innovationspace.ansys.com/courses/courses/getting-started-with-pyfluent/lessons/lesson-2-installation/

## Setting Up
For the mesher, all required is a step file or any CAD formatted file which ANSYS supports. 
* Make sure to see how your software names your sketched parts. For example, CATIA uses the format [name of the project].[order of creation]. This is for setting up local sizes, and/or boundary conditions.

## Changing the Config
To change your config, you need to follow these steos:
For mesher:
* Open up file named "cfd_mesher.py"
* Change the variables under #CAD CONFIG to match your file. (make sure your CAD file is readable as 2D)
* Change the edgesize struct to include which settings you want.
* Change the refinement ratios to match whichever ratios you want to involve for the independence study.
* If you need to change any other configs, go through the other segments and change them as you like.
* The file will be outputted as "[CAD name]-mesh_r_[refinement ratio].msh.h5"

For solver:
* Open up file named "cfd_mesher.py"
* Search and change variables that matches your project.
* This file is automated for each refinement ratio and Reynolds number, and velocity gets changed to match the reynolds number in iterations.
* The file names of exported files include the refinement ratio and Reynolds number.
