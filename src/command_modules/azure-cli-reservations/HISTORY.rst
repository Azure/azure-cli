.. :changelog:

Release History
===============

0.3.2
+++++
* Minor fixes

0.3.1
+++++
* Minor fixes.

0.3.0
+++++
* BREAKING CHANGE: 'show' commands log error message and fail with exit code of 3 upon a missing resource.

0.2.1
+++++
* Minor fixes.

0.2.0
+++++
**Breaking changes**

* reservations catalog show
    - Added required parameter ReservedResourceType.
    - Added optional parameter Location.
* Updated ReservationProperties model.
    - Removed 'kind'.
* Updated Catalog model.
    - Renamed 'capabilities' to 'sku_properties'.
    - Removed 'size' and 'tier'.

**Notes**

* reservations reservation update
    - Added optional parameter InstanceFlexibility.
* Support for InstanceFlexibility and ReservedResourceType.

0.1.2
++++++
* `sdist` is now compatible with wheel 0.31.0

0.1.1
++++++
* Update for CLI core changes.

0.1.0
+++++
* Initial release.
