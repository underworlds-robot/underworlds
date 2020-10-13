========================
Spatial Relations Module
========================

This document explains some of the features of the spatial relations 
module for underworlds and how to use it.

***************
Basic Relations
***************

Currently all these relations are based on calculating simple bounding
boxes.

islower
=======

isabove
=======

isbelow
=======

isontop
=======

isclose
=======

isin
====

*********************
Directional Relations
*********************

These relations are also based on simple bounding boxes. They assume that the north vector is in the positive *Y* direction. These relations are used in the more complex calculations based on perspective.

isnorth
=======

iseast
======

issouth
=======

iswest
======

istonorth
=========

istoeast
========

istosouth
=========

istowest
========

***************************
Perspective Based Relations
***************************

These relations recalculate a transformed bounding boxes based on a view matrix. Unlike the previous relations these are calculated based on a node, rather than directly from a bounding box. Currently two types of perspective are considered:

    - **Camera** - The view from a camera. Cameras may also be used to determine where a person is viewing from.
    - **Object** - A view calculated based on the facing of an object. This requires determining if an object has a 'face' and where this is calculated from.

Calculating the View Matrix
===========================

Both perspective types require calculating the transformation, either to the camera, or to the 'face' of the object. In the case of the camera this is a simple case of extracting the world transformation of the camera. To calculate an object's view we look for the 'facing' property. This property is a transformation matrix from the object to its 'face'. This property can be manually set in an underworlds client. It is also set by the loader module if it finds a child object beginning with '_face', in which case the transformation is given to the parent object as the 'facing' property.

With the transformation you can calculate the View Matrix for spatial relations using the function *get_spatial_view_matrix*. This function has an option for *gravity bias*. As when we are calculating relations we often take into account the direction of gravity into our calculations (which in underworlds is assumed to be in the downward *Z* direction) by enabling gravity bias we eliminate from the transformation matrix the *Z* translation as well as the *pitch* and *roll* before calculating the view matrix.

**WARNING** - When removing pitch and roll from the transformation matrix this module is currently using Euler Angles. Due to the way transformation matrices are composed and decomposed this means the calculation may be wrong if any of the original angles were outside of the following ranges(in Radians):
    - *X* :- -pi -> pi
    - *Y* :- -pi/2 -> pi/2
    - *Z* :- -pi -> pi

A future update will convert this function to using quaternions.

istoback
========

isfacing
========

istoright
=========

isstarboard
===========

istofront
=========

isbehind
========

istoleft
========

isport
======

****************
Document Version
****************
04/Jul/2018 - 0.1 - Initial Version
