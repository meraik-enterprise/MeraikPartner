# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    payroll_ai_log_ids = fields.One2many(string="Payroll AI Logs", comodel_name="payroll.ai.log", inverse_name="employee_id")
    payroll_ai_log_count = fields.Integer(compute='_compute_payroll_ai_log_count')
    extra_info = fields.Char(string="Extra Info")

    def _compute_payroll_ai_log_count(self):
        # Method not optimized for batches since it is only used in the form view.
        for employee in self:
            if employee.payroll_ai_log_ids:
                employee.payroll_ai_log_count = len(employee.payroll_ai_log_ids.ids)
            else:
                employee.payroll_ai_log_count = 0

    def action_open_payroll_ai_logs(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('indaws_payroll_ai_assistant.action_payroll_ai_log')
        action['context'] = {
            'default_employee_id': self.id
        }
        action['domain'] = [('employee_id', '=', self.id)]
        return action

class ResUsers(models.Model):
    _inherit = 'res.users'
    def check_if_employee(self):
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.id)])
        if employee:
            return True
        return False