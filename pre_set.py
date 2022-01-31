# -*- coding:utf-8 -*-

import logging
import xmlrpc.client
import edu_connection_config as edu_connection_config
from safetywrap import Result, Ok, Err

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

xmlrpc.client.Marshaller.dispatch[type(0)] = lambda _, v, w: w("<value><i8>%d</i8></value>" % v)

def pre_set(uid: int) -> Result[dict,str]:
    if uid:
        logging.info("Start of pre_set data to odoo server ...")
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(edu_connection_config.ODOO_URL))
        datas = [
            ('Monsieur', 'M.'),
            ('Madame', 'Mme'),
            ('Mademoiselle', 'Melle'),
        ]
        res = {}
        for civil in datas:
            try:
                c = 0
                while True:
                    try:
                        value = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                  edu_connection_config.ODOO_PASSWORD, 'res.partner.title', 'search_read',
                                                  [[['name', '=', civil[0]]]], {'fields': ['name', 'shortcut'], 'limit': 1,
                                                                                'context' :{'lang': "fr_FR"}})
                        break
                    except TimeoutError:
                        continue
                    except ConnectionRefusedError:
                        continue
                c = 0
                while True:
                    try:
                        if len(value) == 0:
                            civil_id = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                                        edu_connection_config.ODOO_PASSWORD, 'res.partner.title', 'create',
                                                        [{
                                                            'name': civil[0],
                                                            'shortcut': civil[1]
                                                        }],{'context' :{'lang': "fr_FR"}})
                            break
                        else:
                            upd = models.execute_kw(edu_connection_config.ODOO_DB_NAME, uid,
                                              edu_connection_config.ODOO_PASSWORD, 'res.partner.title', 'write',
                                              [[value[0]['id']], {
                                                  'shortcut': civil[1]
                                              }],{'context' :{'lang': "fr_FR"}})
                            if upd:
                                civil_id = value[0]['id']
                            break
                    except TimeoutError:
                        continue
                    except ConnectionRefusedError:
                        continue
                res.update({civil[1]: civil_id})
            except Exception as e:
                return Err("Error dans le configuration du pre_set")
        return Ok(res)