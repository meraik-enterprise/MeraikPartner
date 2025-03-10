# -*- coding: utf-8 -*-
# Part of Odoo.
# Copyright 2024 Bright3C - Aylen Garcés Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.osv import expression
from collections import defaultdict
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext, is_html_empty, email_normalize, plaintext2html
import requests
import logging
import random
import string
from datetime import datetime

_logger = logging.getLogger(__name__)


class ChatbotScriptStep(models.Model):
    _inherit = 'chatbot.script.step'

    triggering_answer_ids = fields.Many2many(  # comenting domain="[('script_step_id.sequence', '<', sequence)]",
        'chatbot.script.answer',
        compute='_compute_triggering_answer_ids', readonly=False, store=True,
        copy=False,  # copied manually, see chatbot.script#copy
        string='Only If', help='Show this step only if all of these answers have been selected.')

    step_cyclic = fields.Selection([('none', 'None'), ('end', 'End Point'), (
        'init', 'Init Pont')], string='Step Cyclic', default='none')

    def _fetch_next_step(self, selected_answer_ids):
        self.ensure_one()
        domain = [('chatbot_script_id', '=', self.chatbot_script_id.id),
                  ('step_cyclic', '=', 'init')]
        if selected_answer_ids:
            domain = expression.AND([domain, [
                '|',
                ('triggering_answer_ids', '=', False),
                ('triggering_answer_ids', 'in', selected_answer_ids.ids)]])

        steps = self.env['chatbot.script.step'].sudo().search(domain)
        return steps

    def _process_step(self, discuss_channel):
        """ When we reach a chatbot.step in the script we need to do some processing on behalf of
        the bot. Which is for most chatbot.script.step#step_types just posting the message field.

        Some extra processing may be required for special step types such as 'forward_operator',
        'create_lead', 'create_ticket' (in their related bridge modules).
        Those will have a dedicated processing method with specific docstrings.

        Returns the mail.message posted by the chatbot's operator_partner_id. """

        self.ensure_one()
        # We change the current step to the new step
        discuss_channel.chatbot_current_step_id = self.id

        if self.step_type == 'forward_operator':
            return self._process_step_forward_operator(discuss_channel)

        message_body = html2plaintext(
            discuss_channel.chatbot_message_ids[0].mail_message_id.body) if discuss_channel.chatbot_message_ids else ''
        response = discuss_channel.send_message(user_message=message_body)

        return discuss_channel._chatbot_post_message(self.chatbot_script_id, plaintext2html(response))
