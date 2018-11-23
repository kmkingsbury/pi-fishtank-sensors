CREATE TABLE fishtanksensordata (
  measurement_timestamp timestamp NOT NULL,
  temperature_degf NUMERIC(5,2),
  PRIMARY KEY (measurement_timestamp)
);
