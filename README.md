# HubSpot Webhook Integration

Servicio en Flask que recibe leads por webhook (por ejemplo, desde un formulario web)
y los sincroniza con HubSpot CRM de forma idempotente.

## Flujo

Formulario web → `POST /webhook/lead` → validación → HubSpot API
(upsert de contacto, upsert de empresa, asociación contacto-empresa)

## Qué hace

- Valida el payload y devuelve `400` si el email no es válido.
- **Autenticación del webhook** con un secreto compartido en la cabecera `X-Webhook-Secret` (comparación en tiempo constante). Devuelve `401` si falta o es incorrecto, antes de tocar HubSpot.
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
Copy-Item .env.example .env
python app.py
```

Antes de arrancar, edita `.env` y rellena `HUBSPOT_KEY` y `WEBHOOK_SECRET` con tus valores.

Probar:

```powershell
$body = '{"email":"ana@acme.com","nombre":"Ana","apellido":"Ruiz","empresa":"Acme","dominio":"acme.com"}'
Invoke-RestMethod -Method Post -Uri http://localhost:5000/webhook/lead -ContentType "application/json" -Body $body -Headers @{ "X-Webhook-Secret" = "un_secreto_largo_y_aleatorio" }
```

Las credenciales se leen de variables de entorno, cargadas desde un archivo `.env` en local (ignorado en Git; la plantilla es `.env.example`). Nunca se guardan en el repositorio. El servicio no arranca si falta `WEBHOOK_SECRET`.
Permisos necesarios: lectura y escritura de contactos y empresas.

## Decisiones y limitaciones

- La creación automática de empresas de HubSpot (por dominio del email) puede generar empresas duplicadas por una condición de carrera con la búsqueda. Alternativas: desactivarla, reintentar la búsqueda tras un breve retraso o fusionar después.
- El secreto compartido es una protección básica. La evolución natural es verificar una firma HMAC del cuerpo (como hacen HubSpot y otras plataformas) y añadir una cola de reintentos propia.
- En local las credenciales vienen de un `.env`. En producción se inyectarían desde un gestor de secretos (por ejemplo, Secret Manager en GCP) y no habría archivo.
