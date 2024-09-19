# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
import json
import base64

class AccountMove(models.Model):
    _inherit = 'account.move'

    response = fields.Text(string="Response")
    def process_response(self, vals_response):
        response = vals_response.get('response', False)
        res_id = self.id if self.id else False
        res_name = self.name if self.name else ''

        json_response = json.loads(response)

        #vendor bills
        if json_response.get('vendor_bill_number', False):
            supplier_id = json_response.get('supplier_id', False)
            supplier_name = json_response.get('supplier_name', False)
            supplier_referece = json_response.get('vendor_bill_number', False)
            date_order = json_response.get('order_date', False)
            notes = json_response.get('notes', False)
            if notes == 'not_found':
                notes = False

            invoice_line_data = []
            for item in json_response.get('item_list', []):
                product_id = int(item.get('product_id', False))
                product_qty = item.get('product_qty', False)
                price_unit = item.get('price_unit', False)
                description = item.get('description', False)
                product_uom = item.get('product_uom', False)
                if not product_uom:
                    product_uom = self.env['product.product'].browse(product_id).uom_id.id
                invoice_line_data.append((0, 0, {
                    'product_id': product_id,
                    'quantity': product_qty,
                    'price_unit': price_unit,
                    # 'name': description,
                    'product_uom_id': product_uom
                }))

            if res_id:
                am = self.env['purchase.order'].browse(res_id)
                am.write({
                    'invoice_line_ids': [(5, 0, 0)]
                })

                am.write({
                    'invoice_line_ids': invoice_line_data
                })
                self.write({'response': response})
            elif supplier_id:
                am = self.env['account.move'].create({
                    'partner_id': supplier_id,
                    'ref': supplier_referece,
                    'invoice_date': date_order,
                    'response': response,
                    'narration': notes,
                    'move_type':'in_invoice',
                    'invoice_line_ids': invoice_line_data
                })
                am.write({'response': response})
                res_id = am.id
                res_name = am.name

            if json_response.get('doc_data', False):
                doc_data = json_response.get('doc_data')
                attachment_data = {
                    'name': json_response.get('doc_name','Attachment'),
                    'type': 'binary',
                    'datas': base64.b64decode(doc_data),
                    'res_model': 'account.move',
                    'res_id': res_id,
                    'res_name': res_name,
                }
                self.env['ir.attachment'].create(attachment_data)


        return res_id