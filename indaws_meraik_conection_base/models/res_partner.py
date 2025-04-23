# Copyright 2024 Meraik - Aylen Garcés Fernández
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    x_studio_meraik_extra_info = fields.Text(string="Meraik Extra Info")