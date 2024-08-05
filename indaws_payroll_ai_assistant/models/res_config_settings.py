# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    send_mail_to_employee = fields.Boolean(string="Send Mail to Employee",config_parameter='send_mail_to_employee')
    send_mail_planning = fields.Selection(string="Send Mail Planning",config_parameter='send_mail_planning', selection=[('ontime', 'On time'), ('dayofmonth', 'Day of month')], default='ontime')
    send_mail_planning_day = fields.Integer(string="Send Mail Planning Day",config_parameter='send_mail_planning_day', default=5)
    how_many_pages_per_employee = fields.Integer(string="How Many Pages per Employee",config_parameter='how_many_pages', default=1)