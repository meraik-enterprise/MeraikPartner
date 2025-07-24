from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):

        result = super().create(vals_list)
        # Actualizar last_human_intervention si aplica
        for vals, msg in zip(vals_list, result):
            if vals.get('model') == 'discuss.channel' and vals.get('author_id'):
                channel = self.env['discuss.channel'].browse(
                    vals.get('res_id'))
                if channel:
                    channel.update_last_human_intervention(
                        vals.get('author_id'))
        return result


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def message_post(self, *args, **kwargs):
        result = super().message_post(*args, **kwargs)
        return result
