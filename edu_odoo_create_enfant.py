# -*- coding:utf-8 -*-

from edu_logger import root
import logging
import xmlrpc.client
import mysql.connector
from tqdm import tqdm
import edu_connection_config as edu_connection_config
import edu_mysql_script as edu_mysql_script
from typing import Type

log_err = logging.getLogger('Error Enfant logger')
log_err.propagate = False
log_err.setLevel(logging.DEBUG)
hdlr_2 = logging.FileHandler("log/res_partner_enfant_debug.log", mode="w")
hdlr_2.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_2.setLevel(logging.DEBUG)
log_err.addHandler(hdlr_2)
hdlr_3 = logging.FileHandler("log/res_partner_enfant_error.log", mode="w")
hdlr_3.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_3.setLevel(logging.ERROR)
log_err.addHandler(hdlr_3)


xmlrpc.client.Marshaller.dispatch[type(0)] = lambda _, v, w: w("<value><i8>%d</i8></value>" % v)

def edu_odoo_create_enfant(uid: int , odoo_model_name: str,data_to_creates: list[dict], import_from: str) -> tuple[bool,int]:
    if uid:
        if len(data_to_creates) > 0:
            root.info("Start of create [{0}] data to odoo server ...".format(odoo_model_name))
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(edu_connection_config.ODOO_URL))
            result = 0
            for num, to_create in enumerate(tqdm(data_to_creates)):
                ### make reference to external id
                ref = None
                if 'in_ext_id' in to_create.keys():
                    ref = to_create.pop('in_ext_id')
                ### Upadte sexe
                sex = to_create.pop('sex')
                if sex == 'M':
                    to_create.update({'sex': 'boy'})
                elif sex == 'F':
                    to_create.update({'sex': 'girl'})
                else:
                    to_create.update({'sex': 'idontknow'})
                ### date de naissance
                if 'birthdate' in to_create.keys():
                    birthday = to_create.pop('birthdate')
                    if birthday != '':
                        to_create.update({'birthdate': str(birthday)})
                ### find external id
                ext_id = None
                if 'search_client_partner_id' in to_create.keys():
                    search = to_create.pop('search_client_partner_id')
                    c = 0
                    while True:
                        try:
                            model2, ext_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                    edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                                                    'get_object_reference',
                                                    ['__import__', 'client_'+odoo_model_name.replace('.','_')+'_'+str(search)], {})
                            break
                        except ConnectionRefusedError:
                            if c == 0:
                                root.info("Connection lost")
                            c += 1
                            continue
                        except TimeoutError:
                            if c == 0:
                                root.info("Connection lost")
                            c += 1
                            continue
                        except Exception:
                            log_err.debug(str(num) + ' | Erreur get reference '+odoo_model_name+' | ' + str(search))
                            break
                ### papa ou maman
                parent = to_create.pop('find_parent')
                if ext_id != None:
                    if parent in ['Mme', 'Melle']:
                        to_create.update({'mother_id': ext_id})
                    else:
                        to_create.update({'father_id': ext_id})
                else:
                    log_err.debug(str(num)+' | Chirld without parent | '+str(to_create.get('firstname'))+' '+str(to_create.get('lastname')))
                ##### No name
                if 'name' in to_create.keys():
                    if to_create['name'] in ['', ' ', None, False]:
                        to_create['name'] = "Sans Nom"
                        log_err.debug(str(num)+' | Debug name is empty replace by Sans Nom | '+ str(ref))
                else:
                    if to_create['firstname']+to_create['lastname'] in ['', ' ', None, False]:
                        to_create['firstname'] = "Sans"
                        to_create['lastname'] = "Nom"
                        log_err.debug(str(num)+' | Debug name is empty replace by Sans Nom | '+ str(ref))
                #### If exist
                partner_id = None
                # while True:
                #     try:
                #         model2, partner_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                #                                               edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                #                                               'get_object_reference',
                #                                               ['__import__', import_from+'_res_partner_' + str(ref)], {})
                #         break
                #     except ConnectionRefusedError:
                #         root.info('Connexion lost')
                #         continue
                #     except TimeoutError:
                #         root.info('Connexion lost')
                #         continue
                #     except Exception:
                #         log_err.debug(str(num) + ' | Erreur get reference res_partner | ' + str(ref))
                #         break
                if partner_id == None:
                    enfants = []
                    err = ''
                    exit = False
                    c = 0
                    while True:
                        try:
                            enfants = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                       edu_connection_config.ODOO_PASSWORD, odoo_model_name, 'search',
                                                       [[['firstname', '=', to_create['firstname']],
                                                          ['lastname', '=', to_create['lastname']],
                                                           ['sex', '=', to_create['sex']]]])
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
                            err = str(e)
                            exit = True
                            break
                    if exit:
                        log_err.error(str(num) + ' | Erreur  count if exist user | ' + str(to_create)+' | '+err)
                        continue
                    if len(enfants) > 0:
                        partner_id = enfants[0]
                    else:
                    #### create res partner
                        c = 0
                        while True:
                            try:
                                partner_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                             edu_connection_config.ODOO_PASSWORD,
                                                             odoo_model_name, 'create', [to_create])
                                break
                            except ConnectionRefusedError:
                                if c == 0:
                                    root.info("Connexion lost")
                                c += 1
                                continue
                            except TimeoutError:
                                if c == 0:
                                    root.info("Connexion lost")
                                c += 1
                                continue
                            except Exception as e:
                                break
                        if partner_id == None:
                            log_err.error(str(num) + ' | Erreur of creation of partner data enfant| ' + str(to_create) + ' | ' + str(e))
                            continue
                    #### External id
                        external_ids = {
                            'module': '__import__',
                            'model': 'res.partner',
                            'name': import_from+'_res_partner_'+str(ref),
                            'res_id': partner_id,
                        }
                        c = 0
                        while True:
                            try:
                                id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                       edu_connection_config.ODOO_PASSWORD,
                                                       'ir.model.data', 'create', [external_ids])
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
                                log_err.debug(str(num) + ' | Erreur of creation of external id | '+str(external_ids)+' | '+str(e))
                                break
                    result += 1
            root.info("End of create [{0}] data to odoo server".format(odoo_model_name))
            return True, result
    else:
        root.info("Create request on odoo server failed!")
        return False, 0