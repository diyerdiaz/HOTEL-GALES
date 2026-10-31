"""Envío de correos electrónicos por SMTP (Gmail, Outlook, Brevo, SendGrid, etc.).

La configuración se toma de las variables MAIL_* del archivo .env. Si MAIL_SERVER
no está definido, el envío de correos queda desactivado.
"""

import smtplib
import ssl
import threading
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from flask import current_app


def correo_configurado():
    return bool(current_app.config.get('MAIL_SERVER'))


def _construir_mensaje(config, destinatario, asunto, texto, html=None):
    mensaje = EmailMessage()
    mensaje['Subject'] = asunto
    mensaje['From'] = formataddr((config['MAIL_SENDER_NAME'], config['MAIL_SENDER']))
    mensaje['To'] = destinatario
    mensaje['Message-ID'] = make_msgid(domain=config['MAIL_SENDER'].split('@')[-1])
    mensaje.set_content(texto)
    if html:
        mensaje.add_alternative(html, subtype='html')
    return mensaje


def _enviar(config, mensaje, logger):
    try:
        contexto = ssl.create_default_context()
        if config['MAIL_USE_SSL']:
            servidor = smtplib.SMTP_SSL(config['MAIL_SERVER'], config['MAIL_PORT'],
                                        timeout=config['MAIL_TIMEOUT'], context=contexto)
        else:
            servidor = smtplib.SMTP(config['MAIL_SERVER'], config['MAIL_PORT'],
                                    timeout=config['MAIL_TIMEOUT'])
        with servidor:
            if config['MAIL_USE_TLS'] and not config['MAIL_USE_SSL']:
                servidor.starttls(context=contexto)
            if config['MAIL_USERNAME']:
                servidor.login(config['MAIL_USERNAME'], config['MAIL_PASSWORD'])
            servidor.send_message(mensaje)
        logger.info("Correo enviado a %s: %s", mensaje['To'], mensaje['Subject'])
        return True
    except Exception:
        # Nunca se muestra el error al usuario: queda en el registro del servidor
        logger.exception("No se pudo enviar el correo a %s", mensaje['To'])
        return False


def enviar_correo(destinatario, asunto, texto, html=None):
    """Envía un correo. Por defecto en segundo plano, para que la página responda
    igual de rápido exista o no la cuenta (y no tarde mientras habla con el servidor SMTP)."""
    if not correo_configurado():
        return False

    app = current_app._get_current_object()
    claves = ('MAIL_SERVER', 'MAIL_PORT', 'MAIL_USE_TLS', 'MAIL_USE_SSL', 'MAIL_USERNAME',
              'MAIL_PASSWORD', 'MAIL_SENDER', 'MAIL_SENDER_NAME', 'MAIL_TIMEOUT')
    config = {clave: app.config.get(clave) for clave in claves}
    mensaje = _construir_mensaje(config, destinatario, asunto, texto, html)

    if app.config.get('MAIL_ASYNC', True):
        threading.Thread(target=_enviar, args=(config, mensaje, app.logger), daemon=True).start()
        return True
    return _enviar(config, mensaje, app.logger)
