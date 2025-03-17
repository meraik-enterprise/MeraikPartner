# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
import json
import base64
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    response = fields.Text(string="Response", copy=False)

    def process_response(self, vals_response):

        server_action = self.env.ref('indaws_meraik_conection_account_move.action_process_response_account_move')
        response = vals_response.get('response', '{}')
        move_json_str = server_action.with_context(vals_response=response).run()
        json_response = json.loads(response)
        _logger.info('move_json')
        _logger.info(move_json_str)
        move_json = json.loads(move_json_str)
        res_id = move_json.get('res_id', False)
        res_name = move_json.get('res_name', '')

        if json_response.get('doc_data', False) and res_id:
            doc_data = json_response.get('doc_data')
            attachment_data = {
                'name': json_response.get('doc_name', 'Attachment'),
                'type': 'binary',
                'datas': base64.b64decode(doc_data),
                'res_model': 'account.move',
                'res_id': res_id,
                'res_name': res_name,
            }
            self.env['ir.attachment'].create(attachment_data)

        if not res_id:
            raise ValidationError(_("Document not created!"))

        return res_id

