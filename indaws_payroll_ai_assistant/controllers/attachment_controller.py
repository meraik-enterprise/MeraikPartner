from odoo import http
from odoo.http import request
import base64


class AttachmentDownloadController(http.Controller):

    @http.route('/download/attachment/<int:attachment_id>', type='http', auth='public', website=True)
    def download_attachment(self, attachment_id, **kwargs):
        # Verificar si el usuario está autenticado
        if not request.session.uid:
            return request.redirect('/web/login')  # Redirigir al login si no hay sesión activa

        # Buscar el archivo adjunto
        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)

        # Validar que el archivo existe
        if not attachment or not attachment.exists():
            return request.not_found()

        # Decodificar el contenido del archivo
        file_content = base64.b64decode(attachment.datas) if attachment.datas else b""
        if not file_content:
            return request.not_found()

        # Preparar el nombre del archivo
        file_name = attachment.name or "attachment"

        # Preparar la respuesta HTTP
        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', f'attachment; filename="{file_name}"'),
            ]
        )
