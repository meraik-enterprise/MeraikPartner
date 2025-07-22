# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    url_remote = fields.Char(string="Remote server URL", config_parameter='url_remote')
    db_remote = fields.Char(string="Remote server DB Name", config_parameter='db_remote')
    username = fields.Char(string="User Remote Login", config_parameter='username')
    password = fields.Char(string="User Remote Password", config_parameter='password')