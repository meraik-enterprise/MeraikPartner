# -*- coding: utf-8 -*-
# Part of Odoo.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
import json
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    response = fields.Text(string="Response")
    def process_response(self, vals_response):
        response = vals_response.get('response', False)
        res_id = self.id if self.id else False

        json_response = json.loads(response)
        client_id = json_response.get('client_id', False)
        client_name = json_response.get('client_name', False)
        order_referece = json_response.get('sale_order_number', False)
        date_order = json_response.get('order_date', False)
        notes = json_response.get('notes', False)

        so_line_data = []
        for item in json_response.get('item_list', []):
            product_id = int(item.get('product_id', False))
            product_qty = item.get('product_qty', False)
            price_unit = item.get('price_unit', False)
            description = item.get('description', False)
            product_uom = item.get('product_uom', False)
            if not product_uom:
                product_uom = self.env['product.product'].browse(product_id).uom_id.id
            so_line_data.append((0, 0, {
                'product_id': product_id,
                'product_qty': product_qty,
                'price_unit': price_unit,
                'name': description,
                'product_uom': product_uom
            }))

        if res_id:
            so = self.env['sale.order'].browse(res_id)
            so.write({
                'order_line': [(5, 0, 0)]
            })
            so.write({
                'order_line': so_line_data
            })
            self.write({'response': response})
        elif client_id:
            so = self.env['sale.order'].create({
                'partner_id': client_id,
                'client_order_ref': order_referece,
                'date_order': date_order,
                'response': response,
                'order_line': so_line_data
            })
            so.write({'response': response})
            res_id = so.id
        return res_id