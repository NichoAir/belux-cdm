# belux-cdm data pack
Operational data and configuration files for the VATSIM CDM plugin, based on the Brussels (EBBU) and Luxembourgh (ELLX).

## Content
- [CDMconfig.xml](cfg/CDMconfig.xml): plugin settings
- [ctot.txt](cfg/ctot.txt): optional slot overrides
- [interval.txt](cfg/interval.txt): SID departure separations (minutes) per runway at EBBR.
- [rate.txt](cfg/rate.txt): FIR-level arrival/departure rates
- [taxi.txt](cfg/taxi.txt): runway-specific taxi polygons for EBBR in hemisphere DMS format with taxi times.
- [capacity/cad.txt](capacity/cad.txt): aerodrome capacity
- [capacity/geozones.json](capacity/geozones.json): GeoJSON feature collection of sector polygons with capacity/level limits.
- [src/coordinates.txt](src/coordinates.txt): taxi polygons as decimal degrees
- [scripts/convert-coordinates.py](scripts/convert-coordinates.py): helper to convert decimal degrees to hemisphere DMS for `taxi.txt`

