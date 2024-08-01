# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

class MeraikRequestResponse(models.Model):
    _name = 'meraik.request.response'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Meraik Request Response'

    contract_id = fields.Many2one('meraik.contract', string='Contract')
    request_remote_id = fields.Integer(string='Request Remote ID', copy=False, tracking=True)
    response_json = fields.Text(string='Response JSON', copy=False, tracking=True)
    response_date = fields.Datetime(string='Response Date', copy=False, tracking=True)
    state = fields.Selection(
        [('pending', 'Pending'), ('success', 'Success'), ('error', 'Error'), ('cancel', 'Canceled')],
        string="State", default='pending', tracking=True, copy=False)

    def check_result(self):
        pass
