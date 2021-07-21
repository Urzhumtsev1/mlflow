INSERT INTO fires.aggr (id, satellite, region_id)
SELECT md.id, 'modis', rg.id 
FROM fires.modis as md
CROSS JOIN geographies.regions as rg
WHERE st_contains(rg.geometry, md.geom) AND md.id > {{ params.current_id }}