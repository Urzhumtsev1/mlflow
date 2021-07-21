CREATE TABLE IF NOT EXISTS fires.aggr (
    fire_id int8 NULL,
    satellite varchar(255) NULL,
    region_id int8 NULL,
    CONSTRAINT aggr_id_key UNIQUE (fire_id, satellite, region_id)
);