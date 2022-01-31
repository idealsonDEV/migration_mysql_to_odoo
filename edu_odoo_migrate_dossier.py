# -*- coding:utf-8 -*-

import base64
import logging
import xmlrpc.client
import mysql.connector
from tqdm import tqdm
import edu_connection_config as edu_connection_config
import edu_mysql_script as edu_mysql_script
from edu_logger import root
import paramiko
from typing import Type

logging.getLogger("paramiko").setLevel(logging.WARNING)
log_err = logging.getLogger('Error ir.attachment logger')
log_err.propagate = False
log_err.setLevel(logging.DEBUG)
hdlr_2 = logging.FileHandler("log/ir_attachment_debug.log", mode="w")
hdlr_2.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_2.setLevel(logging.DEBUG)
log_err.addHandler(hdlr_2)
hdlr_3 = logging.FileHandler("log/ir_attachment_error.log", mode="w")
hdlr_3.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_3.setLevel(logging.ERROR)
log_err.addHandler(hdlr_3)

xmlrpc.client.Marshaller.dispatch[type(0)] = lambda _, v, w: w("<value><i8>%d</i8></value>" % v)

def edu_odoo_migrate_dossier(uid: int, odoo_model_name: str, data_to_creates: list[dict], import_from:str) -> tuple[bool,int]:

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=edu_connection_config.SFTP_SERVER_HOST,
                       username=edu_connection_config.SFTP_SERVER_USER,
                       password=edu_connection_config.SFTP_SERVER_PASSWORD,
                       port=edu_connection_config.SFTP_SERVER_PORT)
        root.info("Connection on sftp server success")
    except Exception as e:
        root.info("Error connection to sftp :"+str(e))
        return False, 0
    if uid:
        if len(data_to_creates) > 0:
            root.info("Start of create [{0}] data to odoo server ...".format(odoo_model_name))
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(edu_connection_config.ODOO_URL))
            result = 0
            for num,to_create in enumerate(tqdm(data_to_creates)):
                ### find external id
                ext_id = None
                if to_create['res_model'] == 'res.partner':
                    import_table = 'client'
                elif to_create['res_model'] == 'hr.employee':
                    import_table = 'intervenant'
                if 'search_client_partner_id' in to_create.keys():
                    search = to_create.pop('search_client_partner_id')
                    c = 0
                    while True:
                        try:
                            model2, ext_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                    edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                                                    'get_object_reference',
                                                    ['__import__', import_table+'_'+to_create['res_model'].replace('.','_')+'_'+str(search)], {})
                            break

                        except Exception:
                            log_err.debug(str(num) + ' | Erreur get reference '+to_create['res_model']+' | ' + str(search))
                            break
                if ext_id != None:
                    to_create.update({'res_id': ext_id})
                else:
                    log_err.error(str(num)+' | reference not found | '+import_table+'_'+to_create['res_model'].replace('.','_')+'_'+str(search))
                    continue
                ### find documents
                encoded = None
                if 'document' in to_create.keys():
                    base_file = to_create.pop('document')
                    result_file: list = []
                    c = 0
                    while True:
                        try:
                            result_file = find(client,
                                 edu_connection_config.SFTP_ROOT_PATH+edu_connection_config.MYSQL_SERVER_DBNAME+edu_connection_config.SFTP_DOC_PATH,
                                 base_file)
                            break
                        except ConnectionRefusedError:
                            if c == 0:
                                root.info('connexion lost')
                            c += 1
                            continue
                        except TimeoutError:
                            if c == 0:
                                root.info('connexion lost')
                            c += 1
                            continue
                    if len(result_file) == 0 :
                        log_err.error(str(num)+' | File not found | '+base_file)
                        continue
                    else:
                        c = 0
                        while True:
                            try:
                                encoded = get_file(client, result_file[0].decode("utf-8"))
                                break
                            except ConnectionRefusedError:
                                if c == 0:
                                    root.info('connexion lost')
                                c += 1
                                continue
                            except TimeoutError:
                                if c == 0:
                                    root.info('connexion lost')
                                c += 1
                                continue
                            except Exception :
                                break
                if encoded != None:
                    to_create.update({'datas': str(encoded)[2:-1]})
                else:
                    log_err.error(str(num)+' | File encoded is empty | '+base_file)
                    continue
                ##### create
                ir_id = None
                c = 0
                while True:
                    try:
                        ir_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                          edu_connection_config.ODOO_PASSWORD,
                                                          odoo_model_name, 'create', [to_create])
                        break
                    except ConnectionRefusedError:
                        if c == 0:
                            root.info('connexion lost')
                        c += 1
                        continue
                    except TimeoutError:
                        if c == 0:
                            root.info('connexion lost')
                        c += 1
                        continue
                    except Exception as e:
                        log_err.error(str(num) + ' | Erreur to create ir_attach | ' + str(search)+' | '+str(to_create['name'])+' | '+ str(e))
                        break
                if ir_id == None:
                    continue
                result += 1
            client.close()
            root.info("End of create [{0}] data to odoo server".format(odoo_model_name))
            return True, result
        else:
            return True, 0
    else:
        client.close()
        root.info("Create request on odoo server failed!")
        return False, 0

def find(client : Type[paramiko.SSHClient], path: str , name: str) -> list[str]:
    list_file:list = []
    stdin, stdout, stderr = client.exec_command('find '+path+' -name "'+name+'"')
    for line in stdout.read().splitlines():
        list_file.append(line)
    return list_file

def get_file(client : Type[paramiko.SSHClient], filename: str) -> bytes:
    sftp = client.open_sftp()
    remote_file = sftp.open(filename, mode="rb")
    encoded = base64.b64encode(remote_file.read())
    remote_file.close()
    return encoded