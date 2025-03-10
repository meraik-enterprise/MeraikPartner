# -*- coding: utf-8 -*-
# Part of Odoo.
# Copyright 2024 Bright3C - Aylen Garcés Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import requests
import logging
import random
import string
from datetime import datetime

_logger = logging.getLogger(__name__)

class ImLivechatChannel(models.Model):
    _inherit = 'im_livechat.channel'

    chatbot_id = fields.Char(string="Chatbot ID", copy=False)
    api_key = fields.Char(string="API Key", copy=False)