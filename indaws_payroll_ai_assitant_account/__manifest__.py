# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Indaws Payroll Assistant -ACCOUNT",
    "summary": "Indaws Payroll Assistant - ACCOUNT",
    "description": "This module expands the functionality of the Payroll AI Assistant module, adding the functionality of creating the accounting entries for the payroll.",
    "version": "17.0.1.1.0",
    "category": "HR",
    "license": "AGPL-3",
    "website": "https://www.indaws.es/",
    "author": "Aylen Garces, inDAWS",
    "depends": [
        "indaws_payroll_ai_assistant",
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/payroll_ai_account_move.xml",
        "views/payroll_ai_log_view.xml",
        "views/hr_employee_views.xml",
        "views/res_config_settings_views.xml",
        "data/data.xml",
    ],
    "installable": True,
    "auto_install": False,
}