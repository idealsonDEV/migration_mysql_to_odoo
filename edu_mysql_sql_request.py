# -*- coding:utf-8 -*-

ALL_TABLE_SQL: list[dict[dict,str,str,dict]] = [
    {
        'intervenant': { # Mysql table name
            'fields': { # all fields Mysql to Odoo migration  ------- {'mysql_field': 'odoo_field'}-------
                'Id': 'in_ext_id',
                'Login': 'login',
                'Mot_De_Passe_SHA': 'password_sha',
                'Mot_De_Passe': 'password_md5',
                'Prenom': 'firstname',
                'Nom': 'lastname',
                #'concat(Politesse,\' \',Prenom,\' \',Nom)': 'name',
                'Adresse': 'street',
                'Complement_Adresse': 'street2',
                'Code_Postal': 'zip',
                'replace(Ville,"\b","")': 'city',
                'Tel_Fixe': 'phone',
                'Tel_Mobile': 'mobile',
                'Email': 'email',
                'CONVERT(Id,char)': 'ref',
                'Politesse': 'title',
                #'concat(Prenom,\' \',Nom)': 'name2',
                'Nom_Jeune_Fille': 'birth_name',
                'concat(`Adresse_Ecole/Travail`,\' \',`Code_Postal_Ecole/Travail`)': 'work_location',
                '`Ville_Ecole/Travail`': 'city_work',
                '`Ville_Ecole/Travail` as studies': 'city_studies',
                '`Code_Postal_Ecole/Travail`': 'zip_code',
                'Nationalite': 'country_id',
                'Date_De_Naissance': 'birthday',
                'Ville_De_Naissance': 'place_of_birth',
                'Departement_De_Naissance': 'birthplace_department',
                'Pays_De_Naissance': 'country_of_birth',
                'Securite_Sociale': 'ssnid',
                'ID_EBP': 'id_ebp',
            },
            'model_name': 'res.users', # Odoo model name,
            'join_param': "",
            'default': {
                'sel_groups_1_9_10': 9,
                'company_id': 1,
            },
        }
    },{
        'dossiers': {
            'fields': {
                'File_Name as nane': 'name',
                'File_Name as document': 'document',
                'File_Name as fname': 'store_fname',
                'Date_Enrergistrement': 'create_date',
                'Intervenant_Id': 'search_client_partner_id',
            },
            'model_name': 'ir.attachment',
            'join_param': 'left join intervenant on dossiers.Intervenant_Id = intervenant.Id where intervenant.Id is not null',
            'default': {
                'res_model': 'hr.employee',
                'type': 'binary',
            }
        }
    }, {
        'intervenant': {
            'fields': {
                'concat(Iban_Codepays,Iban_Banque,Iban_Guichet,Iban_Compte1,Iban_Compte2,Iban_Compte3,Iban_Cle) as bank': 'make_bank',
                'concat(Iban_Codepays,\' \',Iban_Banque,\' \',Iban_Guichet,\' \',Iban_Compte1,\' \',Iban_Compte2,\' \',Iban_Compte3,\' \',Iban_Cle)': 'acc_number',
                'Id': 'search_client_partner_id',
                'Bic': 'bic',
            },
            'model_name': 'res.partner.bank',
            'join_param': 'WHERE Id is not null and Iban_Codepays is not null and Iban_Banque is not null and Iban_Guichet is not null and Iban_Compte1 is not null and Iban_Compte2 is not null and Iban_Compte3 is not null and Iban_Cle is not null',
            'default': {
                'acc_type': 'iban',
            }
        }
    }, {
        'client': { # Mysql table name
            'fields': { # all fields Mysql to Odoo migration  ------- {'mysql_field': 'odoo_field'}-------
                'Id': 'in_ext_id',
                'Login': 'login',
                'Mot_De_Passe_SHA': 'password_sha',
                'Mot_De_Passe': 'password_md5',
                'Prenom': 'firstname',
                'Nom': 'lastname',
                #'concat(Politesse,\' \',Prenom,\' \',Nom)': 'name',
                'Adresse': 'street',
                'Complement_Adresse': 'street2',
                'Code_Postal': 'zip',
                'Ville': 'city',
                'Tel_Fixe': 'phone',
                'Tel_Mobile': 'mobile',
                'Email': 'email',
                'CONVERT(Id,char)': 'ref',
                'Politesse': 'title',
                'Autre_Nom': 'other_lastname',
                'Autre_Prenom': 'other_firstname',
                'Autre_Politesse': 'other_title',
                #'concat(Autre_Politesse,\' \',Autre_Prenom,\' \',Autre_Nom)': 'other_name',
                'Tel_Mobile_Autre_Parent': 'other_mobile',
                'Autre_Email': 'other_email',
            },
            'model_name': 'res.users', # Odoo model name,
            'join_param': "",
            'default': {
                'sel_groups_1_9_10': 9,
                'company_id': 1,
            },
        }
    }, {
        'dossiers': {
            'fields': {
                'File_Name as nane': 'name',
                'File_Name as document': 'document',
                'File_Name as fname': 'store_fname',
                'Date_Enrergistrement': 'create_date',
                'Client_Id': 'search_client_partner_id',
            },
            'model_name': 'ir.attachment',
            'join_param': 'left join client on dossiers.Client_Id = client.Id where client.Id is not null',
            'default': {
                'res_model': 'res.partner',
                'type': 'binary',
            }
        }
    }, {
        'client': {
            'fields': {
                'concat(Iban_Codepays,Iban_Banque,Iban_Guichet,Iban_Compte1,Iban_Compte2,Iban_Compte3,Iban_Cle) as bank': 'make_bank',
                'concat(Iban_Codepays,\' \',Iban_Banque,\' \',Iban_Guichet,\' \',Iban_Compte1,\' \',Iban_Compte2,\' \',Iban_Compte3,\' \',Iban_Cle)': 'acc_number',
                'Id': 'search_client_partner_id',
                'Bic': 'bic',
            },
            'model_name': 'res.partner.bank',
            'join_param': 'WHERE Id is not null and Iban_Codepays is not null and Iban_Banque is not null and Iban_Guichet is not null and Iban_Compte1 is not null and Iban_Compte2 is not null and Iban_Compte3 is not null and Iban_Cle is not null',
            'default': {
                'acc_type': 'iban',
            }
        }
    }, {
        'enfant': {
            'fields':{
                'enfant.Id': 'in_ext_id',
                'enfant.Nom': 'lastname',
                'enfant.Prenom': 'firstname',
                'enfant.Adresse': 'street',
                'enfant.Code_Postal': 'zip',
                'enfant.Ville': 'city',
                'enfant.Sexe': 'sex',
                'enfant.Date_Naissance': 'birthdate',
                'enfant.Client_Id': 'search_client_partner_id',
                'Politesse': 'find_parent',
            },
            'model_name': 'res.partner',
            'join_param': 'left join client on enfant.Client_Id = client.Id',
            'default': {
                'company_id': 1,
            }
        }
    }, {
        'relation':{
            'fields':{
                'relation.Id': 'in_ext_id',
                #### account.analytic.account
                'concat(\'CTR_CLI_\',relation.Id,\'_\',database())': 'name_cli',
                'relation.Client_Id': 'search_client_partner_id',
                'relation.Intervenant_Id': 'search_intervenant_partner_id',
                'relation.Offre_Id':  'code',
                'relation.Date_Debut': 'date_start',
                'relation.Date_Fin': 'date',
                'relation.Prix_Horaire': 'net_rate',
                'relation.En_place': 'active',
                #### hr.contract
                'concat(\'CTR_INT_\',relation.Id,\'_\',database())': 'name_int',
                'relation.Salaire_Horaire': 'wage',
                #### resource.calendar.attendance
                'relation.Agenda': 'agenda',
            },
            'model_name': 'account.analytic.account',
            'join_param': 'left join offre on relation.Offre_Id = offre.Id where relation.Date_Debut > "2021-01-01"',
            'default':{
            }
        }
    }
]