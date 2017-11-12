from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = "stock.picking"
    _description = "Stock Picking Wholesale POS"
    
    
    @api.one
    def get_print_tabular_data(self):
        total_product_ids = {}
        invoice_lines = {'total':0.00,'paid':0.00,'residual':0.00,'invoice':{}}
        for line in self.move_lines: 
            # Here if and else condition will take care of the case where we a product repeating multiple times
            if line.product_id.id in total_product_ids.keys():
                total_product_ids[line.product_id.id] += line.product_uom_qty
            else:
                total_product_ids.update({line.product_id.id:line.product_uom_qty})
        tab_product_ids = [] # product_ids that belong to tab
        without_tab_product_ids = [] # product_ids that do not beong to tab
        shipping_product_id = self.env['ir.values'].sudo().get_default('sale.config.settings', 'shipping_product_id')
        tab_object = self.env['product.tab']
        product_object = self.env['product.product']
        p_attr_val_object = self.env['product.attribute.value']
        tab_data = {}
        tab_count = {}
        tabs = {}
        flavors = {}
        concentrations = {}
        products = {}
        total_count = 0.0
        order_note = self.sale_note
        paid_stamp = True
        if not self.move_lines:
            return {
                    'tab_data':tab_data,
                    'tabs':tabs,
                    'flavors':flavors,
                    'concentrations':concentrations,
                    'products':products,
                    'shipping':True,
                    'tab_count':tab_count,
                    'total_count':total_count,
                    'order_note':order_note,
                    'invoice_lines':invoice_lines,
                    'paid_stamp':False,
                }            
        if self.sale_id:
            for invoice  in self.sale_id.invoice_ids:
                #Checking for the paid_stamp
                if invoice.state != 'cancel':
                    if invoice.state != 'paid':
                        paid_stamp = False
                    invoice_lines['invoice'].update({
                                            invoice.number or invoice.state:{'total':invoice.amount_total,'residual':invoice.residual,'paid':invoice.amount_total - invoice.residual}
                                         })
                    invoice_lines['total'] =  invoice_lines['total'] +  invoice.amount_total
                    invoice_lines['residual'] = invoice_lines['residual'] +  invoice.residual
                    invoice_lines['paid'] = invoice_lines['paid'] + (invoice.amount_total - invoice.residual)                    
        
        # Check if shipping is free
        shipping = self.sale_id and len(self.sale_id.order_line.filtered(lambda x:x.product_id.id == shipping_product_id)) > 0 or False        
        # This query gives me  0:product_id,1:vol_id,2:conc_id,3:flavor_id,4:tab_id only for those products which belong to concentration matrix tab
        self.env.cr.execute('''
            select vol.product_product_id,vol.product_attribute_value_id,conc.product_attribute_value_id,flav.product_attribute_value_id,ptpp.tab_id
            from (select * from product_attribute_value_product_product_rel as a 
            left join product_attribute_value as pav on pav.id = a.product_attribute_value_id 
            left join product_attribute as pa on pa.id = pav.attribute_id
            where pa.nature = 'vol' ) as vol
            left join 
            (select * from product_attribute_value_product_product_rel as b 
            left join product_attribute_value as pav on pav.id = b.product_attribute_value_id 
            left join product_attribute as pa on pa.id = pav.attribute_id
            where pa.nature = 'conc') as conc on vol.product_product_id = conc.product_product_id
            left join 
            (select * from product_attribute_value_product_product_rel as c 
            left join product_attribute_value as pav on pav.id = c.product_attribute_value_id 
            left join product_attribute as pa on pa.id = pav.attribute_id
            where pa.nature = 'flav') as flav on vol.product_product_id = flav.product_product_id
            left join            
            product_tab_product_product as ptpp on ptpp.product_id = vol.product_product_id            
            where vol.product_product_id in (%s) and ptpp.tab_id is not null
        '''%((",").join(map(lambda id:str(id),total_product_ids.keys()))))
        
        res = self.env.cr.fetchall()
        
        # All the flavor concentration matrix data is organized to be printed
        for i in res:
            tab = tab_object.browse(i[4])
            if not tab.tab_style == 1: # Ensuring flavor concetration matrix
                continue
            product = product_object.browse(i[0])
            flavor = p_attr_val_object.browse(i[3])
            conc = p_attr_val_object.browse(i[2])
            total_count += total_product_ids[product.id]
            if tab.id in tabs.keys():
                # Check if the flavor exists
                t = tab_data[tab.id]
                if flavor.id in t.keys():
                    t[flavor.id].update({conc.id:(product.id,total_product_ids[product.id])})
                else:
                    # if the flavor does not exist
                    t.update({
                            flavor.id:{conc.id:(product.id,total_product_ids[product.id])}
                        })
                tabs[tab.id]['conc_ids'].append(conc.id)
                tabs[tab.id]['flavor_ids'].append(flavor.id)
                # Add it to the count
                if conc.id in tab_count[tab.id]:
                    tab_count[tab.id][conc.id]+=total_product_ids[product.id]
                else:
                    tab_count[tab.id][conc.id]=total_product_ids[product.id]
                
            else:
                tab_count.update({
                        tab.id:{
                                conc.id:total_product_ids[product.id]
                            }
                    })
                tabs.update(
                        {
                            tab.id:{
                                    'name':tab.name,
                                    'tab_style':tab.tab_style,
                                    'conc_ids':[conc.id],
                                    'flavor_ids':[flavor.id],
                                }
                        })
                tab_data.update({
                        tab.id:{
                                flavor.id:{conc.id:(product.id,total_product_ids[product.id])}
                            }
                    })
            flavors.update({flavor.id:flavor.name})
            concentrations.update({conc.id:conc.name})
            products.update({product.id:product.name})
            del total_product_ids[product.id]
        
        def _getConcName(id):
            return concentrations[id]
        
        def _getFlavorsName(id):
            return flavors[id]        
        
        # Now go through every tab to sort the concentrations and flavors based on names
        for tab in tabs:
            tabs[tab]['conc_ids'] = list(set(tabs[tab]['conc_ids']))
            tabs[tab]['flavor_ids'] = list(set(tabs[tab]['flavor_ids']))            
            tabs[tab]['conc_ids'] = sorted(tabs[tab]['conc_ids'],key = _getConcName)
            tabs[tab]['flavor_ids'] = sorted(tabs[tab]['flavor_ids'],key = _getFlavorsName)
            

        if total_product_ids:# if there are products still left then llok for products in list tab            
            # All the product which belong to a list  tab and do not belong to a tab
            self.env.cr.execute('''
                select tab_id,product_id from  product_tab_product_product 
                where product_id in (%s)
            '''%(",").join(map(lambda id:str(id),total_product_ids.keys())))
            res = self.env.cr.fetchall()
            # All the list type tab data is organized to be printed
            for i in res:
                # 1->(tab_id,product_id)
                tab = tab_object.browse(i[0])
                if not tab.tab_style == 2: # Ensuring list tab
                    continue            
                product = product_object.browse(i[1])
                total_count+=total_product_ids[product.id]
                if tab.id in tabs.keys():
                    tab_data[tab.id][product.id] = total_product_ids[product.id]
                    tab_count[tab.id]+=total_product_ids[product.id]
                    
                else:
                    tab_count.update({
                            tab.id:total_product_ids[product.id],
                        })
                    tabs.update(
                            {
                                tab.id:{
                                        'name':tab.name,
                                        'tab_style':tab.tab_style,
                                    }
                            })
                    tab_data.update({
                            tab.id:{
                                    product.id:total_product_ids[product.id]
                                }
                        })                
                products.update({product.id:product.name})
                del total_product_ids[product.id]
        
        if total_product_ids: # if there are products still left then they belong to miscllenaeous tab
        # Now only those products are left that belong to Miscellaneous tab.
        # The tab id for miscelleaneous is 0
        # First create miscellaneous tab
            tab_count.update({0:0.0})
            tabs.update({
                0:{
                    'name':"Miscellaneous",
                    'tab_style':3
                }
            })
            tab_data.update({
                    0:{}
                })
            for i in total_product_ids.keys():
                product =  product_object.browse(i)
                total_count+=total_product_ids[product.id] 
                if 0 in tabs.keys():
                    tab_data[0][product.id] = total_product_ids[product.id]
                    tab_count[0]+=total_product_ids[product.id]
                products.update({product.id:product.name})
                del total_product_ids[product.id]        
                
        return {
                'tab_data':tab_data,
                'tabs':tabs,
                'flavors':flavors,
                'concentrations':concentrations,
                'products':products,
                'shipping':shipping,
                'tab_count':tab_count,
                'total_count':total_count,
                'order_note':order_note,
                'invoice_lines':invoice_lines,
                'paid_stamp':paid_stamp,
            }
            
        
        
        
        
        