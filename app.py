import logging
import requests
from flask import Flask, request, jsonify
import hubspot_client as hs

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("app")
app = Flask(__name__)

@app.post("/webhook/lead")
def lead():
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