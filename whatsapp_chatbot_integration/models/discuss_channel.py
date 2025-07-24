from odoo import models, fields, api
import logging
import requests
import random
import string
from datetime import datetime, timedelta
import json

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    conversation_id = fields.Char(
        string='Conversation ID',
        help='ID de conversación para la integración con el servicio de chatbot',
        copy=False
    )
    last_human_intervention = fields.Datetime(
        string='Última intervención humana',
        help='Fecha y hora de la última intervención de un usuario interno que no sea el chatbot',
        copy=False
    )
    last_conversation_activity = fields.Datetime(
        string='Última actividad de conversación',
        help='Fecha y hora de la última actividad en esta conversación (mensaje enviado o recibido)',
        copy=False
    )

    def _clear_expired_conversation(self):
        """
        Limpia la conversación expirada estableciendo conversation_id como vacío.
        """
        _logger.info(
            f"Chatbot: Limpiando conversación expirada para canal {self.id}")
        _logger.info(
            f"Chatbot: Canal {self.id} - conversation_id antes: {self.conversation_id}")

        self.conversation_id = False

        _logger.info(
            f"Chatbot: Canal {self.id} - conversation_id después: {self.conversation_id}")
        _logger.info(
            f"Chatbot: Conversación expirada limpiada exitosamente para canal {self.id}")

    def _update_conversation_activity(self):
        """
        Actualiza el timestamp de la última actividad de conversación.
        """
        self.last_conversation_activity = fields.Datetime.now()

    def send_message_to_chatbot(self, user_message=False, chatbot_id=False, conversation_id=False):
        """
        Envía un mensaje a un chatbot mediante su API.
        Devuelve la respuesta del bot como string.
        """
        if not self.channel_type == 'whatsapp':
            return {"error": "Este canal no es de WhatsApp"}

        # Verificar si el bot debe estar silenciado por intervención humana reciente
        if self.last_human_intervention and self.wa_account_id.chatbot_silence_minutes:
            tiempo_transcurrido = fields.Datetime.now() - self.last_human_intervention
            minutos_transcurridos = tiempo_transcurrido.total_seconds() / 60
            if minutos_transcurridos < self.wa_account_id.chatbot_silence_minutes:
                return {"silenced": "Bot silenciado por intervención humana reciente"}

        if not chatbot_id:
            chatbot_id = self.wa_account_id.chatbot_id
        if not conversation_id:
            if not self.conversation_id:
                conversation_id = self.generate_conversation_id()
                self.conversation_id = conversation_id
            else:
                conversation_id = self.conversation_id

        # Actualizar la actividad de conversación
        self._update_conversation_activity()

        api_key = self.wa_account_id.chatbot_api_key
        if not api_key or not chatbot_id:
            return {"error": "API Key o Chatbot ID no configurados"}

        url = "https://api.chat-data.com/api/v2/chat"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key
        }
        payload = {
            "chatbotId": chatbot_id,
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "conversationId": conversation_id,
            "appendMessages": "true"
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            try:
                result = response.json()
                if isinstance(result, dict) and 'content' in result:
                    return result['content']
                return str(result)
            except Exception as e:
                return response.text
        except requests.exceptions.RequestException as e:
            _logger.exception(
                "Excepción al conectar con el servicio de chatbot: %s", e)
            return "[Error de conexión con el servicio de chatbot]"

    def post_bot_response_to_whatsapp(self, bot_response):
        """
        Publica la respuesta del bot como mensaje de salida en el canal de WhatsApp.
        """
        if not bot_response:
            return
        try:
            mensaje_amigable = "El chatbot no existe o está fuera de servicio."
            if isinstance(bot_response, dict):
                if bot_response.get('status') == 'error' or 'error' in bot_response.get('message', '').lower():
                    bot_response = mensaje_amigable
            elif isinstance(bot_response, str):
                try:
                    resp_json = json.loads(bot_response)
                    if isinstance(resp_json, dict) and (resp_json.get('status') == 'error' or 'error' in resp_json.get('message', '').lower()):
                        bot_response = mensaje_amigable
                except Exception:
                    if 'error' in bot_response.lower():
                        bot_response = mensaje_amigable

            if self.whatsapp_partner_id and self.whatsapp_partner_id not in self.channel_partner_ids:
                self.channel_partner_ids = [(4, self.whatsapp_partner_id.id)]

            fecha = datetime.now() + timedelta(seconds=2)

            # Actualizar la actividad de conversación cuando el bot responde
            self._update_conversation_activity()

            # Obtener el usuario chatbot desde la cuenta
            chatbot_user = self.wa_account_id.chatbot_user_id
            chatbot_partner_id = chatbot_user.partner_id.id if chatbot_user and chatbot_user.partner_id else False
            vals = {
                'model': 'discuss.channel',
                'res_id': self.id,
                'message_type': 'whatsapp_message',
                'body': bot_response,
                'author_id': chatbot_partner_id,
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'date': fecha.strftime('%Y-%m-%d %H:%M:%S'),
            }
            msg = self.env['mail.message'].create(vals)

            whatsapp_message_vals = {
                'body': msg.body,
                'mail_message_id': msg.id,
                'message_type': 'outbound',
                'mobile_number': f'+{self.whatsapp_number}',
                'wa_account_id': self.wa_account_id.id,
            }
            wa_msg = self.env['whatsapp.message'].create(whatsapp_message_vals)

            phone_uid = self.wa_account_id.phone_uid
            token = self.wa_account_id.token
            whatsapp_number = self.whatsapp_number
            if phone_uid and token and whatsapp_number:
                url = f'https://graph.facebook.com/v18.0/{phone_uid}/messages'
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                }
                payload = {
                    'messaging_product': 'whatsapp',
                    'to': whatsapp_number,
                    'type': 'text',
                    'text': {'body': bot_response},
                }
                try:
                    response = requests.post(
                        url, json=payload, headers=headers)
                except Exception as e:
                    _logger.error(
                        'Chatbot: Excepción al enviar mensaje a WhatsApp Cloud: %s', e)
        except Exception as e:
            _logger.error("Chatbot: Error al crear mensaje en canal: %s", e)

    def generate_conversation_id(self):
        """
        Genera un ID único de conversación.
        """
        # Obtiene la fecha y hora en el formato AAAAMMDDHHMMSSFFF (con microsegundos)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        # Genera una cadena aleatoria de 6 caracteres (letras y números)
        rand_str = ''.join(random.choices(
            string.ascii_letters + string.digits, k=6))
        # Combina ambos valores para formar el ID único
        return timestamp + rand_str

    def update_last_human_intervention(self, author_id):
        """
        Actualiza el campo last_human_intervention si el autor es un usuario interno que no es el chatbot.
        """
        # Usar el usuario chatbot configurado en la cuenta
        chatbot_user = self.wa_account_id.chatbot_user_id
        if author_id:
            user = self.env['res.users'].sudo().search(
                [('partner_id', '=', author_id)], limit=1)
            if user and chatbot_user and user.id != chatbot_user.id and user.share is False:
                self.last_human_intervention = fields.Datetime.now()
