# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import xmlrpc.client

class MeraikRequestResponse(models.Model):
    _name = 'meraik.request.response'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Meraik Request Response'

    contract_id = fields.Many2one('meraik.contract', string='Contract', ondelete='cascade', required=True, tracking=True)
    request_remote_id = fields.Integer(string='Request Remote ID', copy=False, tracking=True)
    response_json = fields.Text(string='Response JSON', copy=False, tracking=True)
    response_date = fields.Datetime(string='Response Date', copy=False, tracking=True)
    state = fields.Selection(
        [('pending', 'Pending'), ('success', 'Success'), ('error', 'Error'), ('cancel', 'Canceled')],
        string="State", default='pending', tracking=True, copy=False)
    model_id = fields.Many2one('ir.model', string='Model Related', related='contract_id.model_id', store=True)
    res_id = fields.Integer(string='Record ID', copy=False, tracking=True)

    def get_conection_info(self):
        url = self.env['ir.config_parameter'].sudo().get_param('url_remote', '')
        db = self.env['ir.config_parameter'].sudo().get_param('db_remote', '')
        username = self.env['ir.config_parameter'].sudo().get_param('username', '')
        password = self.env['ir.config_parameter'].sudo().get_param('password', '')
        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        return uid, password,db,models

    def check_result(self):
        try:
            remote_id = self.request_remote_id
            uid, password, db, models = self.get_conection_info()
            result = models.execute_kw(db, uid, password, 'ai.contract.request', 'read', [[remote_id], ['state', 'response']])
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
        return super(MeraikRequestResponse, self).write(vals)

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