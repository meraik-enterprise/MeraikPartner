# -*- coding: utf-8 -*-
# Part of Odoo.
# Copyright 2024 Bright3C - Aylen Garcés Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Meraik Livechat Cyclic",
    "summary": "Meraik Livechat Cyclic",
    "version": "18.0.0.0.1",
    "license": "AGPL-3",
    # "website": "https://www.bright3c.com/",
    "author": "Meraik, Aylen Garcés, Indaws",
    "depends": ["im_livechat"],
    "data": [
        "views/chatbot_script_step_views.xml",
        "views/im_livechat_channel_views.xml",
    ],
    "installable": True,
}