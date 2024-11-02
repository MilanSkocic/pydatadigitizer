# 1.2.2

* Switch to pyproject.toml.


# 1.2.1

* Refractoring and code cleaning.


# 1.2.0

* Change of numpy minimum version from 1.17 to 1.20 for taking advantage of the typing module.
* Change of matplotlib minimum version from 3.0 to 3.4 for taking advantage of new features.
* Simplify the settings in init file.


# 1.1.2

* Minor fixes in documentation.


# 1.1.1

* Minor fixes in documentation.


# 1.1.0

* Data table for visualizing the extracted data values as a toplevel window.
* Documentation bug fixes and improvements.
* Data are visible as an array.


# 1.0.2

* Documentation minor fixes.
* Explicit internal functions for converting (i,j) array indexes to (xpix, ypix) graph indexes
* Added ``data folder`` as an option for folder profile.

The data table will be visible in version 1.1 during the process of drawing data 
from the shortcut <Ctrl-t> or through the menu Data -> View Data.

The full data array is now saved instead of (x, y) columns only. 
This changes does not bring any compatibility issue but it is worth mentionning
that the format has changed.


# 1.0.1

* Documentation minor fixes.


# 1.0.0

Initial release with basic features:

* Import image
* Set scale
* Multiple selection of data points
* Compute and save data
