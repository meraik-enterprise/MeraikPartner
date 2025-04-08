
from odoo import fields, models, _
import json
import base64
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    response = fields.Text(string="Response", copy=False)

    def process_response(self, vals_response):

        server_action = self.env.ref('indaws_meraik_conection_whin.action_process_response_stock_picking')
        response = vals_response.get('response', '{}')
        # move_json_str = server_action.with_context(vals_response=response).run()
        move_json_str = self.local_process(response)
        json_response = json.loads(response)
        _logger.info('move_json')
        _logger.info(move_json_str)
        move_json = json.loads(move_json_str)
        res_id = move_json.get('res_id', False)
        res_ids = move_json.get('res_ids', [])
        res_name = move_json.get('res_name', '')
        res_names = move_json.get('res_names', [])

        if json_response.get('doc_data', False) and res_id:
            doc_data = json_response.get('doc_data')
            attachment_data = {
                'name': json_response.get('doc_name', 'Attachment'),
                'type': 'binary',
                'datas': base64.b64decode(doc_data),
                'res_model': 'stock.picking',
                'res_id': res_id,
                'res_name': res_name,
            }
            self.env['ir.attachment'].create(attachment_data)

        elif json_response.get('doc_data', False) and len(res_ids):
            iterator = 0
            for rid in res_ids:
                doc_data = json_response.get('doc_data')
                attachment_data = {
                    'name': json_response.get('doc_name', 'Attachment'),
                    'type': 'binary',
                    'datas': base64.b64decode(doc_data),
                    'res_model': 'stock.picking',
                    'res_id': rid,
                    'res_name': res_names[iterator],
                }
                self.env['ir.attachment'].create(attachment_data)
                iterator += 1

        if not res_id and not len(res_ids):
            raise ValidationError(_("Document not created!"))

        return res_id if res_id else res_ids

    def local_process(self, vals_response):
        import json
        env = self.env

        json_response = json.loads(vals_response)

        # Función para limpiar valores
        def clean(value):
            return False if value in [None, 'not_found'] else value

        supplier_id = clean(json_response.get('supplier_id'))
        receipt_date = clean(json_response.get('receipt_date'))
        notes = clean(json_response.get('notes'))

        purchase_orders_data = {}
        for item in json_response.get('item_list', []):
            po_number = item.get('related_purchase_order')
            if po_number not in purchase_orders_data:
                purchase_orders_data[po_number] = []
            purchase_orders_data[po_number].append(item)

        res_ids = []
        res_names = []

        for po_number in purchase_orders_data:
            items = purchase_orders_data[po_number]

            purchase_order = env['purchase.order'].search([('name', '=', po_number)], limit=1)
            if not purchase_order:
                res_ids.append(False)
                res_names.append(False)
                continue

            # Buscar albarán existente
            stock_picking = env['stock.picking'].search([
                ('origin', '=', po_number),
                ('state', 'not in', ['done', 'cancel'])
            ], limit=1)

            move_data = []

            for item in items:
                product_id = int(item.get('product_id'))
                received_qty = item.get('received_qty', 0)
                description = item.get('description', '')
                product_uom = item.get('product_uom')

                # Recuperar UoM si no viene en el JSON
                if not product_uom:
                    product = env['product.product'].browse(product_id)
                    product_uom = product.uom_id.id if product else False

                # Línea del pedido correspondiente
                purchase_line = purchase_order.order_line.filtered(lambda l: l.product_id.id == product_id)
                purchase_line_id = purchase_line.id if purchase_line else False

                # Ubicaciones
                location_id = stock_picking.location_id.id if stock_picking else purchase_order.picking_type_id.default_location_src_id.id
                location_dest_id = stock_picking.location_dest_id.id if stock_picking else purchase_order.picking_type_id.default_location_dest_id.id

                if not location_id:
                    location_id = env['stock.location'].search([('usage', '=', 'supplier')], limit=1).id

                move_dict = {
                    'product_id': product_id,
                    'quantity': received_qty,
                    'name': description,
                    'product_uom': product_uom,
                    'purchase_line_id': purchase_line_id,
                    'location_id': location_id,
                    'location_dest_id': location_dest_id
                }

                if stock_picking:
                    move = stock_picking.move_ids.filtered(lambda m: m.product_id.id == product_id)
                    if move:
                        move.write({'quantity': received_qty})
                    else:
                        move_data.append((0, 0, move_dict))
                else:
                    move_data.append((0, 0, move_dict))

            if stock_picking:
                if move_data:
                    stock_picking.write({'move_ids': move_data})
                stock_picking.write({'note': notes})
            else:
                stock_picking = env['stock.picking'].create({
                    'partner_id': supplier_id,
                    'origin': po_number,
                    'scheduled_date': receipt_date,
                    'note': notes,
                    'picking_type_id': purchase_order.picking_type_id.id,
                    'move_ids': move_data
                })

            if stock_picking:
                stock_picking.write({'response': vals_response})
                res_ids.append(stock_picking.id)
                res_names.append(stock_picking.name)
            else:
                res_ids.append(False)
                res_names.append(False)

        return json.dumps({'res_ids': res_ids, 'res_names': res_names})

