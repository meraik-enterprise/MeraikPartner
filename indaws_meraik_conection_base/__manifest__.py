# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "MerAIk Connection Base",
    "summary": "Base module for Indaws-MerAIk connection",
    "version": "17.0.1.1.0",
    "category": "AI",
    "license": "AGPL-3",
    "website": "https://www.indaws.es/",
    "author": "MerAik,Aylen Garces",
    "depends": ["base","mail","base_automation"],
    "data": [
        "security/ir.model.access.csv",
        "views/meraik_contract.xml",
        "views/meraik_request_response.xml",
        "views/res_config_settings_views.xml",
        "views/menu.xml",
        "data/base_automation.xml",
    ],
    "installable": True,
    "auto_install": False,
}