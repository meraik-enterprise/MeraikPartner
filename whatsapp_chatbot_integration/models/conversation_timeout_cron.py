from odoo import models, fields, api
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ConversationTimeoutCron(models.Model):
    _name = 'conversation.timeout.cron'
    _description = 'Cron para limpiar conversaciones expiradas de WhatsApp'

    name = fields.Char(
        string='Nombre', default='Limpiar conversaciones expiradas')
    active = fields.Boolean(string='Activo', default=True)

    @api.model
    def _clean_expired_conversations(self):
        """
        Método que se ejecuta periódicamente para limpiar conversaciones expiradas.
        """
        _logger.info(
            "=== INICIO: Cron de limpieza de conversaciones expiradas ===")

        try:
            # Buscar canales de WhatsApp con conversaciones activas
            channels = self.env['discuss.channel'].search([
                ('channel_type', '=', 'whatsapp'),
                ('conversation_id', '!=', False),
                ('wa_account_id.chatbot_enabled', '=', True),
                ('wa_account_id.chatbot_conversation_timeout_minutes', '>', 0)
            ])

            _logger.info(
                f"Chatbot: Encontrados {len(channels)} canales con conversaciones activas")

            cleaned_count = 0
            for channel in channels:
                _logger.info(
                    f"Chatbot: Procesando canal {channel.id} - {channel.name}")
                _logger.info(
                    f"Chatbot: Canal {channel.id} - conversation_id: {channel.conversation_id}")
                _logger.info(
                    f"Chatbot: Canal {channel.id} - last_conversation_activity: {channel.last_conversation_activity}")

                timeout_minutes = channel.wa_account_id.chatbot_conversation_timeout_minutes
                _logger.info(
                    f"Chatbot: Canal {channel.id} - timeout configurado: {timeout_minutes} minutos")

                if channel.last_conversation_activity:
                    tiempo_transcurrido = fields.Datetime.now() - channel.last_conversation_activity
                    minutos_transcurridos = tiempo_transcurrido.total_seconds() / 60

                    _logger.info(
                        f"Chatbot: Canal {channel.id} - minutos transcurridos: {minutos_transcurridos}")

                    if minutos_transcurridos >= timeout_minutes:
                        _logger.info(
                            f"Chatbot: Canal {channel.id} - EXPIRADO - Limpiando conversación")
                        channel._clear_expired_conversation()
                        cleaned_count += 1
                    else:
                        _logger.info(
                            f"Chatbot: Canal {channel.id} - NO EXPIRADO - Tiempo restante: {timeout_minutes - minutos_transcurridos} minutos")
                else:
                    _logger.warning(
                        f"Chatbot: Canal {channel.id} - No tiene last_conversation_activity configurado")

            _logger.info(
                f"Chatbot: Proceso completado - {cleaned_count} conversaciones limpiadas")

        except Exception as e:
            _logger.error(
                f"Chatbot: ERROR en cron de limpieza de conversaciones: {e}")
            _logger.exception("Chatbot: Traceback completo:")

        _logger.info(
            "=== FIN: Cron de limpieza de conversaciones expiradas ===")

    def execute_manual_cleanup(self):
        """
        Método para ejecutar limpieza manual desde la interfaz.
        """
        self._clean_expired_conversations()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Limpieza completada',
                'message': 'Se han limpiado las conversaciones expiradas',
                'type': 'success',
            }
        }
