#!/usr/bin/python

import os
import re
import subprocess
import time
import MySQLdb

##############################################################################
##																			##
##							 Gestion du thermostat							##
##																			##
##############################################################################


## CONSTANTES
BDDSERVEUR = "localhost"
BDDLOGIN = "****************"
BDDMOTDEPASSE = "**************"
BDDNOM = "**************"
DEBUG = True
HYSTERESIS = 0.2
DUREEMAX = 20
DUREEPAUSE = 10

## INITIALISATION DE VARIABLES GLOBALES
tempPilote = 999
tempProg = 999
timeCron = time.localtime()

## CONNEXION A LA BASE DE DONNEES
db = MySQLdb.connect(BDDSERVEUR, BDDLOGIN, BDDMOTDEPASSE, BDDNOM)


##############################################
##		DEFINITION DES FONCTIONS			##
##############################################

def ChauffageAllume():
	## FONCTION PERMETTANT DE SAVOIR SI LE CHAUFFAGE EST ALLUME OU ETEINT
	etatChaudiere = False;
	cursor = db.cursor()
	query = " SELECT COUNT(*) AS estallume FROM plage_allumage WHERE pal_datetime_OFF = '0000-00-00 00:00:00'"
	if (DEBUG):
		print "+-------------------  Etat Chaudiere  --------------------+"
	try:
		cursor.execute(query)
		resultat = cursor.fetchone()

		if int(resultat[0]) >= 1:
			etatChaudiere = True
			if (DEBUG):
				print "! > Chaudiere allumee, depuis combien de temps ?"
            
			## Depuis combien de temps est-il allume ?
			cursor = db.cursor()
			query = " SELECT TIMESTAMPDIFF(MINUTE, pal_datetime_ON, NOW()) FROM plage_allumage WHERE pal_datetime_OFF = '0000-00-00 00:00:00'"
			try:
				cursor.execute(query)
				resultat = cursor.fetchone()
				if (DEBUG):
					print "! > Nb Minute : " + str(resultat[0])
				if int(resultat[0]) > DUREEMAX:
					## On force l'extinction pour 10 minutes
					if (DEBUG):
						print "! > Forcage extinction " + str(DUREEPAUSE) + " minutes"
						ForcageExtinction(DUREEPAUSE)
						etatChaudiere = False
				else :
					if (DEBUG):
						print "! > Chaudiere allumee depuis moins de 15 minutes"
			except MySQLdb.Error, e:
				print "! > Erreur : " + str(e)
        
		else :
			etatChaudiere = False
			if (DEBUG):
				print "! > Chaudiere eteinte"
	except MySQLdb.Error, e:
		print "! > Erreur : " + str(e)
		etatChaudiere = False
	return etatChaudiere

def AllumerChauffage(Temperature) :
	## FONCTION DECLENCHANT L'ALLUMAGE DE LA CHAUDIERE
	
	## Verification qu'il ny a pas de forcage d'extinction en cours
	pasDeForcageExtinction = True
	cursor = db.cursor()
	query = " SELECT for_source, for_datetime, for_minute_OFF, TIMESTAMPDIFF(MINUTE, for_datetime, NOW()) FROM forcage WHERE TIMESTAMPDIFF(MINUTE, for_datetime, NOW()) < for_minute_OFF "
	try:
		cursor.execute(query)
		resultat = cursor.fetchone()
		
		if (resultat):
			## On allume pas
			if (DEBUG):
				print "! > Forcage Extinction en cours : " + str(resultat[0]) + " - " + str(int(resultat[2])-int(resultat[3])) + " minute(s) restante(s)"
			pasDeForcageExtinction = False
	except MySQLdb.Error, e:
		print "! > Erreur : " + str(e)
    
	## Declencher l'allumage
	if (pasDeForcageExtinction):
		output = subprocess.check_output(["k8055", "-p:0", "-d:1"])
		if (DEBUG):
			print "+-----------------  Allumer Chaudiere  -------------------+"

		## enregistrer en BDD l'heure d'allumage.
		cursor = db.cursor()
		query = " INSERT INTO plage_allumage (pal_datetime_ON, pal_temp_ON) VALUE ('"+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())+"',"+str(Temperature)+")"
		if (DEBUG):
			print "! > Requete : " +query
		try:
			cursor.execute(query)
			db.commit()
		except MySQLdb.Error, e:
			print "! > Erreur : " + str(e)
			db.rollback()


def EteindreChauffage(Temperature) :
	## FONCTION ETAIGNANT LA CHAUDIERE
    
    ## TODO : Verification qu'il ny a pas de forcage d'allumage en cours

	## Declencher l'extinction
	output = subprocess.check_output(["k8055", "-p:0", "-d:0"])
	if (DEBUG):
		print "+-----------------  Eteindre Chaudiere  ------------------+"

	## enregistrer en BDD l'heure d'extinction
	cursor = db.cursor()
	query = " UPDATE plage_allumage SET pal_datetime_OFF = '"+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())+"', pal_temp_OFF = "+str(Temperature)+" WHERE pal_datetime_OFF = '0000-00-00 00:00:00'"
	if (DEBUG):
		print "! > Requete : " +query
	try:
		cursor.execute(query)
		db.commit()
	except MySQLdb.Error, e:
		print "! > Erreur : " + str(e)
		print "! > [" + query + "]"
		db.rollback()


def ForcageExtinction(duree) :
	## FONCTION Forcant l'extinction du chauffage pendant une duree donnee
    
	## enregistrer en BDD l'heure d'allumage.
	cursor = db.cursor()
	query = " INSERT INTO forcage (for_datetime, for_minute_OFF, for_source) VALUE ('"+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())+"',"+str(duree)+",'Allumage > "+str(DUREEMAX)+" minutes')"
	if (DEBUG):
		print "! > Requete : " +query
	try:
		cursor.execute(query)
		db.commit()
	except MySQLdb.Error, e:
		print "! > Erreur : " + str(e)
		db.rollback()
    
	## Declencher l'extinction
	EteindreChauffage(0)



##############################################
##			PROGRAMME DU THERMOSTAT			##
##############################################

if (DEBUG):
	print "+------------------------  DEBUT  ------------------------+"
	print "! > " + time.strftime('%d/%m/%Y %H:%M')

## Recherche de toutes les pieces a mesurer.
cursor = db.cursor()
requeteSQL = " SELECT pie_id, pie_nom, pie_pin, pie_delta, pie_thermostat FROM pieces WHERE pie_actif = 'OUI'"
try:
	cursor.execute(requeteSQL)
	resultat = cursor.fetchone()
	while resultat is not None:
		IdPiece = str(resultat[0])
		NomPiece = str(resultat[1])
		PinPiece = str(resultat[2])
		DeltaTemp = float(resultat[3])
		SondePilote = int(resultat[4])
		if (DEBUG):
			print "+-------------------  Releve Capteur  --------------------+"
			print "! > NomPiece : [" + NomPiece + "]"
        
		## Pour chaque piece on fait un releve de temperature
		os.chdir("/home/blockout/adafruit/Adafruit-Raspberry-Pi-Python-Code-master/Adafruit_DHT_Driver")
		output = subprocess.check_output(["./Adafruit_DHT", "22", PinPiece])
        
		temp = 999
		humidite = 999
		iteration = 0
		while temp == 999 and iteration <= 100 :
			try:
				output = subprocess.check_output(["./Adafruit_DHT", "22", PinPiece])
				matches = re.search("Temp =\s+([0-9.]+)", output)
				temp = float(matches.group(1)) + DeltaTemp
				matches = re.search("Hum =\s+([0-9.]+)", output)
				humidite = float(matches.group(1))
			except:
				temp = 999
			iteration += 1
        
		datejour = time.strftime('%Y%m%d',timeCron)
		heurejour = time.strftime('%H%M',timeCron)
        
		if (DEBUG):
			print "! > iteration : [" + str(iteration) + "]"
			print "! > temp : [" + str(temp) + "]"
			print "! > humidite : [" + str(humidite) + "]"
        
		if (SondePilote > 0):
			tempPilote = temp
        
		if (temp < 999):
			cInsert = db.cursor()
			requeteSQL = " INSERT INTO releve (rel_date,rel_heure,rel_piece,rel_temp,rel_hum) VALUES ({0},{1},{2},{3},{4}) ".format(datejour, heurejour, IdPiece, temp, humidite)
			try:
				cInsert.execute(requeteSQL)
				db.commit()
				if (DEBUG):
					print "! > INSERT OK"
			except MySQLdb.Error, e:
				db.rollback()
				print "! >  ERREUR : " + str(e)
        
		resultat = cursor.fetchone()
except MySQLdb.Error, e:
	print "Erreur : " + str(e)
## Etat de la chaudiere
chaudiereAllumee = ChauffageAllume()

## Recuperation de la temperature programmee dans les plages du thermostat
if (DEBUG):
	print "+---------------------  Thermostat  ----------------------+"

if (tempPilote < 999):
	heure = int(time.strftime('%H%M',timeCron))
	##if (DEBUG):
    ##print "! > heure : [" + str(heure) + "]"
	cursor = db.cursor()
	requeteSQL = " SELECT tpr_heure_debut, tpr_heure_fin, tpr_temp_prog FROM temp_prog "
	try:
		cursor.execute(requeteSQL)
		resultat = cursor.fetchone()
		while resultat is not None:
			HeureDebut = int(resultat[0])
			HeureFin = int(resultat[1])
            
			if (heure >= HeureDebut) and (heure < HeureFin) :
				tempProg = float(resultat[2])
				if (DEBUG):
					print "! > Plage : [" + str(HeureDebut) + "] - [" + str(HeureFin) + "] - Temp prog : [" + str(tempProg) + "] <<<<<<"
			else:
				if (DEBUG):
					print "! > Plage : [" + str(HeureDebut) + "] - [" + str(HeureFin) + "] - Temp prog : [" + str(resultat[2]) + "]"
			
			resultat = cursor.fetchone()
	except MySQLdb.Error, e:
		print "! > Erreur : " + str(e)


if (DEBUG):
	print "! > Temperature actuelle : [" + str(tempPilote) + "]"
	print "! > Temperature programmee : [" + str(tempProg) + "]"

## Allumage ou non du chauffage
if (tempProg < 999):
    
	if tempPilote <= (tempProg - HYSTERESIS):
		## On allume le chauffage !!!
		if (chaudiereAllumee) :
			if (DEBUG):
				print "! > Le chauffage est deja allume !"
		else:
			if (DEBUG):
				print "! > On allume le chauffage !"
			AllumerChauffage(tempPilote)
    
	elif tempPilote >= (tempProg + HYSTERESIS):
		## On coupe le Chauffage !!!
		if (chaudiereAllumee) :
			if (DEBUG):
				print "! > On eteint le chauffage !"
			EteindreChauffage(tempPilote)
		else:
			if (DEBUG):
				print "! > Le chauffage est deja eteint !"
    
	else:
		## On coupe le chauffage, les radiateurs ayant une certaine inertie, la température va continuer de monter un peu.
		if (DEBUG):
			print "! > On eteint le chauffage !"
		EteindreChauffage(tempPilote)

db.close();
print "! > " + time.strftime('%d/%m/%Y %H:%M')
print "+------------------------  FIN  --------------------------+"
print ""
