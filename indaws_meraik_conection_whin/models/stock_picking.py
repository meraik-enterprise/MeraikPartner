
from odoo import fields, models, _
import json
import base64
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    response = fields.Text(string="Response", copy=False)

    def process_response(self, vals_response):

        server_action = self.env.ref('indaws_meraik_conection_whin.action_process_response_stock_picking')
        response = vals_response.get('response', '{}')
        move_json_str = server_action.with_context(vals_response=response).run()
        json_response = json.loads(response)
        _logger.info('move_json')
        _logger.info(move_json_str)
        move_json = json.loads(move_json_str)
        res_id = move_json.get('res_id', False)
        res_ids = move_json.get('res_ids', [])
        res_name = move_json.get('res_name', '')
        res_names = move_json.get('res_names', [])

        if json_response.get('doc_data', False) and res_id:
            doc_data = json_response.get('doc_data')
            attachment_data = {
                'name': json_response.get('doc_name', 'Attachment'),
                'type': 'binary',
                'datas': base64.b64decode(doc_data),
                'res_model': 'stock.picking',
                'res_id': res_id,
                'res_name': res_name,
            }
            self.env['ir.attachment'].create(attachment_data)

        elif json_response.get('doc_data', False) and len(res_ids):
            iterator = 0
            for rid in res_ids:
                doc_data = json_response.get('doc_data')
                attachment_data = {
                    'name': json_response.get('doc_name', 'Attachment'),
                    'type': 'binary',
                    'datas': base64.b64decode(doc_data),
                    'res_model': 'stock.picking',
                    'res_id': rid,
                    'res_name': res_names[iterator],
                }
                self.env['ir.attachment'].create(attachment_data)
                iterator += 1

        if not res_id and not len(res_ids):
            raise ValidationError(_("Document not created!"))

        return res_id if res_id else res_ids

