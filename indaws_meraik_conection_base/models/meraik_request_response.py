# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class MeraikRequestResponse(models.Model):
    _name = 'meraik.request.response'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Meraik Request Response'
    _order = 'create_date desc'

    contract_id = fields.Many2one('meraik.contract', string='Contract', ondelete='cascade', required=True, tracking=True)
    request_remote_id = fields.Integer(string='Request Remote ID', copy=False, tracking=True)
    response_json = fields.Text(string='Response JSON', copy=False, tracking=True)
    response_date = fields.Datetime(string='Response Date', copy=False, tracking=True)
    state = fields.Selection(
        [('pending', 'Pending'), ('success', 'Success'), ('error', 'Error'), ('error_doc_processing','Error Document'),('cancel', 'Canceled')],
        string="State", default='pending', tracking=True, copy=False)
    model_id = fields.Many2one('ir.model', string='Model Related', related='contract_id.model_id', store=True)
    res_id = fields.Integer(string='Record ID', copy=False, tracking=True)
    res_ids = fields.Char(string='Record IDs', copy=False, tracking=True)

    def check_result(self):
        try:
            remote_id = self.request_remote_id
            uid, password, db, models = self.contract_id.get_conection_info()
            result = models.execute_kw(db, uid, password, 'ai.contract.request.doc', 'read', [[remote_id], ['state', 'response']])
            response_date = fields.Datetime.now()
            self.write({'state': result[0]['state'], 'response_json': result[0]['response'], 'response_date': response_date})
            message = _("Request Response Checked Successfully!")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            message = _("Request Response Check Failed! %s") % str(e)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message,
                    'type': 'danger',
                    'sticky': False,
                }
            }
            self.write({'state': 'test', 'name': result[0]['New']})

    def write(self, vals):
        if 'state' in vals and vals['state'] != 'pending' and not vals.get('response_date'):
            vals['response_date'] = str(fields.Datetime.now())
        res = super(MeraikRequestResponse, self).write(vals)
        _logger.info('WRITE LOG: state: %s, process_document: %s', vals.get('state','null'), self.env.context.get('process_document', 'null'))
        if 'state' in vals and vals['state'] == 'success' and self.env.context.get('process_document', False):
            self.process_document()

        return res

    def create(self, vals):
        if 'state' in vals and vals['state'] != 'pending' and not vals.get('response_date'):
            vals['response_date'] = str(fields.Datetime.now())
        res = super(MeraikRequestResponse, self).create(vals)
        _logger.info('CREATE LOG state: %s, process_document: %s', vals.get('state', 'null'),
                     self.env.context.get('process_document', 'null'))
        if res.state == 'success' and self.env.context.get('process_document', False):
            res.process_document()
        return res

    def open_document(self):
        if not self.model_id or (not self.res_id and not self.res_ids):
            return False
        elif self.model_id and self.res_id:
            document = self.env[self.model_id.model].search([('id', '=', self.res_id)])
            if not document:
                self.res_id = False
                return False
            return {
                'view_mode': 'form',
                'res_model': self.model_id.model,
                'res_id': self.res_id,
                'type': 'ir.actions.act_window',
            }
        elif self.model_id and self.res_ids:
            document = self.env[self.model_id.model].search([('id', 'in', self.res_ids.split(','))])
            if not document:
                self.res_ids = False
                return False
            return {
                'view_mode': 'tree,form',
                'res_model': self.model_id.model,
                'domain': [('id', 'in', self.res_ids.split(','))],
                'type': 'ir.actions.act_window',
            }

    def process_document(self):
        for record in self:
            try:
                vals_response = {}
                vals_response['response'] = record.response_json
                vals_response['state'] = record.state
                document = self.env[record.model_id.model].search([('id', '=', record.res_id)])
                if document:
                    document.process_response(vals_response)
                else:
                    res_ids = self.env[record.model_id.model].process_response(vals_response)

                    #if res_ids is a number or a list of numbers
                    if isinstance(res_ids, int):
                        record.write({'res_id': res_ids})
                    elif isinstance(res_ids, list):
                        record.write({'res_ids': ','.join(map(str, res_ids))})
                if record.state == 'error_doc_processing':
                    record.with_context(process_document=False).write({'state': 'success'})
            except Exception as e:
                record.message_post(body=_('Error processing document: %s') % str(e))
                record.write({'state': 'error_doc_processing'})
                record.send_feedback_to_platform(str(e))
        return False

    def send_feedback_to_platform(self, message_error):
        for record in self:
            try:
                message = 'Client Error: %s' % message_error
                remote_id = record.request_remote_id
                uid, password, db, models = record.contract_id.get_conection_info()
                models.execute_kw(db, uid, password, 'ai.contract.request.doc', 'write',
                                           [[remote_id], {'state': 'error', 'response': message}])
            except:
                record.message_post(body=_('Error sending feedback to platform'))