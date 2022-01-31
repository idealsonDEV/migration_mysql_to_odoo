# -*- coding:utf-8 -*-
import get_agenda
from edu_logger import root
import logging
import xmlrpc.client
import mysql.connector
from tqdm import tqdm
import edu_connection_config as edu_connection_config
import edu_mysql_script as edu_mysql_script
from datetime import timedelta, datetime
from typing import Type

log_err = logging.getLogger('Error relation logger')
log_err.propagate = False
log_err.setLevel(logging.DEBUG)
hdlr_2 = logging.FileHandler("log/contract_relation_debug.log", mode="w")
hdlr_2.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_2.setLevel(logging.DEBUG)
log_err.addHandler(hdlr_2)
hdlr_3 = logging.FileHandler("log/contract_relation_error.log", mode="w")
hdlr_3.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
hdlr_3.setLevel(logging.ERROR)
log_err.addHandler(hdlr_3)


xmlrpc.client.Marshaller.dispatch[type(0)] = lambda _, v, w: w("<value><i8>%d</i8></value>" % v)

def edu_odoo_create_relation(uid: int , odoo_model_name: str,data_to_creates: list[dict], import_from: str) -> tuple[bool,int]:
    if uid:
        if len(data_to_creates) > 0:
            root.info("Start of create [{0}] data to odoo server ...".format(odoo_model_name))
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(edu_connection_config.ODOO_URL))
            result = 0
            for num, to_create in enumerate(tqdm(data_to_creates)):
                if 'in_ext_id' in to_create.keys():
                    ref = to_create.pop('in_ext_id')
                ### make reference to external id
                if str(to_create.get('date_start')) == '':
                    log_err.error(str(num)+' | date_start is empty')
                    continue
                if str(to_create.get('date')) == '':
                    log_err.debug(str(num) + ' | date_end is empty replace by 2021-01-02')
                    to_create.update({'date': datetime.strptime('2010-01-02', '%Y-%m-%d').date()})
                if to_create.get('date') < to_create.get('date_start'):
                    log_err.debug(str(num) + ' | date_end < date_start replace by date_start + 1 day')
                    to_create.update({'date' : to_create.get('date_start')+ timedelta(days=1)})
                ref = None
                if 'in_ext_id' in to_create.keys():
                    ref = str(to_create.pop('in_ext_id'))
                ### find external id
                client_id = None
                interv_id = None
                if 'search_client_partner_id' in to_create.keys():
                    search = to_create.pop('search_client_partner_id')
                    exit = False
                    c = 0
                    while True:
                        try:
                            model2, client_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                    edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                                                    'get_object_reference',
                                                    ['__import__', 'client_res_partner_'+str(search)], {})
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
                        log_err.error(str(num) + ' | Erreur get reference client | ' + str(search))
                        continue
                if 'search_intervenant_partner_id' in to_create.keys():
                    search2 = to_create.pop('search_intervenant_partner_id')
                    exit = False
                    c = 0
                    while True:
                        try:
                            model3, interv_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                    edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                                                    'get_object_reference',
                                                    ['__import__', 'intervenant_hr_employee_'+str(search2)], {})
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
                        log_err.error(str(num) + ' | Erreur get reference intervenant  | ' + str(search2))
                        continue
                ### hr.contract
                contract_id = None
                # #### if exist
                # while True:
                #     try:
                #         model4, contract_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                #                                               edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                #                                               'get_object_reference',
                #                                               ['__import__', import_from+'_hr_contract_'+to_create.get('name_int')], {})
                #         break
                #     except ConnectionRefusedError:
                #         root.info('connexion lost')
                #         continue
                #     except TimeoutError:
                #         root.info('connexion lost')
                #         continue
                #     except Exception:
                #         #log_err.debug(str(num) + ' | Erreur get reference contract_id  | ' + to_create.get('name_int'))
                #         break
                if contract_id == None:
                    contract: dict = {}
                    contract.update({'name': to_create.get('name_int')})
                    contract.update({'employee_id': interv_id})
                    contract.update({'wage': float(to_create.get('wage')) / 1.1 if to_create.get('wage') != '' else 0.0})
                    contract.update({'date_start': str(to_create.get('date_start'))})
                    contract.update({'first_contract_date': str(to_create.get('date_start'))})
                    contract.update({'date_end': str(to_create.get('date'))})
                    contract.update({'type_wage': 'hourly'})
                    contract.update({'type_contract': 'provider'})
                    contract.update({'company_id': 1})
                    if edu_connection_config.LOCATION_ID != False:
                        contract.update({'location_id': edu_connection_config.LOCATION_ID})
                    #structure_ids = []
                    c = 0
                    while True:
                        try:
                            structure_ids = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                            edu_connection_config.ODOO_PASSWORD, 'hr.payroll.structure', 'search',
                                                            [[['name', '=', 'Prestataire Horaire']]])
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
                            log_err.debug(str(num) + ' | Erreur find struct_id | ' + str(e))
                            break
                    if len(structure_ids) > 0:
                        contract.update({'struct_id': structure_ids[0]})
                    else:
                        contract.update({'struct_id': 1})
                    type_ids = []
                    c = 0
                    while True:
                        try:
                            type_ids = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                              edu_connection_config.ODOO_PASSWORD, 'hr.contract.type', 'search',
                                                              [[['name', '=', 'CDD']]])
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
                            log_err.debug(str(num) + ' | Erreur find type_id | ' + str(e))
                            break
                    if len(type_ids) > 0:
                        contract.update({'type_id': type_ids[0]})
                    else:
                        contract.update({'type_id': 9})
                    exit = False
                    err = ''
                    c = 0
                    while True:
                        try:
                            contract_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                          edu_connection_config.ODOO_PASSWORD,
                                                          'hr.contract', 'create', [contract])
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
                    if exit:
                        log_err.error(str(num) + ' | Error to create hr.contract [pass] | ' + str(contract)+' | '+ err)
                        continue
                    #### Externat id
                    external_ids = {
                        'module': '__import__',
                        'model': 'hr.contract',
                        'name': import_from + '_hr_contract_' + str(to_create.get('name_int')),
                        'res_id': contract_id,
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
                ### account.analytic.account
                account_id = None
                #### if exist
                # while True:
                #     try:
                #         model5, account_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                #                                                 edu_connection_config.ODOO_PASSWORD, 'ir.model.data',
                #                                                 'get_object_reference',
                #                                                 ['__import__', import_from + '_account_analytic_account_' + to_create.get('name_cli')], {})
                #         break
                #     except ConnectionRefusedError:
                #         root.info('connextion lost')
                #         continue
                #     except TimeoutError:
                #         root.info('connextion lost')
                #         continue
                #     except Exception:
                #         #log_err.error(str(num) + ' | Erreur get reference account_id  | ' + to_create.get('name_int'))
                #         break
                if account_id == None:
                    account: dict = {}
                    account.update({'name': to_create.get('name_cli')})
                    account.update({'code': to_create.get('code')})
                    account.update({'partner_id': client_id})
                    account.update({'date_start': str(to_create.get('date_start'))})
                    account.update({'date': str(to_create.get('date'))})
                    account.update({'net_rate': float(to_create.get('net_rate')) if to_create.get('net_rate') != '' else 0.0})
                    account.update({'type_wage': 'hourly'})
                    account.update({'type_contract': 'provider'})
                    account.update({'price_method': 'contract_price'})
                    if edu_connection_config.LOCATION_ID != False:
                        account.update({'location_id': edu_connection_config.LOCATION_ID})
                    payment_ids = []
                    c = 0
                    while True:
                        try:
                            payment_ids = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                         edu_connection_config.ODOO_PASSWORD, 'account.payment.method', 'search',
                                                         [[['code', '=', 'sepa_direct_debit']]])
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
                            log_err.debug(str(num) + ' | Erreur find payment_method_id | ' + str(e))
                            break
                    if len(payment_ids) > 0:
                        account.update({'payment_method_id': payment_ids[0]})
                    else:
                        account.update({'payment_method_id': 4})
                    exit = False
                    err = ''
                    c = 0
                    while True:
                        try:
                            account_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                          edu_connection_config.ODOO_PASSWORD,
                                                          'account.analytic.account', 'create', [account])
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
                        log_err.error(str(num) + ' | Error to create account.analytic.account [pass] | ' + str(account)+' | '+ err)
                        continue
                    #### external id
                    external_ids2 = {
                        'module': '__import__',
                        'model': 'account.analytic.account',
                        'name': import_from + '_account_analytic_account_' + str(to_create.get('name_cli')),
                        'res_id': account_id,
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
                            log_err.debug(str(num) + ' | Erreur of creation of external id | '+str(external_ids2)+' | '+str(e))
                            break
                ##### resource.calendar.attendance
                agenda = to_create.get('agenda')
                if agenda in [False, None, '', ' ']:
                    log_err.debug(str(num), ' | Agenda is emty')
                else:
                    attendances = get_agenda.agenda2texteperline(agenda)
                for iterate, (day, (hour_from, hour_to)) in enumerate(attendances):
                    resources: dict = {}
                    resources.update({'account_id': account_id})
                    resources.update({'employee_contract_id': contract_id})
                    resources.update({'dayofweek': str(day)})
                    resources.update({'hour_from': hour_from})
                    resources.update({'hour_to': hour_to})
                    resources.update({'date_from': str(to_create.get('date_start'))})
                    resources.update({'date_to': str(to_create.get('date'))})
                    resources.update(({'name': str(ref)+' '+str(day)+' '+str(iterate)}))
                    c = 0
                    while True:
                        try:
                            resource_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                           edu_connection_config.ODOO_PASSWORD,
                                                           'resource.calendar.attendance', 'create', [resources])
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
                            log_err.error(str(num) + ' | Error to create resource.calendar.attendance [pass] | ' + str(
                                resources) + ' | ' + str(e))
                            break
                result += 1
            root.info("End of create [{0}] data to odoo server".format(odoo_model_name))
            return True, result
    else:
        root.info("Create request on odoo server failed!")
        return False, 0