odoo.define("wholesale_pos.wholesale_pos",function(require){
"use strict";
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var core = require('web.core');
    var Model = require('web.DataModel');
    var screen = require('point_of_sale.screens');
    var exports = require("point_of_sale.models");
    var gui = require('point_of_sale.gui');
    var form_common = require('web.form_common');
    var utils = require("web.utils");
    var payment_plans = require('wholesale_pos.payment_plans');
    var QWeb = core.qweb;
    var _t = core._t;
    var FieldFloat = core.form_widget_registry.get('float');
    var FieldText = core.form_widget_registry.get('text');
    var framework = require('web.framework');
    var PopupWidget = require('point_of_sale.popups');
    
    
    FieldFloat.include({
    		initialize_content:function(){
    			this._super();
    			this.$el.addClass('text-center')
    		},
    })
    
    var InventoryPopUpWidget = PopupWidget.extend({
    		template: 'InventoryPopUp',
    		init:function(parent,options){
            var self = this;
            this.inventory_lines = [];
            this._super(parent,options)    			
    		},
    		show:function(inventory_lines){
    			var self = this;
    			self.inventory_lines = inventory_lines;
    			self._super();
    		},
    })
    gui.define_popup({name:'inventory', widget: InventoryPopUpWidget});
    
    var InventoryCollection = Backbone.Collection.extend({
    		check_available:function(product_id){
    			var product  = this.get(product_id)
    			var available = product.get('virtual_available') - product.get('incoming_qty')
    			return available
    		}
    })
    
    var round_di = function(val,prec){
    		return parseFloat(val.toFixed(prec));
    }
    exports.load_fields("res.partner",['property_product_pricelist'])
    exports.load_models([
        {
            model:'product.tab',
            label:"Product Tabs",
            fields:[],
            loaded: function(self,product_tabs){
                self.product_tabs = new Backbone.Collection(product_tabs)
            },
        },
        {
            model:'product.attribute',
            label:"Product Attribute",
            fields:[],
            loaded: function(self,product_attributes){
                self.product_attributes = new Backbone.Collection(product_attributes)
            },
        }
    ])
    var WholeSaleMatrixRow = PosBaseWidget.extend({
        init:function(parent,options){
            var self = this;
            this._super(parent,options);
            this.flavor = options.flavor || {};
            self.columns = {};
        },
        renderElement:function(){
            var self = this;
            self.$el = $("<tr><td>%FLAVOR%</td></tr>".replace('%FLAVOR%',this.flavor.get('name')));
            self.getParent().available_conc.each(function(conc){
                var column = $("<td class='text-center'><input type='text' style='width:50px;'  readonly></td>");
                self.columns[conc.get('id')] = column;
                self.$el.append(column)
            })
            self.price_element = new FieldFloat (self.getParent().dfm, {
                    attrs: {
                        name: "qty_price_"+remove_spaces(self.flavor.get('name')),
                        type: "float",
                        modifiers: '{"required": true}',
                    },
                });
            self.add_column(self.price_element,'60px')
            self.price_element.on('changed_value',self.price_element,function(event){
        			self.set_subtotal();
            })                        
            self.subtotal_element = new FieldFloat (self.getParent().dfm, {
                    attrs: {
                        name: "qty_subtotal_"+remove_spaces(self.flavor.get('name')),
                        type: "float",
                        modifiers: '{"required": true,"readonly":true}',
                    },
                });
            self.add_column(self.subtotal_element,'80px','danger');
        },
        update_price:function(price){
    			this.price_element.set_value(parseFloat(price.toFixed(2)));
        }, 
        get_price:function(){
        		return parseFloat(this.price_element.get_value());
        },
        get_col_qty:function(col_id){
        		var self = this;
        		var col = self.columns[col_id]
        		if (col instanceof FieldFloat){
        			return parseFloat(col.get_value()) || 0.00;	
        		}else{
        			return 0.00
        		}
        },
        get_total_qty:function(){
        		var self = this;
        		var total = 0.00;
        		_.each(self.columns,function(el,index){
        			if (el instanceof FieldFloat){
        				total = total + parseFloat(el.get_value());
        			}
        		});
        		return total;
        },
        get_subtotal:function(){
        		var total_qty = this.get_total_qty();
        		var subtotal  = total_qty * this.get_price();
        		return parseFloat(subtotal.toFixed(2))
        },
	    set_subtotal:function(){
    			this.subtotal_element.set_value(this.get_subtotal());
    			this.trigger("subtotal_changed",this)
	    },   
        get_line:function(line){
	    		var self = this;
	    		if ((line instanceof FieldFloat) &&  (parseFloat(line.get_value()) > 0 ) ){
		    		return {
						'product_uom_qty':parseFloat(line.get_value()),
						'product_id':line.get('product_id'),
						'price_unit':parseFloat(self.price_element.get_value()),
		    		}	    			
	    		}
	    		return false

	    },
	    get_lines:function(){
	    		var self = this;
	    		var lines = [];
	    		_.each(this.columns,function(col,index){
	    			var line = self.get_line(col);
	    			if (line){lines.push(line)}
	    		})
	    		return lines
	    },	   
	    check_inventory:function(inventory){
	    		var self = this;
	    		var invalid_inventory = [];
	    		_.each(self.columns,function(col){
	    			if (col instanceof FieldFloat){ // Check if the inventory value for this product exists in collection
	    				col.$el.css('background-color','white')
	    				var p = inventory.get(col.get('product_id'))
	    				if (p){
		    				var available = inventory.check_available(col.get('product_id'))
		    				if (available < parseFloat(col.get_value())){
		    					col.$el.css('background-color','#f2dede')
		    					invalid_inventory.push({
		    						'display_name':self.pos.db.product_by_id[col.get('product_id')].display_name,
		    						'tab_name':self.getParent().tab_data.get('name'),
		    						'required_qty':col.get_value(),
		    						'available_qty':available,
		    					})
		    				}	    					
	    				}
	    			}
	    		})
	    		return invalid_inventory
	    },
        add_column:function(element,width,context){
            var self = this;
            if (width == undefined){width='50px'}
            if (context){
	        		var column = $("<td class='text-center "+context+"' style='width:%WIDTH%;'></td>".replace('%WIDTH%',width));
	        }else{
	        		var column = $("<td class='text-center' style='width:%WIDTH%;'></td>".replace('%WIDTH%',width));
	        }
            element.appendTo(column);
            element.$el.css('width',width);
            column.appendTo(self.$el)
            element.on('changed_value',element,function(event){
        			self.set_subtotal();
            })                                    
            return element;
        },
        appendProduct:function(product,width){
            var self = this;
            if (width == undefined){width='50px'}
            var element = new FieldFloat (self.getParent().dfm, {
                    attrs: {
                        name: "qty_input_"+remove_spaces(product.display_name),
                        type: "float",
                        modifiers: '{"required": true}',
                    },
                });
            element.set('product_id',product.id)
            element.set('col_id',product.conc_id)
            self.columns[product.conc_id].empty();
            self.columns[product.conc_id].css('width',width)
            element.appendTo(self.columns[product.conc_id])
            element.$el.css('width',width);
            element.on("changed_value",element,function(event){
            		self.set_subtotal();
            		self.trigger("qty_changed",product.conc_id)
            })
            self.columns[product.conc_id] = element;
        }
    })

    var WholeSaleListRow = PosBaseWidget.extend({
        init:function(parent,options){
            var self = this;
            this._super(parent,options);
            this.product_id = options.product_id || {};
            this.tab_id = self.getParent().tab_data.get('id')
            this.columns = {};
        },
        renderElement:function(){
            var self = this;
            var product = self.pos.db.product_by_id[self.product_id];
            self.$el = $("<tr><td>%NAME%</td></tr>".replace('%NAME%',product.display_name));
            var qty_element = new FieldFloat (self.getParent().dfm, {
                    attrs: {
                        name: "qty_input_"+remove_spaces(product.display_name),
                        type: "float",
                        modifiers: '{"required": true}',
                    },
                });
            qty_element.set('product_id',product.id)
            qty_element.set('col_id',self.tab_id)
            self.add_column(qty_element);
            qty_element.on('changed_value',self,function(event){
        			self.set_subtotal();
        			self.trigger("qty_changed",self.getParent().tab_data.get('id'))        			
            })  
            self.columns[self.getParent().tab_data.get('id')] = qty_element;
            self.price_element = new FieldFloat (self.getParent().dfm, {
                    attrs: {
                        name: "qty_price_"+remove_spaces(product.display_name),
                        type: "float",
                        modifiers: '{"required": true}',
                    },
                });
            self.add_column(self.price_element,'60px');
            self.price_element.on('changed_value',self.price_element,function(event){
            		self.set_subtotal();
            })
            self.subtotal_element = new FieldFloat (self.getParent().dfm, {
                    attrs: {
                        name: "qty_subtotal_"+remove_spaces(product.display_name),
                        type: "float",
                        modifiers: '{"required": true,"readonly":true}',
                    },
                });
            self.add_column(self.subtotal_element,'80px',"danger");

        },
        get_line:function(line){
	    		var self = this;
	    		if ((line instanceof FieldFloat) &&  (parseFloat(line.get_value()) > 0 ) ){
		    		return {
						'product_uom_qty':parseFloat(line.get_value()),
						'product_id':line.get('product_id'),
						'price_unit':parseFloat(self.price_element.get_value()),
		    		}	    			
	    		}
	    		return false
	
	    },
	    check_inventory:function(inventory){
	    		var self = this;
	    		var invalid_inventory = [];
	    		_.each(self.columns,function(col){
	    			if (col instanceof FieldFloat){ // Check if the inventory value for this product exists in collection
	    				col.$el.css('background-color','white')
	    				var p = inventory.get(col.get('product_id'))
	    				if (p){
		    				var available = inventory.check_available(col.get('product_id'))
		    				if (available < parseFloat(col.get_value())){
		    					col.$el.css('background-color','#f2dede')
		    					invalid_inventory.push({
		    						'display_name':self.pos.db.product_by_id[col.get('product_id')].display_name,
		    						'tab_name':self.getParent().tab_data.get('name'),
		    						'required_qty':col.get_value(),
		    						'available_qty':available,
		    					})
		    				}	    					
	    				}
	    			}
	    		})
	    		return invalid_inventory
	    },
	    get_lines:function(){
	    		var self = this;
	    		var lines = [];
	    		_.each(this.columns,function(col,index){
	    			var line = self.get_line(col);
	    			if (line){lines.push(line)}
	    		})
	    		return lines
	    },	    
	    get_price:function(){
	    		return parseFloat(this.price_element.get_value());
	    },
        get_col_qty:function(col_id){
	    		var self = this;
	    		var col = self.columns[col_id]
	    		if (col instanceof FieldFloat){
	    			return parseFloat(col.get_value()) || 0.00;	
	    		}else{
	    			return 0.00
	    		}
	    },	    
	    get_total_qty:function(){
	    		return this.get_col_qty(this.tab_id);
	    },
	    get_subtotal:function(){
	    		var total_qty = this.get_total_qty();
	    		var subtotal  = total_qty * this.get_price();
	    		return round_di(subtotal,2);
	    },    
	    set_subtotal:function(){
	    		this.subtotal_element.set_value(this.get_subtotal());
	    		this.trigger("subtotal_changed",this)
	    },
        add_column:function(element,width,context){
            var self = this;
            if (width == undefined){width = '50px'}
            if (context){
            		var column = $("<td class='text-center "+context+"' style='width:%WIDTH%;'></td>".replace('%WIDTH%',width));
            }else{
            		var column = $("<td class='text-center' style='width:%WIDTH%;'></td>".replace('%WIDTH%',width));
            }
            
            element.appendTo(column);
            element.$el.css('width',width);
            column.appendTo(self.$el)
            return element;
        },
        update_price:function(price){
        		this.price_element.set_value(parseFloat(price.toFixed(2)));
        },
    })

	var remove_spaces = function(string){
		return string.replace(/\s/g, "");
	}

    var WholeSaleTab = PosBaseWidget.extend({
        init:function(parent,options){
            this._super(parent,options)
            this.tab_data = options.tab || {}; // This is tab model
            if (this.tab_data.get('tab_style') == 1){
                this.available_conc = new Backbone.Collection;
                this.available_conc.comparator = 'actual_value'
                this.available_vol = new Backbone.Collection;
                this.available_vol.comparator = 'actual_value'
                this.available_flavor = new Backbone.Collection
                this.available_flavor.comparator = 'name'
            }
            this.rows = {};
            this.dfm = new form_common.DefaultFieldManager(this);
            this.strength_element = {};
        },
        prepare_matrix_data:function(){
            var self = this;
            // This function first finds out all the concentrations,flavor and saves them in a collection and orders them based in the comparator
            _.each(self.tab_data.get('product_ids'),function(product_id){
                var product = self.pos.db.product_by_id[product_id];
                _.each(product.attribute_value_ids,function(attribute_value_id){
                    var attribute_value = self.pos.attribute_values.get(attribute_value_id)
                    if (attribute_value.get('attribute_id')[0] == self.getParent().attribute_conc_id.get('id')){
                        self.available_conc.add(attribute_value)
                        product.conc_id  = attribute_value_id
                    }if (attribute_value.get('attribute_id')[0] == self.getParent().attribute_flavor_id.get('id')){
                        self.available_flavor.add(attribute_value)
                        product.flavor_id  = attribute_value_id
                    }
                })
            })
        },
        render_table_head:function(){
            var self = this;
            var thead = $("");
            if (self.tab_data.get('tab_style') == 1){
                thead  = $('<thead><tr><th>Flavor</th></tr></thead>');
                self.available_conc.each(function(attr_val){
                    thead.find('tr').append("<th class='text-center' >%NAME%</th>".replace('%NAME%',attr_val.get('name')))
                })
                thead.find('tr').append("<th class='text-center'>Unit Price</th><th class='text-center'>Subtotal</th>")
            }else if(self.tab_data.get('tab_style') == 2){
                thead  = $("<thead><tr><th>Product</th><th class='text-center' >Qty</th><th class='text-center' >Unit Price</th><th class='text-center' >Subtotal</th></tr></thead>");
            }
            thead.prependTo(self.table);

        },
        check_inventory:function(inventory){
        		var self = this;
        		var invalid_inventory = [];
        		_.each(self.rows,function(row){
        			var invalid_inventory_row = row.check_inventory(inventory);
        			if (invalid_inventory_row.length > 0){
        				invalid_inventory = invalid_inventory.concat(invalid_inventory_row)
        			}
        		})
        		return invalid_inventory
        },
        get_order_lines_row:function(row){
        		// returns list of lines
        		var self = this;
        		return row.get_lines()
        },
        get_order_lines:function(){
        		var self = this;
        		var lines = [];
        		_.each(self.rows,function(row){
        			lines = lines.concat(self.get_order_lines_row(row));
        		})
        		return lines
        },
        get_column_strength:function(col_id){
        		var self = this;
        		var total = 0.00;
        		_.each(self.rows,function(row){
    				total = total + row.get_col_qty(col_id)
        		});
        		return total
        },
        set_strength_element:function(col_id,strength){
        		this.strength_element[col_id].set_value(strength);
        		this.trigger("qty_changed",this.tab_data.get('id'))
        },
        get_total_strength:function(){
        		var self = this;
        		var total = 0.00;
        		_.each(self.rows,function(row){
        			total = total + row.get_total_qty()
        		})
        		return total
        },
        get_subtotal:function(){
        		var self = this;
        		var total = 0.00;
        		_.each(self.rows,function(row){
        			total = total + row.get_subtotal();
        		})
        		return round_di(total,2)
        },
        render_flavor_concentration_matrix:function(){
            var self = this;
            // Preparing Data
            this.prepare_matrix_data();
            // Render Table Heads
            self.render_table_head();
            // Render dummy rows
            self.available_flavor.each(function(flavor){
                var row = new WholeSaleMatrixRow(self,{'flavor':flavor})
                row.appendTo(self.table.find('tbody'));
                self.rows[flavor.get('id')] = row;
                row.on('qty_changed',self,function(col_id){
                		// In case of matric col_id is the conc_id
                		// In case of list col_id is the tab_id
                		var strength = self.get_column_strength(col_id)
                		self.set_strength_element(col_id,strength)
                })
                row.on('subtotal_changed',self,function(row){
                		self.trigger("subtotal_changed",self)
                })
            })
            // Fill the dummy rows with appropriate element
            _.each(self.tab_data.get('product_ids'),function(product_id){
                var product = self.pos.db.product_by_id[product_id];
                if (product.conc_id && product.flavor_id){
                    self.rows[product.flavor_id].appendProduct(product);
                }
            })
            var product_tab_model = new Model('product.tab');
            product_tab_model.call('get_products_price',[self.tab_data.get('id'),self.pos.get_client().property_product_pricelist,self.pos.get_client().id])
            .then(function(prices){
            		_.each(prices,function(val,index){
            			var product = self.pos.db.product_by_id[index];
                    if (product.conc_id && product.flavor_id){
                        self.rows[product.flavor_id].update_price(val[0]);
                    }            			
            		})
            })
            self.strength_total_element = $("<tr class='success' ><td>Total Strength</td></tr>");
            self.available_conc.each(function(conc){
                var row = $("<td class='text-center danger'></td>");
            		var element = new FieldFloat (self.dfm, {
                    attrs: {
                        name: "strength_input_"+remove_spaces(conc.get('name')),
                        type: "float",
                        modifiers: '{"required": true,"readonly":true}',
                    },
                });
                element.set('conc_id',conc.get('id')) 
                element.appendTo(row);
                row.appendTo(self.strength_total_element);
                self.strength_element[conc.get('id')] = element
            })
            self.strength_total_element.appendTo(self.table)
        },
        render_list_products:function(){
            var self = this;
            self.render_table_head();
            var product_tab_model = new Model('product.tab')
            _.each(self.tab_data.get('product_ids'),function(product_id){
                var product = self.pos.db.product_by_id[product_id];
                var row = new WholeSaleListRow(self,{'product_id':product.id})
                row.appendTo(self.table.find('tbody'));
                self.rows[product.id] = row;
                // Attach qty_changed event to row
                row.on('qty_changed',self,function(col_id){
            		// In case of matric col_id is the conc_id
            		// In case of list col_id is the tab_id
            		var strength = self.get_column_strength(col_id)
            		self.set_strength_element(col_id,strength)
                })              
                row.on('subtotal_changed',self,function(row){
                		self.trigger("subtotal_changed",self)
                })                
            })
            product_tab_model.call('get_products_price',[self.tab_data.get('id'),self.pos.get_client().property_product_pricelist,self.pos.get_client().id])
            .then(function(prices){
        			_.each(prices,function(val,key){
        				self.rows[key].update_price(val[0])
        			})
            })
            self.strength_total_element = $("<tr class='info'><td>Total Strength</td></tr>");
            	// rendering Strength Row
            var row = $("<td class='text-center danger'></td>");
	    		var element = new FieldFloat (self.dfm, {
	            attrs: {
	                name: "strength_input_"+remove_spaces(self.tab_data.get('name')),
	                type: "float",
	                modifiers: '{"required": true,"readonly":true}',
	            },
	        });
	        element.set('tab_id',self.tab_data.get('id')) 
	        element.appendTo(row);
	        row.appendTo(self.strength_total_element);
	        self.strength_element[self.tab_data.get('id')] = element
	        self.strength_total_element.appendTo(self.table)
        },
        renderElement:function(){
            var self = this;
            this._super();
            self.$el = self.getParent().$el.find('div.tab-pane#_ID'.replace('ID',self.tab_data.get('id')))
            // Create a table
            self.table = $("<table class='table table-hover table-bordered' ><caption class='text-center' ><h3>%NAME%</h3></caption></table>".replace('%NAME%',self.pos.get_client().name))
            self.table.appendTo(self.$el)
            self.table.append("<tbody></tbody>");
            if (self.tab_data.get('tab_style') == 1){
                self.render_flavor_concentration_matrix();
            }else if(self.tab_data.get('tab_style') == 2){
                self.render_list_products();
            }
        }

    })

    var WholeSalePosWidget = PosBaseWidget.extend({
        template:'WholeSalePosWidget',

        init:function(parent,options){
            this._super(parent,options);
            this.tabs = options.tabs || {};
            this.tabs_widget = [];
            this.attribute_volume_id = this.pos.product_attributes.findWhere({'nature':'vol'})
            this.attribute_conc_id = this.pos.product_attributes.findWhere({'nature':'conc'})
            this.attribute_flavor_id = this.pos.product_attributes.findWhere({'nature':'flav'})
            if (!(this.attribute_volume_id && this.attribute_conc_id)){
                this.gui.show_popup('error',{
                    'title':_t("Configuration Error"),
                    'body':_t('Please set the attribute for concentration and volume')
                });
                return
            }
            this.dfm = new form_common.DefaultFieldManager(this);
            this.payment_plans_widget = new payment_plans.PaymentPlansWidget(this,{})
        },
        renderElement:function(){
            var self = this;
            this._super();
            this.payment_plans_widget.appendTo(self.$el.find("tr#payment_plans"))
        },
        navigate:function(e){
        		var self = this;
        		switch(e.which){
        			case $.ui.keyCode.UP:
		            	var tr = $(e.target).parents('tr:first');
		            	var td_index = $(e.target).parent().index();
		            	var tr_prev = tr.prev();
		            	tr_prev.children("td").eq(td_index).find("input").focus();        				
        				break;
        			case $.ui.keyCode.DOWN:
		            	var tr = $(e.target).parents('tr:first');
		            	var td_index = $(e.target).parent().index();
		            	var tr_next = tr.next();
		            	tr_next.children("td").eq(td_index).find("input").focus();        				
        				break;
        			case $.ui.keyCode.RIGHT:
        				$(e.target).parent().next().find("input").focus();
        				break;
        			case $.ui.keyCode.LEFT:
        				$(e.target).parent().prev().find("input").focus();
        				break;
        		}
        },
        check_inventory:function(inventory){
        		var self = this;
        		var invalid_inventory = [];
        		_.each(self.tabs_widget,function(tab){
        			var tab_invalid_inventory = tab.check_inventory(inventory)
        			if (tab_invalid_inventory.length > 0){
        				invalid_inventory = invalid_inventory.concat(tab_invalid_inventory)
        			}
        			
        		})
        		return invalid_inventory
        },
        get_total_strength:function(){
        		var self = this;
        		var total = 0.00;
        		_.each(self.tabs_widget,function(tab){
        			total = total + tab.get_total_strength();
        		})
        		return total
        },
        set_total_strength:function(){
        		var total_strength = this.get_total_strength();
        		this.total_units_element.set_value(total_strength);
        },
        get_subtotal:function(){
        		var self = this;
        		var total = 0.00;
        		_.each(self.tabs_widget,function(tab){
        			total = total + tab.get_subtotal();
        		})
        		return total;
        },
        set_subtotal:function(){
        		var total = this.get_subtotal();
        		this.subtotal_element.set_value(total);
        },
        set_discount:function(field){
        		var self = this;
        		if (field.field_manager.eval_context.stop){
        			return
        		}
        		field.field_manager.eval_context.stop = true;
    			if (field.name == "discount_percentage"){
    				var discount = self.get_discount();
    				self.discount.set_value(discount)
    				
    			}else if (field.name == "discount"){
    				var discount = parseFloat(field.get_value()) || 0;
    				var subtotal = self.get_subtotal() || 0;
    				var s_h = self.get_s_h() || 0;
    				var total = subtotal + s_h;
    				if (total != 0){
    					var discount_percentage = (discount/total)*100;
    					self.discount_percentage.set_value(parseFloat(discount_percentage.toFixed(2)))
    				}
    			}
    			field.field_manager.eval_context.stop = false;
    			self.set_total();
    			self.set_balance();
        },
        start:function(){
            var self = this;
            self.total_units_element = new FieldFloat (self.dfm, {
                attrs: {
                    name: "total_units",
                    type: "float",
                    modifiers: '{"required": true,"readonly":true}'
                },
            });
            self.total_units_element.appendTo(self.$el.find("td#total_units"))
            self.subtotal_element = new FieldFloat (self.dfm, {
                attrs: {
                    name: "subtotal",
                    type: "float",
                    modifiers: '{"required": true,"readonly":true}'
                },
            });
            self.subtotal_element.appendTo(self.$el.find("td#subtotal"))
            self.subtotal_element.on("change",self,function(){
            		self.set_discount(self.discount_percentage);
            		self.set_total();
            		self.set_balance();
            })
            self.order_notes = new FieldText(self.dfm,{
                attrs: {
                    name: "order_notes_input",
                    type: "text",
                    placeholder:"Order Notes",
                    context: {
                    },
                    modifiers: '{"required": false}',
                },
            })
            self.order_notes.appendTo(self.$el.find("div#order_notes"))
            self.order_notes.$el.css('width','100%')
            self.shipping_handling = new FieldFloat (self.dfm, {
                attrs: {
                    name: "shipping_handling",
                    type: "float",
                    modifiers: '{"required": true,"readonly":false}'
                },
            });
            self.shipping_handling.appendTo(self.$el.find("td#shipping_handling"))
            self.shipping_handling.on("change",self,function(){
            		self.set_discount(self.discount_percentage);
            		self.set_total();
            		self.set_balance();
            })            
            self.discount_percentage = new FieldFloat (self.dfm, {
                attrs: {
                    name: "discount_percentage",
                    type: "float",
                    modifiers: '{"required": true,"readonly":false}'
                },
            });
            self.discount_percentage.appendTo(self.$el.find("td#discount_percentage"))   
            self.discount_percentage.on("change",self,self.set_discount.bind(self))
            self.discount = new FieldFloat (self.dfm, {
                attrs: {
                    name: "discount",
                    type: "float",
                    modifiers: '{"required": true,"readonly":false}'
                },
            });
            self.discount.appendTo(self.$el.find("td#discount"))  
            self.discount.on("change",self,self.set_discount.bind(self))
            self.net_total = new FieldFloat (self.dfm, {
                attrs: {
                    name: "net_total",
                    type: "float",
                    modifiers: '{"required": true,"readonly":true}'
                },
            });
            self.net_total.appendTo(self.$el.find("td#net_total"))
            self.paid = new FieldFloat (self.dfm, {
                attrs: {
                    name: "paid",
                    type: "float",
                    modifiers: '{"required": true,"readonly":false}'
                },
            });
            self.paid.appendTo(self.$el.find("td#paid"))
            self.paid.on("change",self,function(){
            		self.set_balance();
            })
            self.balance = new FieldFloat (self.dfm, {
                attrs: {
                    name: "balance",
                    type: "float",
                    modifiers: '{"required": true,"readonly":true}'
                },
            });
            self.balance.appendTo(self.$el.find("td#balance"))                        
    			self.payment_method = $(QWeb.render('Many2OneSelection',{models:self.pos.all_journals.models}))
    			self.payment_method.appendTo(self.$el.find("td#payment_method"));            
            
            
            self.pos.product_tabs.each(function(tab,key){
                var wholesale_tab = new WholeSaleTab(self,{'tab':tab});
                self.tabs_widget.push(wholesale_tab);
                wholesale_tab.renderElement();
                wholesale_tab.on('qty_changed',self,function(tab_id){
                		self.set_total_strength();
                })
                wholesale_tab.on('subtotal_changed',self,function(tab_id){
                		self.set_subtotal();
                })                
            });
            self.$el.on("keydown",self,self.navigate.bind(self))            
        },
        get_payment_method:function(){
        		return this.payment_method.val() || false;
        },
        get_balance:function(){
        		var self = this;
        		var total = self.get_total();
        		var paid = parseFloat(self.paid.get_value());
        		var payment_plans = self.payment_plans_widget.get_total();
        		var balance = total - paid - payment_plans;
        		return parseFloat(balance.toFixed(2))
        },
        set_balance:function(){
        		var bal = this.get_balance();
        		this.balance.set_value(bal);
        },
        get_discount_percentage:function(){
        		return parseFloat(this.discount_percentage.get_value());
        },
        get_s_h:function(){
        		return parseFloat(this.shipping_handling.get_value())
        },
        get_discount:function(){
        		var self = this;
        		var discount_percentage = self.get_discount_percentage();
        		var discount = self.get_subtotal() * (discount_percentage / 100.0)
        		return parseFloat(discount.toFixed(2));
        },
        get_total:function(){
    			var self = this;
    			var subtotal = self.get_subtotal();
    			var s_h = self.get_s_h();
    			var discount = self.get_discount();
    			var net_total = subtotal + s_h - discount
    			return parseFloat(net_total.toFixed(2))
        },
        set_total:function(){
        		var total = this.get_total();
        		this.net_total.set_value(total)
        },
        get_order:function(){
        		var self = this;
        		var order_lines = [];
        		// Working
        		_.each(self.tabs_widget,function(tab){
        			order_lines = order_lines.concat(tab.get_order_lines())
        		})
        		var res = {
        			'partner_id':self.pos.get_client().id,
        			'order_lines':order_lines,
        			'shipping_handling':self.get_s_h(),
    				'discount_percentage':self.get_discount_percentage(),
    				'paid':parseFloat(self.paid.get_value()),
    				'payment_method':self.get_payment_method(),
    				'note':self.order_notes.get_value() || '',
        		};
    			res['payment_lines'] = self.payment_plans_widget.get_lines()
    			return res;
        },
    })

    var WholeSalePosScreenWidget = screen.ScreenWidget.extend({
        template:'WholeSalePosScreen',
        init: function(parent, options){
            this._super(parent, options);
            this.wholesale_widget = null;
        },
        auto_back: true,
        _wholesale_widget_destroy:function(){
            this.wholesale_widget.destroy();
            this.wholesale_widget = null;
        },
        validate_order:function(order){
        		var self = this;
        		var msg = "";
        		var validated = true;
        		if (order['order_lines'].length <= 0 ){
        			msg = _t("No order lines to checkout");
        			validated = false;
        		}
        		if (order['paid'] > 0 && (!order['payment_method'])){
        			msg = _t("Please set the payment method for the paid amount!");
        			validated = false;
        		}
        		if (order['payment_lines'] == -1){
        			msg = _t("Please fill all the fields of payment lines. No field in the payment line can be left blank!");
        			validated = false;
        		}
        		var product_ids = order.order_lines.map(function(line){
        			return line.product_id
        		})
        		var product = new Model('product.product')
        		console.log("===============product_ids",product_ids);
        		return product.call('read',[product_ids,['virtual_available','incoming_qty']]).then(function(res){
    				var inventory = new InventoryCollection(res)
    				var invalids = self.wholesale_widget.check_inventory(inventory)
        			return {
            			'validated':validated,
            			'msg':msg,
            			'qty':res,
            			'invalids':invalids,
        			}
        		})
        },
        _confirm_order:function(){
        		var self = this;
        		var order = self.wholesale_widget.get_order();
        		var validate_deferred = self.validate_order(order);
        		$.when(validate_deferred).then(function(validate){
        			if (validate.invalids.length > 0){
        				self.pos.gui.show_popup('inventory',validate.invalids)
        				return
        			}
            		if (!validate.validated){
            			self.gui.show_popup('error',{
                        'title':_t("Order Validation Error!"),
                        'body':_t(validate.msg)
                    });
            			return        			        			
            		}
            		framework.blockUI();
            		var pos_session_object = new Model('pos.session');
            		pos_session_object.call('confirm_order_interface',[order]).then(function(res){
        				self.do_action(res);
        				self.back();
            		})        			
        		})
        },
        confirm_order:function(){
        		var self = this;
        		var balance = self.wholesale_widget.get_balance();
        		if (balance > 0){
        			self.gui.show_popup('confirm',{
        				'title':_t("Balance greater than zero"),
        				'body':_t("Are you sure you want to proceed even though all the money is not accounted for?"),
        				'confirm':function(value){
        					self._confirm_order.call(self)
        				},
        				'cancel':function(value){
        					return
        				}
        			})
        		}else if(balance < 0){
                self.gui.show_popup('error',{
                    'title': _t('Balance less than 0'),
                    'body':  _t('Please make sure that the balance does not fall below zero!'),
                });
                return
        		}else{
        			self._confirm_order();
        		}
        },
        back:function(){
        		var self = this;
            self._wholesale_widget_destroy();
            self.gui.back();        		
        },
        show:function(){
            var self = this;
            this._super();
//            var product_tab_object = new Model('product.tab');
//            this.product_tabs = product_tab_object.query([])
//                                    .filter([['active', '=', true]])
//                                    .order_by('sequence')
//                                    .all()
//                                    .then(function(tabs){
            if (self.wholesale_widget){
                self._wholesale_widget_destroy();
            }
            self.renderElement();
            self.wholesale_widget = new WholeSalePosWidget(self,{});
            self.wholesale_widget.appendTo(self.$el.find('div.subwindow-container-fix.touch-scrollable.scrollable-y'));
            self.$('span.back').click(function(){
            		self.back();
            });
            self.$('span.next').click(function(){
            		self.confirm_order();
            });            
//            })
        }
    })

    gui.define_screen({name:'WholeSalePosScreenWidget', widget: WholeSalePosScreenWidget});

    var add_wholesalepos_button = screen.ActionButtonWidget.extend({
        template:"add_wholesalepos_button",
        init:function(parent,options){
            this._super(parent, options);
            this.parent = parent;
        },
        button_click:function(){
            var self = this;
            var order  = self.parent.pos.get('selectedOrder')
            if (self.pos.get_client()){
                self.parent.gui.show_screen('WholeSalePosScreenWidget')
            }else{
                self.gui.show_popup('error',{
                    'title':_t("Client Error"),
                    'body':_t('Please Select a customer!')
                });
            }
        }
    })
    screen.define_action_button({
        'name': 'pos_notes',
        'widget': add_wholesalepos_button,
        'condition': function(){
            return true
        },
    });


//    var _super_ = screen.ProductScreenWidget.prototype.start
//
//    screen.ProductScreenWidget.prototype.start = function(){
//        _super_.call(this)
//        this.wholesale_widget = new WholeSalePosWidget(this,{});
//    }

//    return {
//        'WholeSalePosWidget':WholeSalePosWidget
//    }
});