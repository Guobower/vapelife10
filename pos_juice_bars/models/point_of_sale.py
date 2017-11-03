from openerp import models, fields, api, _
from odoo.tools import float_is_zero

class pos_order(models.Model):
    _inherit = "pos.order"


    def _get_subtotal_line_undiscounted(self,line,precision):
        return round(line.price_unit * line.qty, precision)

    @api.multi
    def _compute_total_discount(self):
        precision = self.env['decimal.precision'].precision_get('Account')
        for order in self:
            total_undiscounted = sum (self._get_subtotal_line_undiscounted(line,precision)  for line in order.lines)
            total_discounted = sum (line.price_subtotal for line in order.lines)
            discount = total_undiscounted - total_discounted
            try:
                discount_percentage = discount*100/total_undiscounted
            except ZeroDivisionError:
                discount_percentage = 0
            order.total_discount_given = discount
            order.discount_percentage = discount_percentage

    def create_picking(self):
        """Create a picking for each order and validate it."""
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        for order in self:
            if not order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                continue
            address = order.partner_id.address_get(['delivery']) or {}
            picking_type = order.picking_type_id
            return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
            order_picking = Picking
            return_picking = Picking
            moves = Move
            location_id = order.location_id.id
            if order.partner_id:
                destination_id = order.partner_id.property_stock_customer.id
            else:
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = StockWarehouse._get_partner_locations()
                    destination_id = customerloc.id
                else:
                    destination_id = picking_type.default_location_dest_id.id

            if picking_type:
                message = _(
                    "This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (
                          order.id, order.name)
                picking_vals = {
                    'origin': order.name,
                    'partner_id': address.get('delivery', False),
                    'date_done': order.date_order,
                    'picking_type_id': picking_type.id,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                }
                pos_qty = any([x.qty > 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
                if pos_qty:
                    order_picking = Picking.create(picking_vals.copy())
                    order_picking.message_post(body=message)
                neg_qty = any([x.qty < 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
                if neg_qty:
                    return_vals = picking_vals.copy()
                    return_vals.update({
                        'location_id': destination_id,
                        'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        'picking_type_id': return_pick_type.id
                    })
                    return_picking = Picking.create(return_vals)
                    return_picking.message_post(body=message)
            bar_ids = eval(self.env['ir.config_parameter'].get_param('pos_juice_bars.juice_bars_ids'))
            for line in order.lines.filtered(
                    lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty,
                                                                                              precision_digits=l.product_id.uom_id.rounding)):
                moves |= Move.create({
                    'name': line.name,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                    'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.qty),
                    'state': 'draft',
                    'location_id': location_id if line.qty >= 0 else destination_id,
                    'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                })
                # Editted by Shivam Goyal
                if line.product_id.id in bar_ids:
                    for j in line.mixture_line_id:
                        vol_attribute_value = line.product_id.attribute_value_ids.filtered(lambda attr: attr.attribute_id.nature == 'vol')
                        qty = vol_attribute_value.actual_value * j.mix * line.qty
                        moves |= Move.create({
                            'name': line.name,
                            'product_uom': j.product_id.uom_id.id,
                            'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                            'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                            'product_id': j.product_id.id,
                            'product_uom_qty': abs(qty),
                            'state': 'draft',
                            'location_id': location_id if line.qty >= 0 else destination_id,
                            'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        })

            # prefer associating the regular order picking, not the return
            order.write({'picking_id': order_picking.id or return_picking.id})

            if return_picking:
                order._force_picking_done(return_picking)
            if order_picking:
                order._force_picking_done(order_picking)

            # when the pos.config has no picking_type_id set only the moves will be created
            if moves and not return_picking and not order_picking:
                tracked_moves = moves.filtered(lambda move: move.product_id.tracking != 'none')
                untracked_moves = moves - tracked_moves
                tracked_moves.action_confirm()
                untracked_moves.action_assign()
                moves.filtered(lambda m: m.state in ['confirmed', 'waiting']).force_assign()
                moves.filtered(lambda m: m.product_id.tracking == 'none').action_done()

        return True


    total_discount_given = fields.Float(string='Discount', compute='_compute_total_discount', readonly=True)
    discount_percentage = fields.Float(string="Discount Percentage", compute='_compute_total_discount', readonly=True)

class pos_mixture_line(models.Model):
    _name = "pos.mixture.line"
    _description = "POS Mixture Line"

    line_id = fields.Many2one('pos.order.line',"POS Order Line")
    product_id = fields.Many2one('product.product',"Product",required=True)
    mix = fields.Float("Mix")



class pos_order_line(models.Model):
    _inherit = "pos.order.line"
    _description = "Lines of Point of Sale"


    mixture_line_id = fields.One2many('pos.mixture.line','line_id',string = 'Mixture')

