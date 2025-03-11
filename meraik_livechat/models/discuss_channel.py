# -*- coding: utf-8 -*-
# Part of Odoo.
# Copyright 2024 Bright3C - Aylen Garcés Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import requests
import logging
import random
import string
from datetime import datetime

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    conversation_id = fields.Char(string="Conversation ID", copy=False)

    def send_message(self, user_message=False, chatbot_id=False, conversation_id=False):
        """
        Envía un mensaje a un chatbot de ChatData mediante su API.

        :param chatbot_id: ID del chatbot configurado en ChatData.
        :param user_message: Texto del mensaje a enviar.
        :return: Diccionario con la respuesta de la API o el error ocurrido.
        """

        if not chatbot_id:
            chatbot_id = self.sudo().livechat_channel_id.chatbot_id
        if not conversation_id:
            if not self.conversation_id:
                conversation_id = self.generate_conversation_id()
                self.conversation_id = conversation_id
            else:
                conversation_id = self.conversation_id

        api_key = self.sudo().livechat_channel_id.api_key

        # Verifica la URL exacta en la documentación
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
            if response.status_code == 200:
                result = response.text
                _logger.info(
                    "Mensaje enviado a ChatData correctamente: %s", result)
                return result
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                _logger.error(
                    "Error al enviar el mensaje a ChatData: %s", error_msg)
                return {"error": error_msg}
        except requests.exceptions.RequestException as e:
            _logger.exception("Excepción al conectar con ChatData: %s", e)
            return {"error": str(e)}

    def generate_conversation_id(self):
        # Obtiene la fecha y hora en el formato AAAAMMDDHHMMSSFFF (con microsegundos)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        # Genera una cadena aleatoria de 6 caracteres (letras y números)
        rand_str = ''.join(random.choices(
            string.ascii_letters + string.digits, k=6))
        # Combina ambos valores para formar el ID único
        return timestamp + rand_str
