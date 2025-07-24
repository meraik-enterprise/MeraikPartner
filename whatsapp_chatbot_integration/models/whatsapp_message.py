from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class WhatsAppMessage(models.Model):
    _inherit = 'whatsapp.message'

    logical_author_id = fields.Many2one(
        'res.partner',
        string='Autor lógico',
        compute='_compute_logical_author_id',
        store=False
    )

    def _compute_logical_author_id(self):
        for rec in self:
            author = rec.mail_message_id.author_id
            rec.logical_author_id = author.id if author else False

    def _process_statuses(self, value):
        """ Process status of the message like 'send', 'delivered' and 'read'."""
        mapping = {'failed': 'error', 'cancelled': 'cancel'}
        processed_message_ids = set()

        for statuses in value.get('statuses', []):
            whatsapp_message = self.env['whatsapp.message'].sudo().search(
                [('msg_uid', '=', statuses['id'])])
            if whatsapp_message:
                # Solo actualizar el estado, no crear duplicados
                whatsapp_message.state = mapping.get(
                    statuses['status'], statuses['status'])
                processed_message_ids.add(whatsapp_message.id)
                whatsapp_message._update_message_fetched_seen()
                if statuses['status'] == 'failed':
                    error = statuses['errors'][0] if statuses.get(
                        'errors') else None
                    if error:
                        whatsapp_message._handle_error(whatsapp_error_code=error['code'],
                                                       error_message=f"{error['code']} : {error['title']}")
            else:
                # Si no existe, puedes crear el registro aquí si es necesario, pero normalmente no debería pasar
                pass
        return self.env['whatsapp.message'].browse(sorted(processed_message_ids, reverse=True)).sudo()

    @api.model
    def create(self, vals):
        # Usar el usuario chatbot configurado en la cuenta
        author_id = None
        chatbot_user_id = None
        wa_account = None
        if vals.get('wa_account_id'):
            wa_account = self.env['whatsapp.account'].browse(
                vals['wa_account_id'])
            chatbot_user_id = wa_account.chatbot_user_id.id if wa_account and wa_account.chatbot_user_id else None
        if vals.get('mail_message_id'):
            mail_msg = self.env['mail.message'].browse(vals['mail_message_id'])
            author_id = mail_msg.author_id.id if mail_msg and mail_msg.author_id else None
        # Solo poner replied si es outbound y el autor es el chatbot
        if vals.get('message_type') == 'outbound' and author_id and chatbot_user_id:
            user = self.env['res.users'].sudo().search(
                [('partner_id', '=', author_id)], limit=1)
            if user and user.id == chatbot_user_id:
                vals['state'] = 'replied'
        res = super().create(vals)
        return res
