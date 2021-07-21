create or replace function 
fires.after_new_rows_modis() returns trigger
   language plpgsql
   security definer
   volatile 
   called on null input
   as
$body$
BEGIN
    INSERT INTO fires.aggr (fire_id, satellite, region_id)
    SELECT ni.id, 'modis', rg.id 
    FROM new_insertions as ni
    CROSS JOIN geographies.regions as rg
    WHERE st_contains(rg.geometry, ni.geom)
    ON CONFLICT (fire_id, satellite, region_id) DO NOTHING ;

    return null ;
END ;
$body$ ;


create trigger on_new_rows_modis
   after insert on fires.modis 
   referencing new table as new_insertions
   for each statement 
   execute procedure fires.after_new_rows_modis();