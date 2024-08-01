# Copyright 2024 Meraik - Aylen Garcés Fernández
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
import xmlrpc.client

class MeraikContract(models.Model):
    _name = "meraik.contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "MerAik Contract"

    name = fields.Char(string="Name", copy=False, default=lambda self: _('New'))
    remote_id = fields.Integer(string="Contract Remote ID", copy=False, tracking=True)
    state = fields.Selection([
        ('draft','Draft'),
        ('test','Test'),
        ('active','Active'),
        ('cancel','Canceled'),
        ('blocked','Blocked'),
    ], string='State', tracking=True, default='draft')
    meraik_request_response_ids = fields.One2many("meraik.request.response", "contract_id", string="Request Responses")
    request_qty = fields.Integer(string="Request Quantity", compute="_compute_request_qty")
    model_id = fields.Many2one('ir.model', string='Model Related', required=True, ondelete='cascade', index=True, tracking=True)

    def action_test_conection(self):
        try:
            url = self.env['ir.config_parameter'].sudo().get_param('url_remote', '')
            db = self.env['ir.config_parameter'].sudo().get_param('db_remote', '')
            username = self.env['ir.config_parameter'].sudo().get_param('username', '')
            password = self.env['ir.config_parameter'].sudo().get_param('password', '')
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
            uid = common.authenticate(db, username, password, {})
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
            remote_id = self.remote_id
            result = models.execute_kw(db, uid, password, 'ai.contract', 'read', [[remote_id], ['state', 'name']])
            self.write({'state': result[0]['state'],'name': result[0]['name']})
            message = _("Connection Test Successful!")
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
            message = _("Connection Test Failed! %s") % str(e)
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


    def _compute_request_qty(self):
        for record in self:
            record.request_qty = len(record.meraik_request_response_ids.ids)

    def action_view_request_responses(self):
        self.ensure_one()
        action = self.env.ref('indaws_meraik_conection_base.action_meraik_request_response').read()[0]
        action['domain'] = [('contract_id', '=', self.id)]
        return action




