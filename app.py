import hmac
import logging
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

import hubspot_client as hs

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("app")
app = Flask(__name__)

load_dotenv()

def _leer_secreto() -> str:
    valor = os.environ.get("WEBHOOK_SECRET")
    if not valor:
        raise RuntimeError("Falta la variable de entorno WEBHOOK_SECRET")
    return valor

WEBHOOK_SECRET = _leer_secreto()

def autorizado():
    recibido = request.headers.get("X-Webhook-Secret", "")
    return hmac.compare_digest(recibido, WEBHOOK_SECRET)

@app.post("/webhook/lead")
def lead():
    if not autorizado():
        log.warning("Webhook rechazado: secreto inválido")
        return jsonify(error="no autorizado"), 401

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if "@" not in email:
        return jsonify(error="email inválido"), 400
    try:
        cid = hs.upsert_contacto(email, data.get("nombre", ""), data.get("apellido", ""))
        if data.get("empresa") and data.get("dominio"):
            eid = hs.upsert_empresa(data["empresa"], data["dominio"].strip().lower())
            hs.asociar(cid, eid)
        log.info("Lead procesado contact_id=%s", cid)
        return jsonify(contact_id=cid), 200
    except requests.RequestException:
        log.exception("Fallo al comunicar con HubSpot")
        return jsonify(error="error en HubSpot"), 502

if __name__ == "__main__":
    app.run(port=5000)
