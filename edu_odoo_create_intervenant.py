# -*- coding:utf-8 -*-

from edu_logger import root
import logging
import xmlrpc.client
import mysql.connector
from tqdm import tqdm
import edu_connection_config
import edu_mysql_script as edu_mysql_script

from typing import Type

log_err = logging.getLogger('Error res.user employee logger')
log_err.propagate = False
log_err.setLevel(logging.DEBUG)
hdlr_2 = logging.FileHandler("log/res_user_employee_debug.log", mode="w")
hdlr_2.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_2.setLevel(logging.DEBUG)
log_err.addHandler(hdlr_2)
hdlr_3 = logging.FileHandler("log/res_user_employee_error.log", mode="w")
hdlr_3.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_3.setLevel(logging.ERROR)
log_err.addHandler(hdlr_3)

xmlrpc.client.Marshaller.dispatch[type(0)] = lambda _, v, w: w("<value><i8>%d</i8></value>" % v)

def edu_odoo_create_intervenant(uid: int , odoo_model_name: str, data_to_creates: list[dict], import_from: str, civility: dict) -> tuple[bool, int]:

    if uid:
        if len(data_to_creates) > 0:
            root.info("Start of create [{0}] data to odoo server ...".format(odoo_model_name))
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(edu_connection_config.ODOO_URL, timeout=10))
            result: int = 0
            for num, to_create in enumerate(tqdm(data_to_creates)):
                ### make reference to external id
                ref = None
                if 'in_ext_id' in to_create.keys():
                    ref = to_create.pop('in_ext_id')
                ### Set login
                if to_create.get('login') in [False, None, '', ' ']:
                    log_err.debug(str(num)+' | Login is null replace by ID')
                    to_create.update({'login': str(ref)})
                ## set password
                password_sha = to_create.pop('password_sha')
                password_md5 = to_create.pop('password_md5')
                password = password_sha if password_sha != '' else password_md5
                to_create.update({'password': password})
                if to_create.get('password') == '':
                    log_err.debug(str(num)+' | Password is null replace by ID')
                    to_create.update({'password': str(ref)})
                ### get other parent
                employee: dict = {}
                if 'name2' in to_create.keys():
                    employee.update({'name': to_create.pop('name2')})
                if 'work_location' in to_create.keys():
                    employee.update({'work_location': to_create.pop('work_location')})
                if 'city_work' in to_create.keys():
                    employee.update({'city_work': to_create.pop('city_work')})
                if 'city_studies' in to_create.keys():
                    employee.update({'city_studies': to_create.pop('city_studies')})
                if 'zip_code' in to_create.keys():
                    employee.update({'zip_code': to_create.pop('zip_code')})
                if 'country_id' in to_create.keys():
                    employee.update({'country_id': to_create.pop('country_id')})
                    country_ids = []
                    c = 0
                    while True:
                        try:
                            country_ids = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                            edu_connection_config.ODOO_PASSWORD, 'res.country', 'search',
                                                            [[['name', 'ilike', employee['country_id']]]], {'context' :{'lang': "fr_FR"}})
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
                            log_err.debug(str(num) + ' | Error searcch country_id of employee | ' + str(employee['country_id']))
                            break
                    if len(country_ids) > 0:
                        employee.update({'country_id': country_ids[0]})
                    else:
                        _ = employee.pop('country_id')
                if 'birthday' in to_create.keys():
                    birthday = to_create.pop('birthday')
                    if birthday != '':
                        employee.update({'birthday': str(birthday)})
                if 'place_of_birth' in to_create.keys():
                    employee.update({'place_of_birth': to_create.pop('place_of_birth')})
                if 'birthplace_department' in to_create.keys():
                    employee.update({'birthplace_department': to_create.pop('birthplace_department')})
                if 'country_of_birth' in to_create.keys():
                    employee.update({'country_of_birth': to_create.pop('country_of_birth')})
                    country_of_birth_ids = []
                    c = 0
                    while True:
                        try:
                            country_of_birth_ids = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                            edu_connection_config.ODOO_PASSWORD, 'res.country', 'search',
                                                            [[['name', 'ilike', employee['country_of_birth']]]], {'context' :{'lang': "fr_FR"}})
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
                            log_err.debug(str(num) + ' | Error searcch country_of_birth of employee | ' + str(employee['country_of_birth']))
                            break
                    if len(country_of_birth_ids) > 0:
                        employee.update({'country_of_birth': country_of_birth_ids[0]})
                    else:
                        _ = employee.pop('country_of_birth')
                if 'ssnid' in to_create.keys():
                    employee.update({'ssnid': to_create.pop('ssnid')})
                if 'id_ebp' in to_create.keys():
                    id_ebp = to_create.pop('id_ebp')
                    if id_ebp in [False, None, '', ' ']:
                        log_err.debug(str(num)+' | Champ ID EBP vide')
                        pass
                    else:
                        employee.update({'id_ebp': id_ebp})
                        pass
                if edu_connection_config.LOCATION_ID != False:
                    employee.update({'location_id': edu_connection_config.LOCATION_ID})
                ##### Update Title
                if to_create['title'] in ['M.','Mme','Melle']:
                    to_create.update({'title': civility[to_create['title']]})
                else:
                    _ = to_create.pop('title')
                ##### No name
                if 'name' in to_create.keys():
                    if to_create['name'] in ['', ' ', None, False]:
                        to_create['name'] = "Sans Nom"
                        log_err.debug(str(num) + ' | Debug name is empty replace by Sans Nom | ' + str(ref))
                else:
                    if to_create['firstname'] + to_create['lastname'] in ['', ' ', None, False]:
                        to_create['firstname'] = "Sans"
                        to_create['lastname'] = "Nom"
                        log_err.debug(str(num) + ' | Debug name is empty replace by Sans Nom | ' + str(ref))
                user_id = None
                # while True:
                #     try:
                #         model2, user_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                #                                               edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                #                                               'get_object_reference',
                #                                               ['__import__', import_from + '_res_users_' + str(ref)], {})
                #         break
                #     except ConnectionRefusedError:
                #         root.info('connexion lost')
                #         continue
                #     except TimeoutError:
                #         root.info('connexion lost')
                #         continue
                #     except Exception:
                #         log_err.debug(str(num) + ' | Erreur get reference user | ' + str(ref))
                #         break
                if user_id == None:
                #### If exist
                    logins = []
                    exit = False
                    c = 0
                    while True:
                        try:
                            logins = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
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
                    if len(logins) > 0:
                        log_err.debug(str(num) + ' | Erreur login already exist in Odoo replace by id | ' + str(to_create['login']))
                        to_create['login'] = str(ref)
                    if user_id == None:
                        ##### create
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
                                exit = True
                                err = str(e)
                                break
                        if exit:
                            log_err.error(str(num)+' | Erreur of creation of data | '+str(to_create)+' | '+err)
                            continue
                        ##### External id
                        external_ids3 = {
                            'module': '__import__',
                            'model': 'res.users',
                            'name': import_from + '_res_users_' + str(ref),
                            'res_id': user_id,
                        }
                        c = 0
                        while True:
                            try:
                                id3 = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                        edu_connection_config.ODOO_PASSWORD,
                                                        'ir.model.data', 'create', [external_ids3])
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
                                log_err.error(str(num) + ' | Erreur of creation of external id partner | ' + str(external_ids3))
                                break
                #### get partner
                partner_id = None
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
                #         log_err.debug(str(num) + ' | Erreur get reference partner | ' + str(ref))
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
                        log_err.error(str(num) + ' | Erreur get partner_id | ' + str(to_create)+' | '+ err)
                        continue
                    #### External id
                    external_ids2 = {
                        'module': '__import__',
                        'model': 'res.partner',
                        'name': import_from + '_res_partner_' + str(ref),
                        'res_id': partner_id,
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
                        except Exception:
                            log_err.error(str(num) + ' | Erreur of creation of external id partner | '+str(external_ids2))
                            break
                #### update employee with user_id and user_partner_id
                employee_id = None
                c = 0
                while True:
                    try:
                        model2, employee_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                               edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                                                               'get_object_reference',
                                                               ['__import__', import_from + '_hr_employee_' + str(ref)], {})
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
                        log_err.debug(str(num) + ' | Erreur get reference employee | ' + str(ref))
                        break
                if employee_id == None:
                    employee.update({
                        'user_id': user_id,
                        'user_partner_id': partner_id,
                        'address_home_id': partner_id,
                    })
                #### create employee
                    exit = False
                    err = ''
                    c = 0
                    while True:
                        try:
                            employee_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                            edu_connection_config.ODOO_PASSWORD,
                                                            'hr.employee', 'create', [employee])
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
                            exit = False
                            err = str(e)
                    if exit:
                        log_err.error(str(num) + ' | Erreur of creation of employee_id | ' + str(employee)+' | '+ err)
                        continue
                #### External id
                    external_ids = {
                        'module': '__import__',
                        'model': 'hr.employee',
                        'name': import_from+'_hr_employee_'+str(ref),
                        'res_id': employee_id,
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
                            log_err.error(str(num) + ' | Erreur of creation of external id employee | '+str(external_ids))
                            break
                result += 1
            root.info("End of create [{0}] data to odoo server".format(odoo_model_name))
            return True, result
    else:
        root.info("Create request on odoo server failed!")
        return False,0
