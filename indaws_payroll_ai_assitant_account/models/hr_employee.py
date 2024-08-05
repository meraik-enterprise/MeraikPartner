# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    account_id_total_devengado = fields.Many2one(string="Cuenta Total Devengado", comodel_name="account.account", company_dependent=True)
    account_id_rem_pendiente = fields.Many2one(string="Cuenta Rem. Pendiente", comodel_name="account.account", company_dependent=True)
    account_id_ss = fields.Many2one(string="Cuenta SS", comodel_name="account.account", company_dependent=True)
    account_id_ret_embargo = fields.Many2one(string="Cuenta Retención Embargo", comodel_name="account.account", company_dependent=True)
    account_id_anticipo = fields.Many2one(string="Cuenta Anticipo", comodel_name="account.account", company_dependent=True)