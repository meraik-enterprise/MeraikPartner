# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ir_cron(models.Model):
    _inherit = "ir.cron"

    def write(self, vals):
        for rec in self:
            if self.env.ref('indaws_payroll_ai_assistant.process_payroll_ai_log') == rec:
                log_ids = self.env['payroll.ai.log'].search(
                    ['|', ('state', 'in', ['pending', 'processing']), '&', ('state', 'in', ['error', 'error_processing']),('num_tries', '<', 3)])
                if not log_ids:
                    vals['active'] = False

        return super(ir_cron, self).write(vals)
