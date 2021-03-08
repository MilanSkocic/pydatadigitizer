2021.XX.XX
============
Modified licence from Framatome restricted to GNU GPL v.3

Added a tutorial in the documentation.

Added the possibilty to test values by plotting them in the graphic based on the defined scale in order to check if
the scale is correct.

Added a menu which emulates the commands from the keyboard.

Added 2 new commands:
 * <Ctrl-l> set all limits from last 4 points.
 * <Ctrl-n> remove all limits.

Rewrote the transformation from pixels to values through a class :class:`digitizer.gui.Transform` for easier
implementation of new transformations.

Added typing informations.

Authors
----------
M. Skocic

2020.11.20
=============
Updated minimum requirements.

Switched to Sphinx classic theme.

Authors
----------
M. Skocic

2020.08.10
============
Improvements
----------------
* Minor refractoring.

Authors
----------
M. Skocic

2020.07.01
===========
New features
--------------

* Added support profile management.

Authors
----------
* M. Skocic

2020.04.15
============

Improvements
---------------

* Fixed the icon path issue.
* Created conda recipe

Authors
----------
* M. Skocic

2020.04.14
=============

Improvements
---------------
* Update setup.py for standardizing the inputs.

Authors
---------
* M. Skocic


2020.04.07
======================

New Features
---------------
Initial release with basic functional features:

* Import image
* Set scale
* Compute and save data

Authors
----------
* M. Skocic