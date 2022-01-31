# -*- coding:utf-8 -*-
from edu_logger import root
import xmlrpc.client
import mysql.connector
import edu_mysql_script
import edu_mysql_sql_request
import edu_connection_config
import edu_odoo_create_data
import edu_odoo_migrate_bank
import edu_odoo_migrate_dossier
import edu_odoo_create_intervenant
import edu_odoo_create_relation
import edu_odoo_create_enfant
from pre_set import pre_set
from safetywrap import Result, Ok, Err

from typing import Any, Type

xmlrpc.client.Marshaller.dispatch[type(0)] = lambda _, v, w: w("<value><i8>%d</i8></value>" % v)

DATA_FORMATED: list[tuple[str, dict]] = []


def edu_odoo_connection():
    """
    Method to connect on odoo server
    :return: user uid
    """
    try:
        root.info("Start of connection to the odoo server ...")
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(edu_connection_config.ODOO_URL))
        uid = common.authenticate(edu_connection_config.ODOO_DB_NAME, edu_connection_config.ODOO_USERNAME,
                                  edu_connection_config.ODOO_PASSWORD, {})
        root.info("Connection to the odoo server success!")
        return uid
    except Exception:
        root.info("Connection to the odoo server failed!")
        return False


def edu_odoo_format_sql_request():
    """
    Method to format dict fields to request mysql and value to Odoo
    :return: 
    """
    try:
        for idx, line_sql in enumerate(edu_mysql_sql_request.ALL_TABLE_SQL):
            for lkey in line_sql:
                all_current_fields = line_sql[lkey]['fields'].keys()
                count_field = 0
                fields_table_sql = ""
                fields_value_dict = "{"
                all_field_lenght = len(all_current_fields)
                for line_field in all_current_fields:
                    if line_sql[lkey]['fields'][line_field]:
                        if count_field < all_field_lenght - 1:
                            fields_table_sql += "{0},".format(line_field)
                            fields_value_dict += "'{0}': line_value[{1}] or '',".format(
                                line_sql[lkey]['fields'][line_field], count_field)
                        else:
                            fields_table_sql += "{0}".format(line_field)
                            fields_value_dict += "'{0}': line_value[{1}] or ''{2}".format(
                                line_sql[lkey]['fields'][line_field], count_field, "}")
                        count_field += 1
                    join_param = ''
                    if line_sql[lkey]['join_param'] != '':
                        join_param = line_sql[lkey]['join_param']
                DATA_FORMATED.append((lkey, {
                    'value': fields_value_dict,
                    'query': """
                    SELECT {0} FROM {1} {2}
                """.format(fields_table_sql, lkey, join_param),
                    'count': """
                    select count(*) FROM {0} {1}
                    """.format(lkey, join_param),
                    'model': '{0}'.format(line_sql[lkey]['model_name']),
                    'default': line_sql[lkey]['default'],
                }))
    except Exception:
        pass


def edu_odoo_create_all_data_requests():
    """
    Method to create odoo data on server
    :return: None
    """
    odoo_uid = edu_odoo_connection()
    mysql_connection = edu_mysql_script.edu_mysql_connexion()
    civility = {}
    if mysql_connection:
        if odoo_uid:
            match pre_set(odoo_uid):
                case Ok(value):
                    civility = value
                case Err(e):
                    root.info(e)
                    exit(1)
            edu_odoo_format_sql_request()
            table: str
            line_format: dict
            for table, line_format in DATA_FORMATED:
                request_results = edu_mysql_script.edu_mysql_execute_request(mysql_connection,
                                                                             line_format['query'])
                request_counts = len(request_results)
                root.info("Start of the creation of {0} data on the odoo server ...".format(
                    line_format['model']))
                data_to_creates: list[dict[str, Any]] = []
                list(map(
                    lambda line_value:
                    data_to_creates.append(eval(line_format['value']))
                    if line_value[0] and line_value[0] != ""
                    else "", request_results))
                for item in data_to_creates:
                    item.update(line_format['default'])
                match line_format['model'], table:
                    case 'ir.attachment', _:
                        res = edu_odoo_migrate_dossier.edu_odoo_migrate_dossier(odoo_uid, line_format['model'],
                                                                                data_to_creates,
                                                                                table)
                        if res[0]:
                            root.info(
                                "The creation {0} on {1} odoo [{2}/{3}] success!".format(table, line_format['model'],
                                                                                         res[1], request_counts))
                    case 'res.partner.bank', _:
                        res = edu_odoo_migrate_bank.edu_odoo_migrate_bank(odoo_uid, line_format['model'], data_to_creates, table)
                        if res[0]:
                            root.info(
                                "The creation {0} on {1} odoo [{2}/{3}] success!".format(table, line_format['model'],
                                                                                         res[1], request_counts))
                    case 'res.users', 'client':
                        res = edu_odoo_create_data.edu_odoo_create_data(odoo_uid, line_format['model'], data_to_creates, table, civility)
                        if res[0]:
                            root.info(
                                "The creation {0} on {1} odoo [{2}/{3}] success!".format(table, line_format['model'],
                                                                                         res[1], request_counts))
                    # case 'res.users', 'intervenant':
                    #     res = edu_odoo_create_intervenant.edu_odoo_create_intervenant(odoo_uid, line_format['model'],
                    #                                                                   data_to_creates, table, civility)
                    #     if res[0]:
                    #         root.info(
                    #             "The creation {0} on {1} odoo [{2}/{3}] success!".format(table, line_format['model'],
                    #                                                                      res[1], request_counts))
                    case 'res.partner', 'enfant':
                        res = edu_odoo_create_enfant.edu_odoo_create_enfant(odoo_uid, line_format['model'], data_to_creates, table)
                        if res[0]:
                            root.info(
                                "The creation {0} on {1} odoo [{2}/{3}] success!".format(table, line_format['model'],
                                                                                         res[1], request_counts))
                    case 'account.analytic.account', 'relation':
                        res = edu_odoo_create_relation.edu_odoo_create_relation(odoo_uid, line_format['model'], data_to_creates, table)
                        if res[0]:
                            root.info(
                                "The creation {0} on {1} odoo [{2}/{3}] success!".format(table, line_format['model'],
                                                                                         res[1], request_counts))
                root.info("The creation data on the odoo server success!")
            mysql_connection.close()
        else:
            root.info("The odoo connection is failed!")
    else:
        root.info("The mysql connection is failed!")
