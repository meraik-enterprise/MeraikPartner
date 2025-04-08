# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "MerAik Indaws WHIN",
    "summary": "MerAik Indaws WHIN",
    "description": "This module allows you to connect incoming transfer with MerAik",
    "version": "17.0.1.1.0",
    "license": "AGPL-3",
    "website": "https://www.indaws.es/",
    "author": "MerAik, Aylen Garces, inDAWS",
    "depends": ["purchase","indaws_meraik_conection_base"],
    "data": [
        "data/server_action.xml",
    ],
    "installable": True,
    "auto_install": False,
}