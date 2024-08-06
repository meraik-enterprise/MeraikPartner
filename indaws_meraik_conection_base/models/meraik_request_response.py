# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
class MeraikRequestResponse(models.Model):
    _name = 'meraik.request.response'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Meraik Request Response'

    contract_id = fields.Many2one('meraik.contract', string='Contract', ondelete='cascade', required=True, tracking=True)
    request_remote_id = fields.Integer(string='Request Remote ID', copy=False, tracking=True)
    response_json = fields.Text(string='Response JSON', copy=False, tracking=True)
    response_date = fields.Datetime(string='Response Date', copy=False, tracking=True)
    state = fields.Selection(
        [('pending', 'Pending'), ('success', 'Success'), ('error', 'Error'), ('error_doc_processing','Error Document'),('cancel', 'Canceled')],
        string="State", default='pending', tracking=True, copy=False)
    model_id = fields.Many2one('ir.model', string='Model Related', related='contract_id.model_id', store=True)
    res_id = fields.Integer(string='Record ID', copy=False, tracking=True)

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
        if 'state' in vals and vals['state'] == 'success' and not self._context.get('process_document', True):
            self.process_document()
        return res

    def create(self, vals):
        if 'state' in vals and vals['state'] != 'pending' and not vals.get('response_date'):
            vals['response_date'] = str(fields.Datetime.now())
        return super(MeraikRequestResponse, self).create(vals)

    def open_document(self):
        if not self.model_id or not self.res_id:
            return False
        return {
            'view_mode': 'form',
            'res_model': self.model_id.model,
            'res_id': self.res_id,
            'type': 'ir.actions.act_window',
        }

    def process_document(self):
        for record in self:
            try:
                vals_response = {}
                vals_response['response'] = record.response_json
                vals_response['state'] = record.state
                if record.model_id and record.res_id:
                    self.env[record.model_id.model].browse(record.res_id).process_response(vals_response)
                else:
                    res_id = self.env[record.model_id.model].process_response(vals_response)
                    record.write({'res_id': res_id})
                if record.state == 'error_doc_processing':
                    record.with_context(process_document=False).write({'state': 'success'})
            except Exception as e:
                record.message_post(body=_('Error processing document: %s') % str(e))
                record.write({'state': 'error_doc_processing'})
        return False