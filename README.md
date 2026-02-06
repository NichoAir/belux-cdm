# Belux CDM data
Operational data and configuration files for the [VATSIM CDM plugin](https://github.com/rpuig2001/CDM) for the Airports and Airspace of the Belux vACC.


## Content
cfg:
- [CDMconfig.xml](cfg/CDMconfig.xml): plugin settings (Only File needed for controllers)
- [ctot.txt](cfg/ctot.txt): optional slot overrides (for events with Slots Booking)
- [sidinterval.txt](cfg/sidinterval.txt): SID departure separations (minutes) per runway
- [rate.txt](cfg/rate.txt): Departure Rates depending on runway config and LVO
- [taxizones.txt](cfg/taxizones.txt): runway-specific taxi polygons for the Airports

capactiy: 
- [cad.txt](capacity/cad.txt): Maximum arrival capacity for per aerodrome
- [procedures.txt](capacity/procedures.txt): Valid SID and STAR Letters for the Airports 
- [profile_restrictions.txt](capacity/profile_restrictions.txt): Maximum FL for different Routings at specific Waypoints, based on the LoAs with the neighbouring vACCs
- [volumes.json](capacity/volumes.json): GeoJSON feature collection of sector polygons with capacity/level limits.

scripts: Some helper scripts, ask @DeadlyFirex

src:
sidinterval, rate and taxizone source grouped per Airport + Pictures for the Taxizones

