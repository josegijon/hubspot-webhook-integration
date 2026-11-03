# HubSpot Webhook Integration

Servicio en Flask que recibe leads por webhook (por ejemplo, desde un formulario web)
y los sincroniza con HubSpot CRM de forma idempotente.

## Flujo

Formulario web → `POST /webhook/lead` → validación → HubSpot API
(upsert de contacto, upsert de empresa, asociación contacto-empresa)

## Qué hace

- Valida el payload y devuelve `400` si el email no es válido.
- **Upsert de contacto** por email: busca antes de crear, así un webhook reenviado no duplica datos.
- **Upsert de empresa** por dominio y asociación contacto-empresa (API v4 de asociaciones).
- **Reintentos con backoff** ante `429` y `5xx` (errores transitorios). Los `4xx` no se reintentan.
- Si HubSpot falla, responde `502` para que el emisor del webhook pueda reintentar.
- **Logging** del error de HubSpot (código y cuerpo) para facilitar el diagnóstico.

## Estructura

- `app.py`: endpoint del webhook, validación y manejo de errores.
- `hubspot_client.py`: cliente reutilizable de HubSpot (autenticación, reintentos, upserts).

## Ejecutar

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:HUBSPOT_KEY = "tu_clave_de_servicio"
python app.py
```

Probar:

```powershell
$body = '{"email":"ana@acme.com","nombre":"Ana","apellido":"Ruiz","empresa":"Acme","dominio":"acme.com"}'
Invoke-RestMethod -Method Post -Uri http://localhost:5000/webhook/lead -ContentType "application/json" -Body $body
```

La clave se lee de la variable de entorno `HUBSPOT_KEY`. Nunca se guarda en el repositorio.
Permisos necesarios: lectura y escritura de contactos y empresas.

## Decisiones y limitaciones

- La creación automática de empresas de HubSpot (por dominio del email) puede generar empresas duplicadas por una condición de carrera con la búsqueda. Alternativas: desactivarla, reintentar la búsqueda tras un breve retraso o fusionar después.
- Sin verificación de firma del webhook ni cola de reintentos propia (siguientes pasos).
