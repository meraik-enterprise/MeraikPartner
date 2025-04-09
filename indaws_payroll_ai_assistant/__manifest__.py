# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "MerAik Indaws Payroll AI assistant",
    "summary": "Payroll AI assistant",
    "description": "This module allows you to split payroll PDFs into multiple PDFs and send to employees by email.",
    "version": "18.0.1.1.0",
    "category": "HR",
    "license": "AGPL-3",
    "website": "https://www.indaws.es/",
    "author": "MerAik, Aylen Garces, inDAWS",
    "depends": ["hr", "portal","documents","indaws_meraik_conection_base"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/payroll_ai_log_view.xml",
        "views/hr_employee_views.xml",
        "views/res_config_settings_views.xml",
        "views/doc_payroll_portal_templates.xml",
        "wizards/import_payroll.xml",
        "data/cron.xml",
        "data/mail_template.xml",
    ],
    "installable": True,
    "auto_install": False,
}