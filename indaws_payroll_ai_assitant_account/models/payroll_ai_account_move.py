# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

class PayrollAiAccountMove(models.Model):
    _name = 'payroll.ai.account.move'
    _description = 'Payroll AI Account Move'
    _order = 'id desc'

    name = fields.Char(string="Payroll AI Account Move", required=True)
    payroll_ai_account_move_line_ids = fields.One2many(string="Payroll AI Account Move Line", comodel_name="payroll.ai.account.move.line", inverse_name="payroll_ai_account_move_id", copy=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)

class PayrollAiAccountMoveLine(models.Model):
    _name = 'payroll.ai.account.move.line'
    _description = 'Payroll AI Account Move Line'
    _order = 'sequence asc, id asc'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    json_key = fields.Char(string="JSON Key", required=True)
    payroll_ai_account_move_id = fields.Many2one(string="Payroll AI Account Move", comodel_name="payroll.ai.account.move", required=True, ondelete="cascade")
    company_id = fields.Many2one('res.company', 'Company', related="payroll_ai_account_move_id.company_id", store=True,
                                 readonly=True, copy=False)
    debit_account_id = fields.Many2one(string="Account Debit", comodel_name="account.account", copy=False)
    credit_account_id = fields.Many2one(string="Account Credit", comodel_name="account.account", copy=False)
    debit_expression = fields.Char(string="Expression Debit")
    credit_expression = fields.Char(string="Expression Credit")
    extra_info = fields.Char(string="Extra Info")


