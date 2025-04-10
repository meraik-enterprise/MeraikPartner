from odoo import models, fields, api
import requests
import logging
from datetime import datetime, timedelta
import json
import pytz
from dateutil.parser import parse

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    x_chat_conversation_id = fields.Char(
        string='Conversación ID',
        help='ID único de la conversación en Chat'
    )
    x_last_message_timestamp = fields.Datetime(
        string='Último mensaje procesado',
        help='Timestamp del último mensaje procesado de la conversación'
    )
    x_source = fields.Selection([
        ('webhook', 'Webhook'),
        ('cron', 'Importación Automática')
    ], string='Origen del Ticket', default='cron', help='Indica el origen de la creación del ticket')

    @api.model
    def _get_chat_config(self):
        """Obtiene la configuración de Chat desde los parámetros del sistema."""
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('chatbot_api_key', '')
        chatbot_id = ICP.get_param('chatbot_id', '')
        start_time_hours = int(ICP.get_param('start_time_hours', '1'))
        end_time_hours = int(ICP.get_param('end_time_hours', '0'))
        base_url = ICP.get_param('chat_base_url',
                                 'https://api.chat-data.com/api/v2/get-conversations')
        ticket_stage_name = ICP.get_param('ticket_stage', 'Solved')
        return api_key, chatbot_id, start_time_hours, end_time_hours, base_url, ticket_stage_name

    def _format_message(self, message, is_first=False):
        """Formatea un mensaje individual para la descripción del ticket."""
        try:
            # Verificar si el mensaje tiene timestamp
            timestamp_str = message.get('timestamp')
            if not timestamp_str:
                _logger.warning(f"Mensaje sin timestamp: {message}")
                formatted_time = "Sin fecha"
            else:
                # El timestamp viene como string ISO 8601
                timestamp = parse(timestamp_str)
                # Convertir a la zona horaria del usuario
                user_tz = pytz.timezone(self.env.user.tz or 'UTC')
                local_timestamp = timestamp.astimezone(user_tz)
                formatted_time = local_timestamp.strftime('%d/%m/%Y %H:%M')

            role = message.get('role', 'unknown')
            content = message.get('content', '')

            # Mapear roles a nombres más amigables
            role_mapping = {
                'assistant': 'Barça Mobile',
                'user': 'Usuario',
                'unknown': 'Desconocido'
            }
            display_role = role_mapping.get(role, role)

            # Si es el primer mensaje, agregamos una línea en blanco antes
            if is_first:
                return f"<b>{display_role}</b> ({formatted_time}) — {content}<br/>"
            else:
                return f"<b>{display_role}</b> ({formatted_time}) — {content}<br/>"

        except Exception as e:
            _logger.error(f"Error formateando mensaje: {str(e)}")
            return f"[ERROR] {message.get('role', 'unknown')}: {message.get('content', '')}<br/>"

    def _get_last_message_timestamp(self, messages):
        """Obtiene el timestamp del último mensaje en formato datetime."""
        if not messages:
            return None
        try:
            last_message = messages[-1]
            timestamp_str = last_message.get('timestamp')
            if not timestamp_str:
                _logger.warning("Último mensaje sin timestamp")
                return None
            # Convertir a datetime sin zona horaria
            timestamp = parse(timestamp_str)
            return timestamp.replace(tzinfo=None)
        except Exception as e:
            _logger.error(f"Error obteniendo último timestamp: {str(e)}")
            return None

    def _create_ticket_from_conversation(self, conversation):
        """Crea o actualiza un ticket a partir de una conversación."""
        _logger.info("Iniciando creación/actualización de ticket")
        conversation_id = conversation.get('conversationId')
        _logger.info(f"ID de conversación: {conversation_id}")

        if not conversation_id:
            _logger.error("Conversación sin ID")
            return False

        # Obtener el nombre del stage desde la configuración
        _, _, _, _, _, ticket_stage_name = self._get_chat_config()
        _logger.info(f"Stage configurado: {ticket_stage_name}")

        # Buscar el stage configurado
        ticket_stage = self.env['helpdesk.stage'].search(
            [('name', '=', ticket_stage_name)], limit=1)
        if not ticket_stage:
            _logger.error(f"No se encontró el stage '{ticket_stage_name}'")
            return False

        # Verificar si ya existe un ticket con este ID
        existing_ticket = self.search([
            ('x_chat_conversation_id', '=', conversation_id)
        ], limit=1)

        if existing_ticket:
            _logger.info(f"Ticket existente encontrado: {existing_ticket.id}")
        else:
            _logger.info("No se encontró ticket existente, creando uno nuevo")

        messages = conversation.get('messages', [])
        _logger.info(f"Número de mensajes en la conversación: {len(messages)}")

        if not messages:
            _logger.warning(f"Conversación {conversation_id} sin mensajes")
            return False

        # Log de los primeros 3 mensajes para debugging
        for i, msg in enumerate(messages[:3]):
            _logger.info(f"Mensaje {i+1}: {json.dumps(msg, indent=2)}")

        if existing_ticket:
            if existing_ticket.x_last_message_timestamp:
                _logger.info(
                    f"Último timestamp procesado: {existing_ticket.x_last_message_timestamp}")
                new_messages = []
                last_saved_timestamp = existing_ticket.x_last_message_timestamp

                for message in messages:
                    try:
                        timestamp_str = message.get('timestamp')
                        _logger.debug(
                            f"Procesando mensaje con timestamp: {timestamp_str}")

                        if not timestamp_str:
                            _logger.warning(
                                f"Mensaje sin timestamp en conversación {conversation_id}")
                            continue

                        message_timestamp = parse(
                            timestamp_str).replace(tzinfo=None)
                        _logger.debug(
                            f"Timestamp parseado: {message_timestamp}")

                        if message_timestamp > last_saved_timestamp:
                            _logger.info(
                                f"Nuevo mensaje encontrado: {message_timestamp}")
                            new_messages.append(message)
                    except Exception as e:
                        _logger.error(
                            f"Error procesando timestamp del mensaje: {str(e)}", exc_info=True)
                        continue

                _logger.info(
                    f"Se encontraron {len(new_messages)} mensajes nuevos")

                if new_messages:
                    all_messages = []
                    current_description = existing_ticket.description or ""

                    # Obtener todos los mensajes antiguos
                    for message in messages:
                        try:
                            timestamp_str = message.get('timestamp')
                            if not timestamp_str:
                                _logger.warning(
                                    f"Mensaje sin timestamp en conversación {conversation_id}")
                                continue

                            message_timestamp = parse(
                                timestamp_str).replace(tzinfo=None)
                            if message_timestamp <= last_saved_timestamp:
                                all_messages.append(message)
                        except Exception as e:
                            _logger.error(
                                f"Error procesando mensaje antiguo: {str(e)}")
                            continue

                    # Agregar los mensajes nuevos
                    all_messages.extend(new_messages)

                    # Ordenar todos los mensajes por timestamp
                    try:
                        all_messages.sort(key=lambda x: parse(
                            x.get('timestamp')) if x.get('timestamp') else datetime.min)
                    except Exception as e:
                        _logger.error(f"Error ordenando mensajes: {str(e)}")
                        return existing_ticket

                    # Reformatear toda la descripción
                    new_description = ""
                    for i, message in enumerate(all_messages):
                        new_description += self._format_message(
                            message, is_first=(i == 0))

                    # Actualizar el ticket existente
                    existing_ticket.write({
                        'description': new_description,
                        'x_last_message_timestamp': self._get_last_message_timestamp(messages)
                    })
                    return existing_ticket
                return existing_ticket
            return existing_ticket

        # Si no existe, crear nuevo ticket
        description = ""
        for i, message in enumerate(messages):
            description += self._format_message(message, is_first=(i == 0))

        # Obtener el equipo de helpdesk
        team = self.env['helpdesk.team'].search([], limit=1)
        if not team:
            _logger.error("No se encontró ningún equipo de helpdesk")
            return False

        # Convertir createdAt (que viene en milisegundos) a datetime
        created_at_ms = conversation.get('createdAt', 0)
        if not created_at_ms:
            _logger.warning(
                f"Conversación {conversation_id} sin fecha de creación")
            created_at = datetime.now()
        else:
            created_at = datetime.fromtimestamp(
                created_at_ms / 1000.0)  # Sin UTC

        # Crear el ticket
        ticket_values = {
            'name': f"Conversación {conversation_id[-8:]}",
            'description': description,
            'x_chat_conversation_id': conversation_id,
            'create_date': created_at,
            'team_id': team.id,
            'x_last_message_timestamp': self._get_last_message_timestamp(messages),
            'stage_id': ticket_stage.id,
            'x_source': 'cron'
        }

        try:
            new_ticket = self.create(ticket_values)
            return new_ticket
        except Exception as e:
            _logger.error(f"Error al crear el ticket: {str(e)}")
            return False

    def _import_chat(self):
        """Importa conversaciones desde Chat."""
        try:
            _logger.info("Iniciando importación de conversaciones")
            api_key, chatbot_id, start_time_hours, end_time_hours, base_url, ticket_stage_name = self._get_chat_config()
            if not api_key or not chatbot_id:
                _logger.error("Falta configuración de API Key o Chatbot ID")
                return

            _logger.info(
                f"Configuración obtenida - API Key: {'*'*len(api_key)}, Chatbot ID: {chatbot_id}")
            _logger.info(
                f"Rango de tiempo: {start_time_hours}h hasta {end_time_hours}h")

            # Obtener el timestamp actual en UTC
            end_time = datetime.now(pytz.UTC)
            start_time = end_time - timedelta(hours=start_time_hours)
            end_time = end_time - timedelta(hours=end_time_hours)

            _logger.info(
                f"Buscando conversaciones entre {start_time} y {end_time}")

            # Construir la URL de la API
            url = f"{base_url}/{chatbot_id}"
            params = {
                'startTimestamp': int(start_time.timestamp() * 1000),
                'endTimestamp': int(end_time.timestamp() * 1000)
            }

            _logger.info(f"URL de la API: {url}")
            _logger.info(f"Parámetros: {params}")

            # Realizar la petición a la API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers, params=params)

            _logger.info(
                f"Respuesta de la API - Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                _logger.info(
                    f"Respuesta de la API - Data: {json.dumps(data, indent=2)}")

                if data.get('status') != 'success':
                    _logger.error(f"Error en la respuesta de Chat: {data}")
                    return

                conversations = data.get('conversations', [])
                _logger.info(
                    f"Se encontraron {len(conversations)} conversaciones")

                for idx, conversation in enumerate(conversations, 1):
                    _logger.info(
                        f"Procesando conversación {idx}/{len(conversations)}")
                    _logger.info(
                        f"Detalles de la conversación: {json.dumps(conversation, indent=2)}")
                    self._create_ticket_from_conversation(conversation)
            else:
                _logger.error(
                    f"Error al obtener conversaciones: {response.status_code} - {response.text}")

        except Exception as e:
            _logger.error(f"Error en la importación: {str(e)}", exc_info=True)

    @api.model
    def _cron_import_chat(self):
        """Método llamado por el cron para importar conversaciones."""
        self._import_chat()
