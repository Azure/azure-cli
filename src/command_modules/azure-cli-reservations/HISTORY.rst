.. :changelog:

Release History
===============

0.2.0
+++++
* reservations catalog show
    - Added required parameter ReservedResourceType.
    - Added optional parameter Location.
* reservations reservation update
    - Added optional parameter InstanceFlexibility.
* Support for InstanceFlexibility and ReservedResourceType.
* Updated ReservationProperties model.
    - Removed 'kind'.
* Updated Catalog model.
    - Renamed 'capabilities' to 'sku_properties'.
    - Removed 'size' and 'tier'.

0.1.2
++++++

* `sdist` is now compatible with wheel 0.31.0

0.1.1
++++++
* Update for CLI core changes.

0.1.0
+++++
* Initial release.
