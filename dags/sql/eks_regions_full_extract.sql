INSERT INTO fires.aggr (id, satellite, region_id)
SELECT md.id, 'eks', rg.id 
FROM fires.eks as md
CROSS JOIN geographies.regions as rg
WHERE st_contains(rg.geometry, md.geom)