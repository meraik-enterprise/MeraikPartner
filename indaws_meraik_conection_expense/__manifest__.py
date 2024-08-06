# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "MerAik Indaws Expenses",
    "summary": "MerAik Indaws Expenses",
    "description": "This module allows you to connect expenses with MerAik",
    "version": "17.0.1.1.0",
    "category": "HR",
    "license": "AGPL-3",
    "website": "https://www.indaws.es/",
    "author": "MerAik, Aylen Garces, inDAWS",
    "depends": ["hr_expense","indaws_meraik_conection_base"],
    "data": [
        "views/hr_expense_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}