from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from odoo.exceptions import ValidationError
from datetime import date
from openerp import SUPERUSER_ID

_list_tab_style = [
    (1, "Flavor Concentration Matrix"),
    (2, "Products List"),
]

_type_of_product = [
    ('consu', 'Consumable Product'),
    ('product', 'Stockable Product'),
]


class product_tab(models.Model):
    _name = "product.tab"
    _description = "Product Tab"
    _order = "sequence asc"

    @api.model
    def _create_pair(self):
        pairs = []
        for line in self.flavor_conc_line:
            flavor_id,vol_id = line.flavor_id,line.tab_id.vol_id
            for conc in line.conc_ids:
                pairs.append((flavor_id,vol_id,conc))
        return pairs

    @api.model
    def create(self,vals):
        result =  super(product_tab,self).create(vals)
        if (result.tab_style == 1) and result.flavor_conc_line :
            new_pairs = result._create_pair()
            result._create_pair_products(new_pairs = new_pairs)
        return result

    @api.multi
    def get_products_price(self,pricelist_id,partner_id):
        pricelist  = self.env['product.pricelist'].search([('id','=',pricelist_id[0])])
        partner = self.env['res.partner'].search([('id','=',partner_id)])
        product_qty_partner = map(lambda p: (p, 1, partner), self.product_ids)
        res = pricelist._compute_price_rule(product_qty_partner)
        return res

    @api.model
    def _delete_product(self,pairs):
        #(flavor_id,vol_id,conc_id) ---> pair
        product_obj = self.env['product.product']
        product_ids = []
        product_template_ids = []
        for pair in pairs:
            # Check if such product already exists. If yes then do not create. Just add it to Many2many field of the tab
            self.env.cr.execute('''
                select ptp.product_id,t.id from product_tab_product_product as ptp
                left join product_attribute_value_product_product_rel as a on a.product_product_id = ptp.product_id
                left join product_attribute_value_product_product_rel as b on a.product_product_id = b.product_product_id
                left join product_attribute_value_product_product_rel as c on b.product_product_id = c.product_product_id
                left join product_product as p on a.product_product_id = p.id
                left join product_template as t on p.product_tmpl_id = t.id
                where a.product_attribute_value_id = %s and b.product_attribute_value_id = %s and c.product_attribute_value_id = %s
                and p.active = True
            '''%(pair[0].id,pair[1].id,pair[2].id))
            products = self.env.cr.fetchall()
            if products:
                product_ids = product_ids + [product[0] for product in products]
                product_template_ids = product_template_ids + [product[1] for product in products]
                products = product_obj.search([('id','in',product_ids)]).unlink()
                templates = self.env['product.template'].search([('id','in',product_template_ids)]) 
                for j in templates:
                    if not j.product_variant_ids:
                        j.unlink()
        return True

    @api.multi
    def write(self,vals):
        # The list will contain tuples with the following position
        # 0:tab_id,1:(flavor_id,flavor name),2:vol_id,3:conc_id
        if vals.get('flavor_conc_line',False):
            existing_pairs,new_pairs = [],[]
            existing_pairs = self._create_pair()
            result =  super(product_tab,self).write(vals)
            new_pairs = self._create_pair()
            self._create_pair_products(existing_pairs,new_pairs)
        else:
            result =  super(product_tab,self).write(vals)

        if vals.get('vol_id',False):
            raise ValidationError("Cannot change the volume of tab once created")
        if vals.get('consumable_stockable',False):
            self.product_ids.write({'type':vals.get('consumable_stockable',False)})
        return result

    @api.model
    def _create_product(self,pairs):
        if not self.product_category_id:
            raise ValidationError("Product Category Required")
        #(flavor_id,vol_id,conc_id) ---> pair
        product_obj = self.env['product.product']
        template_obj = self.env['product.template']
        product_ids = []
        attribute_conc_id = self.env['product.attribute'].search([('nature','=','conc')],limit=1).id
        attribute_flavor_id = self.env['product.attribute'].search([('nature','=','flav')],limit=1).id
        attribute_vol_id = self.env['product.attribute'].search([('nature','=','vol')],limit=1).id
        created_product_template = {}
        for pair in pairs:
            # Check if a template exist which has same flavor, volume in the same tab . If yes then just add new concentration to it.
            # For the purpose first check if a product exists with same config and then find its template
            self.env.cr.execute('''
                select pt.id
                from (select * from product_attribute_value_product_product_rel as a 
                left join product_attribute_value as pav on pav.id = a.product_attribute_value_id 
                left join product_attribute as pa on pa.id = pav.attribute_id
                where pa.nature = 'vol' ) as vol
                left join 
                (select * from product_attribute_value_product_product_rel as b 
                left join product_attribute_value as pav on pav.id = b.product_attribute_value_id 
                left join product_attribute as pa on pa.id = pav.attribute_id
                where pa.nature = 'flav') as flav on vol.product_product_id = flav.product_product_id
                left join 
                product_tab_product_product as ptpp on ptpp.product_id = vol.product_product_id
                left join 
                product_product as p on p.id = vol.product_product_id
                left join
                product_template as pt on pt.id = p.product_tmpl_id    
                where vol.product_attribute_value_id = %s and flav.product_attribute_value_id = %s and ptpp.tab_id = %s
                limit 1     
            '''%(pair[1].id,pair[0].id,self.id))
            product_template = self.env.cr.fetchone()
            template = False
            if product_template:
                template = template_obj.search([('id','=',product_template[0])])
            elif pair[0].id in created_product_template.keys():
                # This is so that the templates those are created live but have not been written to DB but will be written when the function terminates
                template = created_product_template[pair[0].id]
            if template:
                # Look for attribute_line_ids which has concentration attribute
                line_id = template.attribute_line_ids.filtered(lambda l: l.attribute_id.id == attribute_conc_id)
                current_product_variant_ids = template.product_variant_ids
                if line_id:
                        template.write({
                        'attribute_line_ids':[
                            [1, line_id[0].id, {'value_ids': [[6, False, map(lambda x: x.id,line_id.value_ids) + [pair[2].id] ]]}]
                        ]
                    })
                else: # if there is not concentration attribute associated witht the product
                    template.write({
                        'attribute_line_ids': [
                            [0, 0,{'value_ids': [(4,pair[2].id,False)],'attribute_id':attribute_conc_id,}]
                        ],
                    })
                product_ids = product_ids + [i.id for i in template.product_variant_ids - current_product_variant_ids]
                continue
            # This means there is no matchin product and prodct template hence create a new one
            # First create a template and then add the attributes to it
            vals = {
                    'name': " | ".join([self.name,pair[0].name, pair[1].name,pair[2].name]),
                    'type':self.consumable_stockable,
                    'sale_ok':True,
                    'purchase_ok':True,
                    'attribute_line_ids': [
                        (0, 0, {'attribute_id': attribute_flavor_id, 'value_ids': [(4, pair[0].id, False)]}),
                        (0,0,{'attribute_id':attribute_vol_id,'value_ids':[(4,pair[1].id,False)]}),
                        (0, 0, {'attribute_id': attribute_conc_id, 'value_ids': [(4, pair[2].id, False)]}),
                    ]
                }
            if self.uom_id:
                vals.update({'uom_id':self.uom_id.id,'uom_po_id':self.uom_id.id})
            tmpl = template_obj.create(vals)
            # This is stored so that other concentrations will not create seperate product template but add themselves as variant
            created_product_template.update({pair[0].id:tmpl}) 
            product_ids = product_ids + [i.id for i in tmpl.product_variant_ids]
        self.write({
            'product_ids':[(4,x,False) for x in list(set(product_ids))]
        })
        self.product_ids.write({'categ_id':self.product_category_id.id})
        return product_ids
    
    @api.model
    def _create_pair_products(self, existing_pairs=[], new_pairs=[]):
        '''
            * First check if existing pair are equal to new pairs. If yes then just do not do anything.
                If they are not equal then do the following.
                1. First find out the intersection (These pair will be kept as it is and not touched
                2. E - N will give us set of all the pairs that have been deleted
                3. N - E will give all set of the pairs that have to be created

            * the pairs will be list of tuple and the tuple will have the elements in position as follows (tab_id,flavor_id,vol_id,conc_id)
        '''
        e_minus_n = set(existing_pairs) - set(new_pairs)
        n_minus_e = set(new_pairs) - set(existing_pairs)
        created_product_ids = []
        if e_minus_n:
            self._delete_product(e_minus_n)
        if n_minus_e:
            created_product_ids.append(self._create_product(n_minus_e))
        return True


    @api.model
    def _get_attribute_domain(self):
        # We have access to self.env in this context.
        ids = self.env.ref('vapelife.volume_attribute').id
        return [('attribute_id','=', ids)]




    name = fields.Char('Tab Name', size=30, required=True)
    visible_all_customers = fields.Boolean("Visible to all Customers")
    specific_customer_ids = fields.Many2many('res.partner', 'product_tab_res_partners', 'tab_id', 'partner_id',
                                             string="Customers",
                                             help="List of Customer to whom this tab will be available to")
    tab_style = fields.Selection(_list_tab_style, string="Tab Style", required=True,
                                 help="These are options available that will format and determine the functionality of tab")
    product_ids = fields.Many2many('product.product', 'product_tab_product_product','tab_id','product_id','Products',
                                  help="List of products belonging to this tab")
    vol_id = fields.Many2one('product.attribute.value', "Volume", domain=_get_attribute_domain)
    consumable_stockable = fields.Selection(_type_of_product, "Type of Product", required=True)
    sequence = fields.Integer('Sequence')
    active = fields.Boolean("Active", default=True)
    uom_id = fields.Many2one('product.uom', 'Unit of Measure')
    flavor_conc_line = fields.One2many(
        'flavor.conc.details', 'tab_id', "Flavors & Concentration Details"
    )
    product_category_id = fields.Many2one('product.category',string = "Product Category")


class flavor_concentration_details(models.Model):
    _name = "flavor.conc.details"
    _description = "flavor and Concentration detail for tabs"

    @api.model
    def create(self, vals):
        return super(flavor_concentration_details, self).create(vals)

    @api.model
    def _get_flavor_domain(self):
        # We have access to self.env in this context.
        ids = self.env.ref('vapelife.flavor_attribute').id
        return [('attribute_id', '=', ids)]

    @api.model
    def _get_attribute_domain(self):
        # We have access to self.env in this context.
        ids = self.env.ref('vapelife.nicotine_attribute').id
        return [('attribute_id', '=', ids)]

    tab_id = fields.Many2one('product.tab', 'Tabs', ondelete='cascade', index=True)
    flavor_id = fields.Many2one('product.attribute.value', 'Flavor', domain=_get_flavor_domain)
    conc_ids = fields.Many2many('product.attribute.value', 'details_conc', 'detail_id', 'conc_id', 'Concentrations',
                                domain=_get_attribute_domain)