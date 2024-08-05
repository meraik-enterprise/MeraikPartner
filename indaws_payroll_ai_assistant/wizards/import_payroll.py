# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
import io
import base64
import PyPDF2


class ImportPayroll(models.TransientModel):
    _name = "import.payroll"
    _description = "Response Wizard"

    file = fields.Binary(string="File")
    file_name = fields.Char(string="File Name")

    def import_confirm(self):
        # store data in pdfReader
        pdfReader = PyPDF2.PdfFileReader(io.BytesIO(base64.b64decode(self.file)))

        # count number of pages
        totalPages = pdfReader.getNumPages()
        if totalPages == 1:
            step = page = 1
        else:
            step = page = int(self.env['ir.config_parameter'].sudo().get_param('how_many_pages',1))
        new_files = []

        while page <= totalPages:  #pagination of the split
            name = self.file_name + '-p' + str(page)
            new_files.append({
                'name': name,
                'new_pages': [{'old_file_index': 0, 'old_page_number': page}]
            })
            page += step

        open_files = [io.BytesIO(base64.b64decode(self.file))]

        new_attachments =self.env['ir.attachment']._pdf_split(new_files=new_files,open_files=open_files)

        ids = []

        send_mail_to_employee = self.env['ir.config_parameter'].sudo().get_param('send_mail_to_employee', False)
        send_mail_planning = self.env['ir.config_parameter'].sudo().get_param('send_mail_planning', 'ontime')
        send_mail_planning_day = self.env['ir.config_parameter'].sudo().get_param('send_mail_planning_day', 5)
        sent_to_employee_date = False

        if send_mail_to_employee:
            if send_mail_planning == 'dayofmonth':
                sent_to_employee_date = fields.Date.today()
                if send_mail_planning_day and sent_to_employee_date.day < int(send_mail_planning_day):
                    sent_to_employee_date = sent_to_employee_date.replace(day=int(send_mail_planning_day))
                elif send_mail_planning_day and sent_to_employee_date.day > int(send_mail_planning_day):
                    sent_to_employee_date = sent_to_employee_date.replace(day=int(send_mail_planning_day), month=sent_to_employee_date.month+1)

        for attachment in new_attachments:
            payroll_ai_log_id = self.env['payroll.ai.log'].create({
                'attachment_id': attachment.id,
                'sent_to_employee_date': sent_to_employee_date,
            })
            ids.append(payroll_ai_log_id.id)

        action = self.env['ir.actions.act_window']._for_xml_id('indaws_payroll_ai_assistant.action_payroll_ai_log')
        action['domain'] = [('id', 'in', ids)]

        cron_id = self.env.ref('indaws_payroll_ai_assistant.process_payroll_ai_log')
        cron_id.write({'active': True, 'nextcall': fields.Datetime.now()})

        return action


