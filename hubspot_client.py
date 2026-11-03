import logging
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger("hubspot")
BASE = "https://api.hubapi.com"

session = requests.Session()
session.headers["Authorization"] = f"Bearer {os.environ['HUBSPOT_KEY']}"
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=3, backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=None)))  # reintenta también POST: es seguro porque todo es upsert

def _call(method, path, **kw):
    r = session.request(method, BASE + path, timeout=10, **kw)
    if not r.ok:
        log.error("HubSpot %s %s -> %s %s", method, path, r.status_code, r.text)
    r.raise_for_status()
    return r

def _buscar(objeto, propiedad, valor):
    body = {"filterGroups": [{"filters": [
        {"propertyName": propiedad, "operator": "EQ", "value": valor}]}]}
    res = _call("POST", f"/crm/v3/objects/{objeto}/search", json=body).json()["results"]
    return res[0]["id"] if res else None

def upsert_contacto(email, nombre, apellido):
    props = {"properties": {"email": email, "firstname": nombre, "lastname": apellido}}
    cid = _buscar("contacts", "email", email)
    if cid:
        _call("PATCH", f"/crm/v3/objects/contacts/{cid}", json=props)
        return cid
    return _call("POST", "/crm/v3/objects/contacts", json=props).json()["id"]

def upsert_empresa(nombre, dominio):
    eid = _buscar("companies", "domain", dominio)
    if eid:
        return eid
    body = {"properties": {"name": nombre, "domain": dominio}}
    return _call("POST", "/crm/v3/objects/companies", json=body).json()["id"]

def asociar(contact_id, company_id):
    _call("PUT", f"/crm/v4/objects/contacts/{contact_id}/associations/default/companies/{company_id}")
