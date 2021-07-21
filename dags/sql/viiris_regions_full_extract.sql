INSERT INTO fires.aggr (id, satellite, region_id)
SELECT md.id, 'viiris', rg.id 
FROM fires.viiris as md
CROSS JOIN geographies.regions as rg
WHERE st_contains(rg.geometry, md.geom)