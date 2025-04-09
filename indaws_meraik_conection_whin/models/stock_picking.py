import json
import base64
from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    response = fields.Text(string="Response", copy=False)

    def process_response(self, vals_response):
        response = vals_response.get('response', False)
        json_response = json.loads(response)

        supplier_id = json_response.get('supplier_id', False)
        supplier_name = json_response.get('supplier_name', False)
        delivery_note_number = json_response.get('delivery_note_number', False)
        receipt_date = json_response.get('receipt_date', False)
        notes = json_response.get('notes', False)

        if notes == 'not_found':
            notes = False

        # Agrupar los productos por pedido de compra
        purchase_orders_data = {}
        for item in json_response.get('item_list', []):
            purchase_order_number = item.get('related_purchase_order', False)
            if purchase_order_number not in purchase_orders_data:
                purchase_orders_data[purchase_order_number] = []
            purchase_orders_data[purchase_order_number].append(item)

        # Procesar cada pedido de compra relacionado
        for purchase_order_number, items in purchase_orders_data.items():
            purchase_order = self.env['purchase.order'].search([('name', '=', purchase_order_number)], limit=1)

            # Si no hay un pedido de compra, saltamos este grupo
            if not purchase_order:
                continue

            # Buscar un albarán existente asociado a este pedido
            stock_picking = self.env['stock.picking'].search([
                ('origin', '=', purchase_order_number),
                ('state', 'not in', ['done', 'cancel'])  # Solo si no está finalizado o cancelado
            ], limit=1)

            move_data = []
            for item in items:
                product_id = int(item.get('product_id', False))
                received_qty = item.get('received_qty', False)
                description = item.get('description', False)
                product_uom = item.get('product_uom', False)

                if not product_uom:
                    product_uom = self.env['product.product'].browse(product_id).uom_id.id

                # Buscar la línea del pedido de compra correspondiente
                purchase_order_line = purchase_order.order_line.filtered(lambda l: l.product_id.id == product_id)

                # Determinar locations (se basan en el tipo de picking)
                location_id = stock_picking.location_id.id if stock_picking else purchase_order.picking_type_id.default_location_src_id.id
                location_dest_id = stock_picking.location_dest_id.id if stock_picking else purchase_order.picking_type_id.default_location_dest_id.id

                if stock_picking:
                    move = stock_picking.move_ids.filtered(lambda m: m.product_id.id == product_id)
                    if move:
                        # ✅ Si la línea ya existe, actualizar cantidad
                        move.write({'quantity': received_qty})
                    else:
                        # ✅ Si la línea no existe, agregarla
                        move_data.append((0, 0, {
                            'product_id': product_id,
                            'quantity': received_qty,
                            'name': description,
                            'product_uom': product_uom,
                            'purchase_line_id': purchase_order_line.id if purchase_order_line else False,
                            'location_id': location_id,
                            'location_dest_id': location_dest_id
                        }))
                else:
                    # ✅ Si no existe un picking, preparar la nueva línea
                    move_data.append((0, 0, {
                        'product_id': product_id,
                        'quantity': received_qty,
                        'name': description,
                        'product_uom': product_uom,
                        'purchase_line_id': purchase_order_line.id if purchase_order_line else False,
                        'location_id': location_id,
                        'location_dest_id': location_dest_id
                    }))

            if stock_picking:
                # ✅ Si el picking ya existía, agregar solo las nuevas líneas sin borrar las existentes
                if move_data:
                    stock_picking.write({'move_ids': move_data})
                stock_picking.write({'note': notes})
            else:
                # ✅ Si no existe un albarán, crearlo con las líneas correspondientes
                stock_picking = self.env['stock.picking'].create({
                    'partner_id': supplier_id,
                    'origin': purchase_order_number,
                    'scheduled_date': receipt_date,
                    'note': notes,
                    'picking_type_id': purchase_order.picking_type_id.id,
                    'move_ids': move_data
                })

            stock_picking.write({'response': False})

            # Guardar la respuesta en el registro del albarán
            stock_picking.write({'response': response})

            # Si hay un documento adjunto, guardarlo
            if json_response.get('doc_data', False):
                doc_data = json_response.get('doc_data')
                attachment_data = {
                    'name': json_response.get('doc_name', 'Attachment'),
                    'type': 'binary',
                    'datas': base64.b64decode(doc_data),
                    'res_model': 'stock.picking',
                    'res_id': stock_picking.id,
                }
                self.env['ir.attachment'].create(attachment_data)

        return True
