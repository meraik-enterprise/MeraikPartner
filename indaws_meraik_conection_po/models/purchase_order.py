# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
import json
import base64

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    response = fields.Text(string="Response")
    def process_response(self, vals_response):
        response = vals_response.get('response', False)
        res_id = self.id if self.id else False
        res_name = self.name if self.name else ''

        json_response = json.loads(response)
        supplier_id = json_response.get('supplier_id', False)
        supplier_name = json_response.get('supplier_name', False)
        supplier_referece = json_response.get('purchase_order_number', False)
        date_order = json_response.get('order_date', False)
        notes = json_response.get('notes', False)
        if notes == 'not_found':
            notes = False

        po_line_data = []
        for item in json_response.get('item_list', []):
            product_id = int(item.get('product_id', False))
            product_qty = item.get('product_qty', False)
            price_unit = item.get('price_unit', False)
            description = item.get('description', False)
            product_uom = item.get('product_uom', False)
            if not product_uom:
                product_uom = self.env['product.product'].browse(product_id).uom_id.id
            po_line_data.append((0, 0, {
                'product_id': product_id,
                'product_qty': product_qty,
                'price_unit': price_unit,
                'name': description,
                'product_uom': product_uom
            }))


        if res_id:
            po = self.env['purchase.order'].browse(res_id)
            po.write({
                'order_line': [(5, 0, 0)]
            })

            po.write({
                'order_line': po_line_data
            })
            self.write({'response': response})
        elif supplier_id:
            po = self.env['purchase.order'].create({
                'partner_id': supplier_id,
                'partner_ref': supplier_referece,
                'date_order': date_order,
                'response': response,
                'notes': notes,
                'order_line': po_line_data
            })
            po.write({'response': response})
            res_id = po.id
            res_name = po.name

        if json_response.get('doc_data', False):
            doc_data = json_response.get('doc_data')
            attachment_data = {
                'name': json_response.get('doc_name', 'Attachment'),
                'type': 'binary',
                'datas': base64.b64decode(doc_data),
                'res_model': 'account.move',
                'res_id': res_id,
                'res_name': res_name,
            }
            self.env['ir.attachment'].create(attachment_data)

        return res_id