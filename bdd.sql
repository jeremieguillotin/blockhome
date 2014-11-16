CREATE TABLE IF NOT EXISTS forcage (
  for_datetime timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  for_minute_OFF int(11) NOT NULL,
  for_source varchar(50) COLLATE latin1_general_cs NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;

CREATE TABLE IF NOT EXISTS pieces (
  pie_id int(11) NOT NULL,
  pie_thermostat int(11) NOT NULL,
  pie_pin int(11) NOT NULL,
  pie_nom varchar(50) COLLATE latin1_general_cs NOT NULL,
  pie_delta float NOT NULL,
  pie_actif text COLLATE latin1_general_cs NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;

CREATE TABLE IF NOT EXISTS plage_allumage (
  pal_id int(11) NOT NULL AUTO_INCREMENT,
  pal_datetime_ON timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  pal_temp_ON float NOT NULL,
  pal_datetime_OFF timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  pal_temp_OFF float NOT NULL DEFAULT '0',
  PRIMARY KEY (pal_id)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs AUTO_INCREMENT=51 ;

CREATE TABLE IF NOT EXISTS releve (
  rel_date date NOT NULL,
  rel_heure int(11) NOT NULL,
  rel_piece int(11) NOT NULL,
  rel_temp float NOT NULL,
  rel_hum float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;

CREATE TABLE IF NOT EXISTS temp_prog (
  tpr_id int(11) NOT NULL AUTO_INCREMENT,
  tpr_heure_debut int(11) NOT NULL,
  tpr_heure_fin int(11) NOT NULL,
  tpr_temp_prog float NOT NULL,
  PRIMARY KEY (tpr_id)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs AUTO_INCREMENT=4 ;

CREATE TABLE IF NOT EXISTS utilisateurs (
  uti_login varchar(50) COLLATE latin1_general_cs NOT NULL,
  uti_prenom varchar(50) COLLATE latin1_general_cs NOT NULL,
  uti_password varchar(50) COLLATE latin1_general_cs NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_general_cs;
