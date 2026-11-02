import os, requests

BASE = "https://api.hubapi.com"
H = {"Authorization": f"Bearer {os.environ['HUBSPOT_KEY']}"}

def buscar_contacto(email):
    body = {"filterGroups": [{"filters": [
        {"propertyName": "email", "operator": "EQ", "value": email}]}]}
    r = requests.post(f"{BASE}/crm/v3/objects/contacts/search", json=body, headers=H, timeout=10)
    r.raise_for_status()
    res = r.json()["results"]
    return res[0]["id"] if res else None

def upsert_contacto(email, nombre, apellido):
    props = {"properties": {"email": email, "firstname": nombre, "lastname": apellido}}
    cid = buscar_contacto(email)
    if cid:
        r = requests.patch(f"{BASE}/crm/v3/objects/contacts/{cid}", json=props, headers=H, timeout=10)
    else:
        r = requests.post(f"{BASE}/crm/v3/objects/contacts", json=props, headers=H, timeout=10)
    r.raise_for_status()
    return r.json()["id"]

def buscar_empresa(dominio):
    body = {"filterGroups": [{"filters": [
        {"propertyName": "domain", "operator": "EQ", "value": dominio}]}]}
    r = requests.post(f"{BASE}/crm/v3/objects/companies/search", json=body, headers=H, timeout=10)
    r.raise_for_status()
    res = r.json()["results"]
    return res[0]["id"] if res else None

def upsert_empresa(nombre, dominio):
    eid = buscar_empresa(dominio)
    if eid:
        return eid
    body = {"properties": {"name": nombre, "domain": dominio}}
    r = requests.post(f"{BASE}/crm/v3/objects/companies", json=body, headers=H, timeout=10)
    r.raise_for_status()
    return r.json()["id"]

def asociar(contact_id, company_id):
    url = f"{BASE}/crm/v4/objects/contacts/{contact_id}/associations/default/companies/{company_id}"
    requests.put(url, headers=H, timeout=10).raise_for_status()

cid = upsert_contacto("prueba1@example.com", "Ana", "Test")
eid = upsert_empresa("Empresa Demo", "empresademo.com")
asociar(cid, eid)
print("Contacto", cid, "asociado a empresa", eid)