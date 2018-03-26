odoo.define("point_of_sale_return.point_of_sale_return",function(require){
"use strict";

	var core = require('web.core');
	var QWeb = core.qweb;
	var _t = core._t;
	var Model = require('web.DataModel');
	var pos_old_order_widget = require("pos_order.order_reprinting_pos");
	var PopupWidget = require('point_of_sale.popups');
	var gui = require('point_of_sale.gui');
	var QWeb = core.qweb;
	var PosBaseWidget = require('point_of_sale.BaseWidget');
	var Backbone = window.Backbone;
	var utils = require('web.utils');
	var round_pr = utils.round_precision;
	
	var ReturnLineWidget = PosBaseWidget.extend({
		template:'PointOfSaleReturnLine',
		init:function(options){
			var self = this;
			options.line.return_qty = 0.00;
			options.line.amt_return_qty = 0.00;
			this.data = new Backbone.Model(options.line);
			this._super(options)
		},
		get_return_amt:function(){
			return this.data.get('amt_return_qyt');
		},
		set_return_amt:function(val){
			this.set({'amt_return_qty':val})
		},
		calculate_return_amt:function(){
	        var rounding = this.pos.currency.rounding;
	        var subtotal =  round_pr(this.data.get('price_unit') * this.data.get('return_qty') * (1 - this.data.get('discount')/100), rounding);
	        return subtotal
		},
		renderElement:function(){
			var self = this;
			this._super();
			self.$el.find("input#return_qty").change(function(e){
				var quant = $(this).val() || 0;
				self.data.set({'return_qty':quant})
			})
			self.data.on("change:return_qty",function(val){
				var amt = self.calculate_return_amt()
				self.data.set({'amt_return_qty':amt})
				self.$el.find("input#amt_return_qty").val(amt)
				self.trigger("change_amt_return_qty")
			})
		},
		destroy:function(){
			this._super();
			this.data.destroy();
		},
	}) 
	
	var PointOfSaleReturnPopUp = PopupWidget.extend({
		template:'PointOfSaleReturn',
		init:function(parent,options){
			var self = this;
			this._super(parent,options);
			this.total_return_amt = 0.00;
		},
	    events: {
	        'click .button.cancel':  'click_cancel',
	        'click .button.confirm': 'click_confirm',
	        'click .selection-item': 'click_item',
	        'click .input-button':   'click_numpad',
	        'click .mode-button':    'click_numpad',
	        'click .button.return':    'click_return',
	    },	
	    click_return:function(){
	    		var self = this;
        		self.gui.show_popup('selection',{
        			'title':_t('Select Payment Mode'),
        			'list':_.map(self.pos.cashregisters,function(register){
        				return {label:register.journal_id[1],item:register.journal_id[0]}
        			}),
        			'confirm':function(item){
	    		    		var return_lines = self.lines.reduce((function(ol,line){
	    	            		if (line.data.get('return_qty') > 0){
	    	            			ol.push([0,0,{
	    	            				'product_id':line.data.get('productId'),
	    	            				'qty':-line.data.get('return_qty'),
	    	            				'price_unit':line.data.get('price_unit'),
	    	            				'discount':line.data.get('discount'),
	    	            			}])
	    	            		}
	    	            		return ol
	    	            }),[]);

	    		    		if (return_lines.length <= 0){
	    		        		self.gui.show_popup('error',{
	    		                    'title':_t("Return Product Error"),
	    		                    'body':_t('There is nothing to be returned!')
	    		                });		        		
	    		        		return
	    		    		}
	    		    		
	    		    		var order = {
	    			                'name': self.data.order.name + _t(' REFUND'),
	    			                'session_id': self.pos.pos_session.id,
	    			                'date_order': new Date(),
	    			                'pos_reference': self.data.order.pos_reference,
	    			                'lines':return_lines,
    				    		}
	    		    		
	    		    		new Model('pos.order').call('create_return_order',[order,item]).done(function(report){
	    		    			self.do_action(report)
    		    			})
        			},
        		});

	    },
		set_total_return_amt:function(){
			var self = this;
			this.total_return_amt = round_pr(this.lines.reduce((function(sum, line){
	            return sum + line.data.get('amt_return_qty')
	        }), 0), this.pos.currency.rounding);
		},
		update_total_return_amt:function(){
			this.total_node.find("td#val").text(this.total_return_amt);
		},
		show:function(options){
			var self = this;
			this._super(options);
			console.log(options)
			this.data = options.data;
			this.lines = [];
			this.total_node = $(QWeb.render('PointOfSaleReturnTotalLine', {name: 'Total Return Amt'}));
			_.each(options.data.lines,function(l,i){
				l.pos = self.pos;
				var line = new ReturnLineWidget({
					pos:self.pos,
					line:l
				});
				self.lines.push(line);
				line.appendTo(self.tbody);
				line.on("change_amt_return_qty",self,function(){
					self.set_total_return_amt();
					self.update_total_return_amt();
				})
			});
			this.total_node.appendTo(self.tbody)
		},
		
        renderElement:function(){
            var self = this;
            self._super();
            self.tbody = self.$el.find('tbody');
        },		
	})
	gui.define_popup({name:'point_of_sale_return', widget: PointOfSaleReturnPopUp});
	
	pos_old_order_widget.OldOrdersWidget.include({
		render_list:function(orders){
			var self = this;
			this._super(orders);
			this.$('.order-list-contents').delegate('.return-product','click',function(event){
				var order_id = $(this).data('id');
				var order = self.pos.pos_orders[order_id]
				new Model('pos.order').call('get_orderlines',[order.id]).then(function(result){
					self.gui.show_popup('point_of_sale_return',{
			            'title':"Return Products",
	        				'confirm':function(value){
			            		return
			            },
			            'data':{
			            		'id':order_id,
			            		'order':order,
		                    'lines' : result[0],
		                    'payments' : result[2],
		                    'discount' : result[1],
			            },
	        			});					
				});
			});
		},
	});
	
	
});