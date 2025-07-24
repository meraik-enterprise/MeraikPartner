from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class WhatsAppAccount(models.Model):
    _inherit = 'whatsapp.account'

    # Campos para la integración con Chatbot
    chatbot_id = fields.Char(
        string='Chatbot ID',
        help='ID del chatbot configurado en el servicio de IA',
        copy=False
    )
    chatbot_api_key = fields.Char(
        string='Chatbot API Key',
        help='Clave de API para autenticación con el servicio de chatbot',
        copy=False,
        groups='whatsapp.group_whatsapp_admin'
    )
    chatbot_enabled = fields.Boolean(
        string='Habilitar Chatbot',
        help='Activa la integración con el servicio de chatbot para esta cuenta',
        default=False
    )
    chatbot_silence_minutes = fields.Integer(
        string='Minutos de silencio del bot',
        help='Tiempo en minutos que el bot permanecerá silenciado después de intervención humana',
        default=15
    )
    chatbot_user_id = fields.Many2one(
        'res.users',
        string='Usuario Chatbot',
        help='Usuario de Odoo que representa al chatbot para identificar sus mensajes',
        copy=False
    )
    chatbot_conversation_timeout_minutes = fields.Integer(
        string='Timeout de conversación (minutos)',
        help='Tiempo en minutos después del cual se creará una nueva conversación. 0 = sin timeout',
        default=0
    )

    @api.constrains('chatbot_enabled', 'chatbot_user_id')
    def _check_chatbot_user_required(self):
        """Verifica que el usuario chatbot sea obligatorio solo cuando el chatbot esté habilitado"""
        for record in self:
            if record.chatbot_enabled and not record.chatbot_user_id:
                raise ValidationError(
                    'El campo "Usuario Chatbot" es obligatorio cuando el chatbot está habilitado.'
                )

    def _process_messages(self, value):
        # Procesar mensajes de texto para Chatbot antes de llamar al método padre
        chatbot_messages = []
        for messages in value.get('messages', []):
            msg_uid = messages.get('id')
            # Verifica si ya existe un mensaje con ese msg_uid
            existing = self.env['whatsapp.message'].sudo().search(
                [('msg_uid', '=', msg_uid)], limit=1)
            if existing:
                existing.state = 'delivered'
                continue  # Ya fue procesado, no responder de nuevo

            sender_name = value.get('contacts', [{}])[
                0].get('profile', {}).get('name')
            sender_mobile = messages['from']
            channel = False
            parent_msg_id = False
            parent_id = False
            if 'context' in messages and messages['context'].get('id'):
                parent_whatsapp_message = self.env['whatsapp.message'].sudo().search(
                    [('msg_uid', '=', messages['context']['id'])])
                if parent_whatsapp_message:
                    parent_msg_id = parent_whatsapp_message.id
                    parent_id = parent_whatsapp_message.mail_message_id
                if parent_id:
                    channel = self.env['discuss.channel'].sudo().search(
                        [('message_ids', 'in', parent_id.id)], limit=1)
            if not channel:
                channel = self._find_active_channel(
                    sender_mobile, sender_name=sender_name, create_if_not_found=True)

            # Guardar información para procesar después
            if messages.get('type') == 'text':
                text = messages.get('text', {}).get('body', '')
                chatbot_messages.append({
                    'channel': channel,
                    'text': text
                })

        # Llamar al método padre para crear el mensaje del usuario
        result = super()._process_messages(value)

        # Ahora procesar Chatbot después de que el mensaje del usuario se haya creado
        for msg_data in chatbot_messages:
            channel = msg_data['channel']
            text = msg_data['text']
            # Llamada a Chatbot
            if channel and channel.wa_account_id.chatbot_enabled:
                respuesta = channel.send_message_to_chatbot(
                    user_message=text)
                channel.post_bot_response_to_whatsapp(respuesta)

        return result
