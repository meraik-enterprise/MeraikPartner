# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
import json

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    response = fields.Text(string="Response")

    def get_list_of_employee_ids(self):
        employee_ids = self.env['hr.employee'].search([('company_id', '=', self.company_id.id)])
        list_of_ids = []
        for employee in employee_ids:
            list_of_ids.append({"odoo_id_employee":employee.id, "odoo_id_name":employee.name, "id_no": employee.identification_id, "pass_id": employee.passport_id, "extra_info": employee.extra_info})
        return list_of_ids

    def get_list_of_expense_product_ids(self):
        product_ids = self.env['product.product'].search([('company_id', '=', self.company_id.id),('can_be_expensed', '=', True)])
        list_of_ids = []
        for product in product_ids:
            #use description in expense category to provide more information of when to use this product
            list_of_ids.append({"odoo_id_product":product.id, "odoo_id_name":product.name, "default_code": product.default_code, "description": product.description})
        return list_of_ids

    def get_parse_info(self):
        return json.dumps({
            'odoo_id_employee': 'ID employee in Odoo in the json above',
            'name_employee': 'Name of the employee in the image',
            'total_amount_currency': 'Total amount in currency',
            'date': 'Date of the expense, Format: yyyy-mm-dd',
            'odoo_id_product': 'ID product in Odoo in the json above',
        })
    def get_image_from_pdf(self,attachment=False):
        if attachment:
            return attachment.datas
        return False

    def send_attachment_to_process(self):
        for record in self:
            if record.state in ['draft']:
                try:
                    base64_image = self.get_image_from_pdf(record.message_main_attachment_id)
                    list_of_ids = {
                        'input_employee_ids': self.get_list_of_employee_ids(),
                        'input_product_ids': self.get_list_of_expense_product_ids()
                    }
                    list_of_ids = json.dumps(list_of_ids)
                    parse_info = self.get_parse_info()
                    request_id = self.create_request(base64_image, list_of_ids, parse_info)
                    record.write({'meraik_request_id': request_id, 'response': False})
                    record.message_post(body=_('Request sent to Meraik AI Assistant.'))
                except Exception as e:
                    record.write({'response': e})
                    record.message_post(body=_('Error sending request to Meraik AI Assistant.\n%s') % e)
                    return False

    def create_request(self, base64_image, inputs={}, output_json={}):
        contract = self.env['meraik.contract'].search([('model_id.model', '=', self._name)], limit=1)
        if contract:
            request_id = contract.create_request(base64_image, inputs, output_json, self.id)
            return request_id
        return False

    def process_response(self, vals_response):
        response = vals_response.get('response', False)
        res_id = self.id if self.id else False
        json_response = json.loads(response)
        employee_id = json_response.get('employee_id', False)
        product_id = json_response.get('product_id', False)
        total_amount_currency = json_response.get('total_amount_currency', False)
        date = json_response.get('date', False)

        if res_id:
            self.write({
                'response': response,
                'employee_id': employee_id,
                'product_id': product_id,
                'total_amount_currency': total_amount_currency,
                'date': date
            })
        elif employee_id and product_id:
            res_id = self.env['hr.expense'].create({
                'name': _('New Expense'),
                'response': response,
                'employee_id': employee_id,
                'product_id': product_id,
                'total_amount_currency': total_amount_currency,
                'date': date
            })
        return res_id