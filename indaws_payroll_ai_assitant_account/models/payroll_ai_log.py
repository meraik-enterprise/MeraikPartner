# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
import json

class PayrollAiLog(models.Model):
    _inherit = 'payroll.ai.log'

    account_move_id = fields.Many2one(string="Account Move", comodel_name="account.move")

    def get_parse_info(self):
        json_text = super(PayrollAiLog, self).get_parse_info()
        company_id = self.company_id
        json_json = json.loads(json_text)
        payroll_ai_account_move_id = self.env['payroll.ai.account.move'].with_context(company_id=company_id.id).search([('company_id','=',company_id.id)], limit=1)
        if payroll_ai_account_move_id and payroll_ai_account_move_id.payroll_ai_account_move_line_ids:
            for line in payroll_ai_account_move_id.payroll_ai_account_move_line_ids:
                json_json[line.json_key] = line.name + ' - ' + line.extra_info if line.extra_info else line.name
        return json.dumps(json_json)

    def find_employee(self):
        json_response = super(PayrollAiLog, self).find_employee()
        company_id = self.company_id
        if json_response:
            try:
                self.with_context(company_id=company_id.id).create_account_move(json_response)
            except Exception as e:
                # self.write({'state': 'error_processing', 'num_tries': self.num_tries + 1, 'process_log': 'Error creando asiento contable'})
                self.write({'state': 'error', 'num_tries': self.num_tries + 1, 'process_log': 'Error creando asiento contable'})
                return False
        return json_response

    def create_account_move(self, json_response):
        try:
            company_id = self.company_id
            json_response = json.loads(json_response)
            payroll_ai_account_move_id = self.env['payroll.ai.account.move'].with_context(
                company_id=company_id.id).search([('company_id', '=', company_id.id)], limit=1)
            if not payroll_ai_account_move_id:
                raise Exception(
                    'No se encontro la configuracion de asientos contables para la empresa: ' + self.company_id.name)
            partner_id = self.employee_id.user_id.partner_id if self.employee_id.user_id else False
            if payroll_ai_account_move_id and payroll_ai_account_move_id.payroll_ai_account_move_line_ids:
                account_move_line_ids = []
                for line in payroll_ai_account_move_id.payroll_ai_account_move_line_ids:
                    value_text = json_response.get(line.json_key, 0)
                    value = float(value_text)
                    if value:
                        if line.debit_expression:
                            account_id = eval('self.employee_id.' + line.debit_expression + '.id')
                            if not account_id:
                                if line.debit_account_id:
                                    account_id = line.debit_account_id.id
                                else:
                                    raise Exception(
                                        'No se encontro la cuenta contable para el empleado: ' + self.employee_id.name)
                            account_move_line_ids.append((0, 0, {
                                'name': line.name,
                                'account_id': account_id,
                                'debit': value,
                                'company_id': company_id.id,
                                'partner_id': partner_id.id if partner_id else False,
                            }))
                        elif line.debit_account_id:
                            account_move_line_ids.append((0, 0, {
                                'name': line.name,
                                'account_id': line.debit_account_id.id,
                                'debit': value,
                                'company_id': company_id.id,
                                'partner_id': partner_id.id if partner_id else False,
                            }))
                        elif line.credit_expression:
                            account_id = eval('self.employee_id.' + line.credit_expression + '.id')
                            if not account_id:
                                if line.credit_account_id:
                                    account_id = line.credit_account_id.id
                                else:
                                    raise Exception(
                                        'No se encontro la cuenta contable para el empleado: ' + self.employee_id.name)
                            account_move_line_ids.append((0, 0, {
                                'name': line.name,
                                'account_id': account_id,
                                'credit': value,
                                'company_id': company_id.id,
                                'partner_id': partner_id.id if partner_id else False,
                            }))
                        elif line.credit_account_id:
                            account_move_line_ids.append((0, 0, {
                                'name': line.name,
                                'account_id': line.credit_account_id.id,
                                'company_id': company_id.id,
                                'credit': value,
                                'partner_id': partner_id.id if partner_id else False,
                            }))

            journal_id = self.env['account.journal'].with_context(company_id=company_id.id).search(
                [('type', '=', 'general'),
                 ('company_id', '=', company_id.id)], limit=1)
            move_id = self.env['account.move'].with_context(company_id=company_id.id).sudo().create({
                'move_type': 'entry',
                'ref': 'Nomina ' + self.employee_id.name,
                'journal_id': journal_id.id,
                'date': str(self.payroll_date),
                'company_id': company_id.id,
                'line_ids': account_move_line_ids})

            if move_id and self.env['ir.config_parameter'].sudo().get_param('post_account_entry', False):
                move_id.action_post()
            self.sudo().write({'account_move_id': move_id.id})

        except Exception as e:
            # self.write({'state': 'error_processing', 'num_tries': self.num_tries + 1, 'process_log': 'Error creando asiento contable: ' + str(e)})
            self.write({'state': 'error', 'num_tries': self.num_tries + 1,
                        'process_log': 'Error creando asiento contable: ' + str(e)})
            return False

class AccountMOve(models.Model):
    _inherit = 'account.move'

    def create(self, vals):
        res = super(AccountMOve, self).create(vals)
        return res

