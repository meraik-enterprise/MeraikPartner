# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
import base64
import json
from odoo.exceptions import UserError
import xmlrpc.client

class PayrollAiLog(models.Model):
    _name = 'payroll.ai.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Payroll AI Log'
    _order = 'id desc'

    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Attachement",
    )
    payroll_date = fields.Date(string="Payroll Date")
    response = fields.Text(string="Response")
    process_log = fields.Text(string="Process Log")
    state = fields.Selection([('pending', 'Pending'),('processing', 'Processing'),('success', 'Success'),('error','Error'),('error_processing', 'Error Processing'),('cancell','Canceled')],
                             string="State", default='pending', tracking=True, copy=False)
    num_tries = fields.Integer(string="Number of Tries", default=0, tracking=True, copy=False)
    employee_id = fields.Many2one(string="Employee", comodel_name="hr.employee", tracking=True, copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company, readonly=True)
    sent_to_employee = fields.Boolean(string="Sent to Employee", default=False, tracking=True, copy=False)
    sent_to_employee_date = fields.Datetime(string="Sent to Employee Date", tracking=True, copy=False)
    meraik_request_id = fields.Char(string="Meraik Request ID", tracking=True, copy=False)

    def get_list_of_ids(self):
        employee_ids = self.env['hr.employee'].search([('company_id', '=', self.company_id.id)])
        list_of_ids = []
        for employee in employee_ids:
            list_of_ids.append({"odoo_id_employee":employee.id, "odoo_id_name":employee.name, "id_no": employee.identification_id, "pass_id": employee.passport_id, "extra_info": employee.extra_info})
        return list_of_ids

    def get_parse_info(self):
        return json.dumps({
            'odoo_id_employee': 'ID empleado en Odoo en el json de arriba',
            'name_employee': 'Nombre del empleado en la imagen',
            'payroll_date': 'Fecha de nomina, Formato: yyyy-mm-dd',
        })
    def get_image_from_pdf(self,attachment=False):
        if attachment:
            return attachment.datas
        return False

    def mass_process_attachment_with_ai(self, limit=5):
        log_ids = self.env['payroll.ai.log'].search(['|',('state','in',['pending','processing']),'&',('state','in',['error','error_processing']),('num_tries','<',3)], limit=limit)
        for log in log_ids:
            if log.state != 'error_processing':
                log.write({'state': 'processing'})
            log.with_context(company_id=log.company_id.id).send_attachment_to_process()

    def send_attachment_to_process(self):
        for record in self:
            if record.state in ['pending','processing'] or (record.state == 'error' and record.num_tries < 3):
                try:
                    base64_image = self.get_image_from_pdf(record.attachment_id)
                    list_of_ids = {'input_employee_ids': self.get_list_of_ids()}
                    list_of_ids = json.dumps(list_of_ids)
                    parse_info = self.get_parse_info()
                    request_id = self.create_request(base64_image, list_of_ids, parse_info)
                    record.write({'state': 'processing', 'meraik_request_id': request_id, 'response': False})
                except Exception as e:
                    record.write({'response': e, 'state': 'error', 'num_tries': record.num_tries + 1})
                    # print(e)
                    return False

    def create_request(self, base64_image, inputs={}, output_json={}):
        contract = self.env['meraik.contract'].search([('model_id.model', '=', self._name)], limit=1)
        if contract:
            request_id = contract.create_request(base64_image, inputs, output_json, self.id)
            return request_id
        return False

    def process_response(self, response=False, state=False):
        try:
            api_answer = response if response else self.response
            remote_state = state if state else self.state
            if remote_state in ['error', 'cancell']:
                self.write({'response': api_answer, 'state': 'error', 'num_tries': self.num_tries + 1})
            else:
                self.write({'response': api_answer})
                self.find_employee()
        except Exception as e:
            self.write({'response': e, 'state': 'error', 'num_tries': self.num_tries + 1})
            # print(e)
            return False


    def find_employee(self):
        for record in self:
            try:
                json_response = json.loads(record.response)
                employee_id = int(json_response.get('odoo_id_employee', 0))
                employee = self.env['hr.employee'].browse(employee_id)
                date = json_response.get('payroll_date', False)
                if employee:
                    record.write({'employee_id': employee_id, 'state': 'success', 'payroll_date':date})
                    attachment_name = 'Nomina_' + date + '_' + employee.name + '.pdf'
                    record.attachment_id.write({'name': attachment_name})
                    if self.env['ir.config_parameter'].sudo().get_param('send_mail_to_employee', False):
                        record.send_mail_to_employee()
                    record.write({'state':'success'})
                    return json.dumps(json_response)
                else:
                    record.write({'state': 'error', 'num_tries': record.num_tries + 1, 'process_log': 'Employee not found'})
                    return False

            except Exception as e:
                record.write({'process_log': e, 'state': 'error', 'num_tries': record.num_tries + 1})
                return False
        return False

    def send_mail_to_employee(self):
        for record in self:
            if record.state == 'success' and record.employee_id and record.employee_id.work_email and not record.sent_to_employee:
                template = self.env.ref('indaws_payroll_ai_assistant.email_template_payroll_ai')
                mail_id = template.with_context(attachment_ids=record.attachment_id.ids).send_mail(record.id)
                mail = self.env['mail.mail'].browse(mail_id)
                vals = {'model': 'payroll.ai.log', 'res_id': record.id, 'attachment_ids': [(6, 0, record.attachment_id.ids)]}
                send_mail_planning = self.env['ir.config_parameter'].sudo().get_param('send_mail_planning', 'ontime')
                if send_mail_planning != 'ontime':
                    vals['scheduled_date'] = str(record.sent_to_employee_date)
                record.write({'sent_to_employee': True})
                mail.write(vals)
        return False

    def unlink(self):
        for record in self:
            if record.state in ['success']:
                raise UserError(_('You can not delete a record with state success'))
        return super(PayrollAiLog, self).unlink()

    def reset(self):
        self.write({'state':'pending', 'num_tries':0})