import requests
import re
from lxml import etree
from safetywrap import Option, Some, Nothing


def get_iban_info(iban: str) -> Option[dict]:
    url = 'https://www.ibancalculator.com/iban_validieren.html?'
    params = {
        "tx_valIBAN_pi1[iban]": iban,
        "tx_valIBAN_pi1[fi]": "fi",
        "no_cache": 1,
    }
    zip = ''
    name = None
    street = ''
    city = ''
    country = None

    try :
        response = requests.post(url, params=params)
        htmlelem = etree.fromstring(response.content, etree.HTMLParser())
        details = htmlelem.find(".//div[@class='tx-valIBAN-pi1']")
        if type(details) != etree._Comment:
            if details.find(".//fieldset[3]/p[1]/").tag == "font":
               return Nothing()
            scountry = details.find(".//fieldset[2]/table/tr/td[2]/p").text
            m = re.search('This IBAN has the correct length for this country \((.+?)\).', scountry)
            country = m.group(1).capitalize()
            if len([i for i in details.find(".//fieldset[3]/p[3]")]) == 2:
               bic = details.find(".//fieldset[3]/p[3]/b").tail.replace(' ', '').replace(' ','')
            else:
               bic = details.find(".//fieldset[3]/p[3]/a").text
            name = details.find(".//fieldset[3]/p[4]/b").tail.replace(' ','').replace(' ','')
            if len([i for i in details.find(".//fieldset[3]/p[5]")]) == 0:
               temp = details.find(".//fieldset[3]/p[5]").text
               if re.search('^([0-9]{5,6}) (.+?)$', temp):
                   street = ''
                   zip_city = temp
               else:
                   street = temp
                   zip_city = ''
            else:
               street = details.find(".//fieldset[3]/p[5]").text or ''
               zip_city = details.find(".//fieldset[3]/p[5]/").tail
            m2 = re.search('^([0-9]+?) (.+?)$', zip_city)
            if m2:
               zip = m2.group(1)
               city = m2.group(2)
        if None in [bic,name,street]:
            return Nothing()
        res ={
            'bic':bic,
            'name':name,
            'street':street,
            'city':city,
            'zip':zip,
            'country':country,
        }
        return Some(res)
    except:
        return Nothing()

def get_bic(bic: str) ->Option[dict]:
    url_bic = 'https://www.ibancalculator.com/blz.html'
    params_bic = {
        "tx_blz_pi1[country]": 'all',
        "tx_blz_pi1[searchterms]": '',
        "tx_blz_pi1[bankcode]": bic,
        "tx_blz_pi1[fi]": "fi",
        "no_cache": 1,
    }
    country = None
    name = None
    try:
        response_bic = requests.post(url_bic, params=params_bic)
        htmlelem_bic = etree.fromstring(response_bic.content, etree.HTMLParser())
        details_bic = htmlelem_bic.find(".//table[@class='table table-hover tablestyle']")
        if type(details_bic) != etree._Comment:
            country = details_bic.find(".//tbody/tr[1]/td[@class='td-0']").text
            name = details_bic.find(".//tbody/tr[1]/td[@class='td-1']").text
        else:
            return Nothing()

        if None in [country, name]:
            return Nothing()
        res = {
            'bic': bic,
            'country_code': country,
            'name': name,
        }
        return Some(res)
    except:
        return Nothing()