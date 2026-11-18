"""El email de restablecimiento: asunto, HTML y versión en texto.

Un cliente de correo no es un navegador. Gmail, Outlook o el Mail del móvil
ignoran las hojas de estilo, las variables CSS y el flexbox. Por eso la
maquetación es de otra época, a propósito:

- **Tablas** para el diseño, porque Outlook las respeta y un `div` con flexbox no.
- **Estilos en línea** en cada etiqueta, porque Gmail borra los `<style>`.
- **Ancho máximo de 480 px** con `width:100%`: en el móvil ocupa la pantalla
  y en el escritorio no se estira.
- **Botón grande** (48 px de alto, buena diana para el dedo) y, debajo, el
  enlace en texto por si el cliente de correo no pinta el botón.
- **Versión en texto**: la leen los clientes sin HTML y los filtros de spam
  la valoran.

Colores de la marca (los de `uis/website/src/input.css`): marca-600 de fondo
del botón con texto blanco, 8,9:1 de contraste.
"""

from __future__ import annotations

from html import escape
from urllib.parse import quote

from ...mailer import EmailMessage

SUBJECT = "Restablece tu contraseña de Nexova"

BRAND_600 = "#1e5695"
BRAND_950 = "#0a1c33"
TEXT_MUTED = "#4b5563"
PAGE_BACKGROUND = "#f3f4f6"


def reset_link(frontend_url: str, token: str) -> str:
    """La página del backoffice que lee el token. `frontend_url` llega sin barra final."""
    # El token ya es seguro para una URL; `quote` es el cinturón por si un día cambia.
    return f"{frontend_url}/reset-password?token={quote(token, safe='')}"


def build_reset_email(to: str, link: str, expire_minutes: int) -> EmailMessage:
    return EmailMessage(
        to=to,
        subject=SUBJECT,
        html=_html(link, expire_minutes),
        text=_text(link, expire_minutes),
    )


def _text(link: str, expire_minutes: int) -> str:
    return (
        "Hola:\n\n"
        "Hemos recibido una solicitud para restablecer la contraseña de tu cuenta "
        "del backoffice de Nexova Solutions.\n\n"
        f"Abre este enlace para elegir una nueva (caduca en {expire_minutes} minutos "
        "y solo sirve una vez):\n\n"
        f"{link}\n\n"
        "Si no lo has pedido tú, ignora este email: tu contraseña no cambia.\n\n"
        "— Nexova Solutions\n"
    )


def _html(link: str, expire_minutes: int) -> str:
    href = escape(link, quote=True)
    font = "font-family:Arial,Helvetica,sans-serif;"
    return f"""\
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(SUBJECT)}</title>
</head>
<body style="margin:0;padding:0;background-color:{PAGE_BACKGROUND};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{PAGE_BACKGROUND};">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:480px;background-color:#ffffff;border-radius:8px;">
<tr><td style="padding:20px 24px;background-color:{BRAND_950};border-radius:8px 8px 0 0;{font}font-size:18px;font-weight:bold;color:#ffffff;">Nexova Solutions</td></tr>
<tr><td style="padding:28px 24px 8px 24px;{font}font-size:22px;line-height:28px;font-weight:bold;color:{BRAND_950};">Restablece tu contraseña</td></tr>
<tr><td style="padding:8px 24px;{font}font-size:16px;line-height:24px;color:{BRAND_950};">Hemos recibido una solicitud para restablecer la contraseña de tu cuenta del backoffice. Pulsa el botón para elegir una nueva.</td></tr>
<tr><td align="center" style="padding:20px 24px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
<td align="center" bgcolor="{BRAND_600}" style="border-radius:6px;">
<a href="{href}" style="display:inline-block;padding:14px 28px;{font}font-size:16px;line-height:20px;font-weight:bold;color:#ffffff;text-decoration:none;border-radius:6px;">Elegir una nueva contraseña</a>
</td></tr></table>
</td></tr>
<tr><td style="padding:8px 24px;{font}font-size:14px;line-height:20px;color:{TEXT_MUTED};">El enlace caduca en <strong>{expire_minutes} minutos</strong> y solo sirve una vez. Si el botón no funciona, copia esta dirección en el navegador:</td></tr>
<tr><td style="padding:4px 24px 16px 24px;{font}font-size:13px;line-height:18px;word-break:break-all;"><a href="{href}" style="color:{BRAND_600};">{href}</a></td></tr>
<tr><td style="padding:16px 24px 28px 24px;border-top:1px solid #e5e7eb;{font}font-size:14px;line-height:20px;color:{TEXT_MUTED};">Si no lo has pedido tú, ignora este email: tu contraseña no cambia.</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"""
