odoo.define("pos_layaway.pos_layaway",function(require){
"use strict";

	var core = require('web.core');
	var screen = require('point_of_sale.screens');
	var _t = core._t;
	var Model = require('web.DataModel');
	var pos_old_order_widget = require("pos_order.order_reprinting_pos")
	
	var add_layaway_button = screen.ActionButtonWidget.extend({
	    template:"AddLayAwayButton",
	    init:function(parent,options){
	        this._super(parent, options);
	        this.parent = parent;
	    },
	    button_click:function(){
	        var self = this;
	        var client = self.pos.get_client();
	        if (client){
		        var order  = self.parent.pos.get('selectedOrder');
		        if (order.is_empty()){
		        		self.gui.show_popup('error',{
	                    'title':_t("Order Error"),
	                    'body':_t('Order is Empty!')
	                });		        		
		        		return
		        }
		        var order_json = order.export_as_JSON();
		        self.parent.gui.show_popup('number',{
		            'title':_t('Amount paid upfront ?'),
		            'confirm': function(value) {
		            		if (!value){
		            			return
		            		}
		            		var input = parseFloat(value) || 0.00;
				        if (input < order_json.amount_total){
				        		self.gui.show_popup('selection',{
				        			'title':_t('Select Payment Mode'),
				        			'list':_.map(self.pos.cashregisters,function(register){
				        				return {label:register.journal_id[1],item:register.journal_id[0]}
				        			}),
				        			'confirm':function(item){
				        				order_json.journal_id = item
				        				order_json.amount_paid = input
					                var posOrderModel = new Model('pos.order');
					                order.initialize_validation_date();
					                self.pos.db.add_order(order_json);
					                self.pos.set('synch',{ state: 'connecting'});
					                posOrderModel.call('create_layaway_order',[order_json]).then(function(order_id){
				                        var new_order = {
				                        		    'id':order_id,
				                                'amount_tax': order_json.amount_tax,
				                                'amount_total': order_json.amount_total,
				                                'pos_reference': order_json.name,
				                                'partner_id': [order_json.partner_id, order.get_client_name()],
				                                'session_id': [
				                                    self.pos.pos_session.id, self.pos.pos_session.name
				                                ],
				                        			'state':'layaway',
				                        			'amount_paid':input,
				                        			'date_order':new Date().toISOString().slice(0, 10),
				                            };		                        			                	
						                	order.finalize()	
						                	self.pos.db.remove_order(order_id);
				                        self.pos.set('synch', {
						                            state: 'connected',
				                        });
				                        self.pos.pos_orders[order_id] = new_order;
				                        self.gui.screen_instances.OldOrdersWidget.render_list(self.pos.pos_orders);
					                }).fail(function(error,event){
				                        self.gui.show_popup('error-traceback',{
				                            'title': error.data.message,
				                            'body':  error.data.debug
				                        });
				                        self.pos.set('synch', {
				                            state: 'error',
				                        });			                				                        
					                });				        	
				        			},
				        		})
				        }else{
			                self.gui.show_popup('error',{
			                    'title':_t("Total Error"),
			                    'body':_t('Amount Paid greater than or equal to Order total!')
			                });	        					        	
				        }		            	
		            }
		        })	        	
	        }else{
                self.gui.show_popup('error',{
                    'title':_t("Client Error"),
                    'body':_t('Please Select a customer!')
                });	        	
	        }
	    }
	})

    screen.define_action_button({
        'name': 'pos_layaway',
        'widget': add_layaway_button,
        'condition': function(){
            return true
        },
    });	
	
	
	pos_old_order_widget.OldOrdersWidget.include({
		render_list:function(orders){
			var self = this;
			this._super(orders);
	        this.$('.order-list-contents').delegate('.layaway-button','click',function(event){
        		var order_id = $(this).data('id');
        		self.gui.show_popup('number',{
		            'title':_t('Payment Amount'),
		            'confirm':function(value){
		            	var input = parseFloat(value) || 0.00;
		            	if (input == 0){
		            		return
		            	}
		        		self.gui.show_popup('selection',{
		        			'title':_t('Select Payment Mode'),
		        			'list':_.map(self.pos.cashregisters,function(register){
		        				return {label:register.journal_id[1],item:register.journal_id[0]}
		        			}),
		        			'confirm':function(item){
	        					var posModel = new Model('pos.order')
	        					posModel.call('make_layaway_payment',[order_id,input,item]).then(function(res){
	        						var order = self.get_order_by_id(order_id)
	        						order.state = res.state;
	        						order.balance = res.balance;
	        						order.amount_paid = res.amount_paid;
	        						self.order_cache.clear_node(order.id)
	        						self.render_list(self.pos.pos_orders);
		        					self.gui.show_popup('alert',{
		        						'title':"Payment Registration",
		        						'body':res.msg,
		        					})	        						
	        					})
		        			}
		        		})
	            	}
        		});
        })			
		},
	})
});