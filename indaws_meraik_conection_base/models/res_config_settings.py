# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    url_remote = fields.Char(string="Remote server URL", config_parameter='indaws_meraik_conection_base.url_remote')
    db_remote = fields.Char(string="Remote server DB Name", config_parameter='indaws_meraik_conection_base.db_remote')
    username = fields.Char(string="User Remote Login", config_parameter='indaws_meraik_conection_base.username')
    password = fields.Char(string="User Remote Password", config_parameter='indaws_meraik_conection_base.password')