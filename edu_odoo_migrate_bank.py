# -*- coding:utf-8 -*-

import logging
import xmlrpc.client
import mysql.connector
from tqdm import tqdm
import edu_connection_config as edu_connection_config
import edu_mysql_script as edu_mysql_script
import get_iban
from safetywrap import Option, Some, Nothing
from edu_logger import root
from typing import Type
import re

log_err = logging.getLogger('Error res.partner.bank logger')
log_err.propagate = False
log_err.setLevel(logging.DEBUG)
hdlr_2 = logging.FileHandler("log/res_partner_bank_debug.log", mode="w")
hdlr_2.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_2.setLevel(logging.DEBUG)
log_err.addHandler(hdlr_2)
hdlr_3 = logging.FileHandler("log/res_partner_bank_error.log", mode="w")
hdlr_3.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_3.setLevel(logging.ERROR)
log_err.addHandler(hdlr_3)

xmlrpc.client.Marshaller.dispatch[type(0)] = lambda _, v, w: w("<value><i8>%d</i8></value>" % v)

def edu_odoo_migrate_bank(uid: int, odoo_model_name: str, data_to_creates: list[dict], import_from: str) -> tuple[bool,int]:
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
                ### Make bank
                iban = None
                bic = None
                bank_info = None
                if 'make_bank' in to_create.keys():
                    iban = to_create.pop('make_bank')
                    bic = to_create.pop('bic')
                    if len(iban) == 0:
                        log_err.error(str(num) + ' | Error iban is empty [Exit] ')
                        continue
                    if len(iban) == 27 :
                        match get_iban.get_iban_info(iban):
                            case Some(response):
                                bank_info = response
                            case Nothing():
                                log_err.debug(str(num)+' | Error iban not found by api | '+str(iban))
                    else:
                        log_err.debug(str(num) + ' | Error iban length | ' + str(iban))
                    if bank_info == None and bic == '':
                        log_err.debug(str(num) + ' | Error bank info None, empty bic | '+ str(iban))
                    elif bank_info == None and bic != '':
                        match get_iban.get_bic(bic):
                            case Some(response2):
                                bank_info = response2
                            case Nothing():
                                log_err.debug(str(num)+' | Error bic not found by api | '+str(bic))
                                bank_info = {'bic': bic, 'name': 'bank_name'}


                bank_id = None
                if bank_info != None:
                    if bic != '':
                        bank_info['bic'] = bic
                    if bank_info['name'] == '':
                        bank_info['name'] == 'bank_name'
                    c = 0
                    while True:
                        try:
                            if 'country_code' in bank_info.keys():
                                country_ids = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                                edu_connection_config.ODOO_PASSWORD, 'res.country', 'search',
                                                                [[['code', '=', bank_info['country_code']]]])
                            else:
                                country_ids = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                      edu_connection_config.ODOO_PASSWORD, 'res.country', 'search',
                                                      [[['name', 'ilike', bank_info['country']]]])
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
                            log_err.debug(str(num) + ' | Error search country in odoo  | ' + str(bank_info))
                            break
                    ### Update bank info
                    if len(country_ids) > 0:
                        if 'country_code' in bank_info.keys():
                            _ = bank_info.pop('country_code')
                        bank_info.update({'country': country_ids[0]})
                    else:
                        log_err.debug(str(num) + ' | Error country not found | ' + str(bank_info))

                    ### Check if exist bank
                    bank_ids = []
                    c = 0
                    while True:
                        try:
                            bank_ids = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                      edu_connection_config.ODOO_PASSWORD, 'res.bank', 'search',
                                                      [[['bic', '=', bank_info['bic']]]])
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
                            log_err.debug(str(num) + ' | Error of count Bic | ' + str(bank_info['bic']))
                            break
                    if len(bank_ids) == 0:
                        c = 0
                        while True:
                            try:
                                bank_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                  edu_connection_config.ODOO_PASSWORD, 'res.bank', 'create', [bank_info])
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
                                log_err.debug(str(num) + ' | Error create bank | ' + str(bank_info) + '| '+ str(e))
                                break
                    else:
                        bank_id = bank_ids[0]
                    if bank_id == None:
                        log_err.debug(str(num) + ' | Error bank id is None, no bank created | ' + str(bank_info))
                    else:
                        to_create.update({'bank_id': bank_id})
                else:
                    log_err.error(str(num)+ ' | No bank info, no bank created')

                ### find external id
                ext_id = None
                if 'search_client_partner_id' in to_create.keys():
                    search = to_create.pop('search_client_partner_id')
                    exit = False
                    err = ''
                    c = 0
                    while True:
                        try:
                            model2, ext_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                    edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                                                    'get_object_reference',
                                                    ['__import__', import_from+'_res_partner_'+str(search)], {})
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
                        log_err.error(str(num) + ' | Error get reference partner [pass] | ' + str(search)+' | '+err)
                        continue
                if ext_id == None:
                    log_err.error(str(num) + ' | Error partner_id is None [pass] | ' + str(search))
                    continue
                ### Update
                to_create.update({'partner_id': ext_id})
                ### Check if exist:
                exit = False
                err = ''
                c = 0
                while True:
                    try:
                        account = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                              edu_connection_config.ODOO_PASSWORD, 'res.partner.bank', 'search_read',
                                              [[['acc_number', '=', to_create['acc_number']]]])
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
                    log_err.error(str(num) + ' | Error check acc_number [pass] | ' + str(to_create['acc_number'])+' | '+ err)
                    continue
                if len(account) == 1:
                    if account[0]['partner_id'][0] == ext_id:
                        continue
                    else:
                        to_create.update({'acc_number': to_create['acc_number']+' (duplication : )'+account[0]['partner_id'][1]})
                    continue
                ##### create
                exit = False
                err = ''
                c = 0
                while True:
                    try:
                        res_bank_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
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
                    log_err.error(str(num) + ' | Error to create res.partner.bank [pass] | ' + str(to_create)+' | '+ err)
                    continue
                if import_from == 'intervenant':
                    exit = False
                    c = 0
                    while True:
                        try:
                            model3, ext_id3 = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                               edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                                                               'get_object_reference',
                                                               ['__import__', import_from + '_hr_employee_' + str(search)],
                                                               {})
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
                            exit = False
                            break
                    if exit:
                        log_err.error(str(num) + ' | Error get reference employee [pass] | ' + str(search))
                        continue
                    c = 0
                    while True:
                        try:
                            models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                      edu_connection_config.ODOO_PASSWORD,
                                                      'hr.employee', 'write', [[ext_id3], {'bank_account_id': res_bank_id}])
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
                            log_err.error(str(num)+ ' | Error write bank_account_id | '+ str([[ext_id3], {'bank_account_id': res_bank_id}])+' | '+ str(e))
                            break
                result += 1
            root.info("End of create [{0}] data to odoo server".format(odoo_model_name))
            return True, result
    else:
        root.info("Create request on odoo server failed!")
        return False, 0