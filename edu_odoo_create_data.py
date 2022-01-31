# -*- coding:utf-8 -*-

from edu_logger import root
import logging
import xmlrpc.client
import mysql.connector
from tqdm import tqdm
import edu_connection_config as edu_connection_config
import edu_mysql_script as edu_mysql_script

from typing import Type

log_err = logging.getLogger('Error res.user logger')
log_err.propagate = False
log_err.setLevel(logging.DEBUG)
hdlr_2 = logging.FileHandler("log/res_user_partner_debug.log", mode="w")
hdlr_2.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_2.setLevel(logging.DEBUG)
log_err.addHandler(hdlr_2)
hdlr_3 = logging.FileHandler("log/res_user_partner_error.log", mode="w")
hdlr_3.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_3.setLevel(logging.ERROR)
log_err.addHandler(hdlr_3)


xmlrpc.client.Marshaller.dispatch[type(0)] = lambda _, v, w: w("<value><i8>%d</i8></value>" % v)

def edu_odoo_create_data(uid: int , odoo_model_name: str, data_to_creates: list[dict], import_from: str, civility: dict) -> tuple[bool,int]:
    """
    Method to create odoo data on server
    :param uid: user odoo uid
    :param odoo_model_name: model odoo name
    """
#    if uid:
#        if len(data_to_creates) > 0:
#            logging.info("Start of create [{0}] data to odoo server ...".format(odoo_model_name))
#            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(edu_connection_config.ODOO_URL))
#            data_created_ids = list(map(lambda to_create:
#                                        models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
#                                                          edu_connection_config.ODOO_PASSWORD,
#                                                          odoo_model_name, 'create', [to_create])
#                                        , tqdm(data_to_creates)))

#            logging.info("End of create [{0}] data to odoo server".format(odoo_model_name))
#            return data_created_ids
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
                ### Set login
                if to_create.get('login') in [False, None, '', ' ']:
                    log_err.debug(str(num) + ' | Login is null replace by ID')
                    to_create.update({'login': str(ref)})
                ## set password
                password_sha = to_create.pop('password_sha')
                password_md5 = to_create.pop('password_md5')
                password = password_sha if password_sha != '' else password_md5
                to_create.update({'password': password})
                if to_create.get('password') == '':
                    log_err.debug(str(num) + ' | Password is null replace by ID')
                    to_create.update({'password': str(ref)})
                ### get other parent
                other: dict = {}
                if 'other_name' in to_create.keys():
                    other.update({'name': to_create.pop('other_name')})
                if 'other_lastname' in to_create.keys():
                    other.update({'lastname': to_create.pop('other_lastname')})
                if 'other_firstname' in to_create.keys():
                    other.update({'firstname': to_create.pop('other_firstname')})
                if 'other_title' in to_create.keys():
                    other.update({'title': to_create.pop('other_title')})
                    if other['title'] in ['M.', 'Mme', 'Melle']:
                        other.update({'title': civility[other['title']]})
                if 'other_mobile' in to_create.keys():
                    other.update({'mobile': to_create.pop('other_mobile')})
                if 'other_email' in to_create.keys():
                    other.update({'email': to_create.pop('other_email')})
                ##### Update Title
                if to_create['title'] in ['M.','Mme','Melle']:
                    to_create.update({'title': civility[to_create['title']]})
                else:
                    _ = to_create.pop('title')
                ##### No name
                if 'name' in to_create.keys():
                    if to_create['name'] in ['', ' ', None, False]:
                        to_create['name'] = "Sans Nom"
                        log_err.debug(str(num)+' | Debug name is empty replace by "Sans Nom"| '+ str(ref))
                else:
                    if to_create['firstname']+to_create['lastname'] in ['', ' ', None, False]:
                        to_create['firstname'] = "Sans"
                        to_create['lastname'] = "Nom"
                        log_err.debug(str(num)+' | Debug name is empty replace by "Sans Nom" | '+ str(ref))
                ##### create res user
                user_id = None
                # while True:
                #     try:
                #         model2, user_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                #                                                edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                #                                                'get_object_reference',
                #                                                ['__import__', import_from + '_res_users_' + str(ref)], {})
                #         break
                #     except ConnectionRefusedError:
                #         root.info('connexion lost')
                #         continue
                #     except TimeoutError:
                #         root.info('connexion lost')
                #         continue
                #     except Exception as e:
                #         log_err.debug(str(num) + ' | Erreur get reference res_user | ' + str(ref))
                #         break
                if user_id == None:
                    #### If exist
                    users = []
                    exit = False
                    c = 0
                    while True:
                        try:
                            users = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                      edu_connection_config.ODOO_PASSWORD, odoo_model_name, 'search',
                                                      [[['login', '=', to_create['login']]]])
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
                        except Exception:
                            exit = True
                            break
                    if exit:
                        log_err.error(str(num) + ' | Erreur of count if exist | ' + str(to_create))
                        continue
                    if len(users) > 0:
                        log_err.debug(str(num) + ' | Erreur login already exist in Odoo replace by id | ' + str(to_create['login']))
                        to_create['login'] = str(ref)
                    else:
                        exit = False
                        err = ''
                        c = 0
                        while True:
                            try:
                                user_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
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
                                err = str(e)
                                exit = True
                                break
                        if exit:
                            log_err.error(str(num)+' | Erreur of creation of data | '+str(to_create)+' | '+err)
                            continue
                    ### External Id
                    external_ids2 = {
                        'module': '__import__',
                        'model': 'res.users',
                        'name': import_from + '_res_users_' + str(ref),
                        'res_id': user_id,
                    }
                    c = 0
                    while True:
                        try:
                            id2 = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                    edu_connection_config.ODOO_PASSWORD,
                                                    'ir.model.data', 'create', [external_ids2])
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
                            log_err.error(str(num) + ' | Erreur of creation of external id | ' + str(external_ids2)+' | ' +str(e))
                            break
                partner_id = None
                #### get partner
                # while True:
                #     try:
                #         model2, partner_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                #                                             edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                #                                             'get_object_reference',
                #                                             ['__import__', import_from + '_res_partner_' + str(ref)], {})
                #         break
                #     except ConnectionRefusedError:
                #         root.info('connexion lost')
                #         continue
                #     except TimeoutError:
                #         root.info('connexion lost')
                #         continue
                #     except Exception:
                #         log_err.debug(str(num) + ' | Erreur get reference res_partner | ' + str(ref))
                #         break
                if partner_id == None:
                    exit = False
                    err = ''
                    c = 0
                    while True:
                        try:
                            read_partner = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                             edu_connection_config.ODOO_PASSWORD,
                                                             'res.users', 'read', [user_id], {'fields': ['partner_id']})
                            partner_id = read_partner[0]['partner_id'][0]
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
                            exit = True
                            err = str(e)
                            break
                    if exit:
                        log_err.error(str(num) + ' | Erreur get partner_id | ' + str(to_create) + ' | ' + err)
                        continue
                        ### External ID
                    external_ids = {
                        'module': '__import__',
                        'model': 'res.partner',
                        'name': import_from + '_res_partner_' + str(ref),
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
                        except Exception:
                            log_err.error(str(num) + ' | Erreur of creation of external id | '+str(external_ids))
                            break
                #### add parent_id to other parent
                result += 1
                if any(other.values()):
                    other.update({'parent_id': partner_id})
                    c = 0
                    while True:
                        try:
                            if 'name' in to_create.keys():
                                if (other['name'] in ['', ' ', None, False]):
                                    other['name'] = "Sans Nom"
                            else:
                                if other['firstname'] + other['lastname'] in ['', ' ', None, False]:
                                    other['firstname'] = "Sans"
                                    other['lastname'] = "Nom"
                            other_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                         edu_connection_config.ODOO_PASSWORD,
                                                         'res.partner', 'create', [other])
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
                            log_err.error(str(num)+' | Erreur of creation of other data | '+str(other)+' | '+str(e))
                            break
            root.info("End of create [{0}] data to odoo server".format(odoo_model_name))
            return True, result
    else:
        root.info("Create request on odoo server failed!")
        return False, 0