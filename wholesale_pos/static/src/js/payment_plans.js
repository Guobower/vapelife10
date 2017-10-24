odoo.define("wholesale_pos.payment_plans",function(require){
"use strict";
	var PosBaseWidget = require('point_of_sale.BaseWidget');
	var form_common = require('web.form_common');
	var core = require('web.core');
	var _t = core._t;
	var exports = require("point_of_sale.models");
    var FieldFloat = core.form_widget_registry.get('float');
    var FieldText = core.form_widget_registry.get('text');
    var FieldDate = core.form_widget_registry.get('date');
    var QWeb = core.qweb;
    
    exports.load_models([
        {
            model:'account.journal',
            label:"Account Journals",
            fields:[],
            domain: function(self){ return [['type','in',['cash','bank']],['at_least_one_inbound','=',true]]; },
            loaded: function(self,journals){
                self.all_journals = new Backbone.Collection(journals)
            },
        }])
        
    var PaymentPlanRow = PosBaseWidget.extend({
    		init:function(parent,options){
    			this._super(parent,options);
    			this.dfm = new form_common.DefaultFieldManager(this);
    		},
    		get_payment_method:function(){
			return this.payment_method.val() || false;
    		},
    		get_date:function(){
    			return this.date.val() || false;
    		},
    		get_data:function(){
    			var self = this;
    			self.$el.removeClass('danger').addClass('success');
    			var res =  {
    				'journal_id':parseInt(self.get_payment_method()),
    				'amount':parseFloat(self.amount.get_value()),
    				'date':self.get_date(),
    				'partner_id':self.pos.get_client().id,
    			}
    			_.each(res,function(field){
    				if (!field){
    	                self.$el.removeClass('success').addClass('danger');
    					self.gui.show_popup('error',{
    	                    'title':_t("Payment Lines Error"),
    	                    'body':_t('Please Check the payment lines or delete the invalid lines')
    	                });
    	                res = false
    				}
    			})
    			return res
    		},
    		destroy:function(){
    			var index = this.getParent().lines.indexOf(this);
    			delete this.getParent().lines[index]
    			this.getParent().getParent().set_balance();
    			this._super();
    		},   		
    		renderElement:function(){
    			var self = this;
    			self.$el = $("<tr class='success' >" +
    							"<td class='payment_plan_rows'></td>" +
    							"<td  id = 'payment_method' ></td>" +
    							"<td  id = 'amount'  ></td>"+
    							"<td  id = 'date' ></td>" +
    							"<td  id = 'delete' ></td>" +
						"</tr>")
    			self.payment_method = $(QWeb.render('Many2OneSelection',{models:self.pos.all_journals.models}))
    			self.payment_method.appendTo(self.$el.find("td#payment_method"));
    			self.amount = new FieldFloat (self.dfm, {
                    attrs: {
                        name: "payment_line_amount",
                        type: "float",
                        modifiers: '{"required": true}',
                    },
                });
    			self.amount.appendTo(self.$el.find("td#amount"))
    			self.amount.on("change",self,function(){
    				self.getParent().getParent().set_balance();
    			})
    			self.date = $("<input type='date'/>")
    			self.date.appendTo(self.$el.find("td#date"))
    			this.$delete = $('<i class="fa fa-trash-o fa-2x" aria-hidden="true"></i>')
    			this.$delete.appendTo(self.$el.find("td#delete"));
    		},
    		start:function(){
    			var self = this;
    			this.$delete.on("click",function(){
    				self.destroy.call(self);
    			})
    		}
    })
    
	var PaymentPlansWidget = PosBaseWidget.extend({
		template:"PaymentPlans",
		init:function(parent,options){
			this._super(parent,options);
			this.lines = [];
		},
		renderElement:function(){
			var self = this;
			this._super();
			self.add_item = $("<tr><td><a href='#'><u>Add an Item</u></a></td></tr>")
			self.add_item.appendTo(self.$el.find("tbody"))
		},
		get_lines:function(){
			var self = this;
			var lines = [];
			_.each(self.lines,function(line){
				if (line){
					var l = line.get_data();
					if (!l){
						lines = -1;
						return
					}
					lines = lines.concat(l);					
				}
			})
			return lines
		},
		get_total:function(){
			var self = this;
			var total = 0.00;
			_.each(self.lines,function(line){
				if (line){
					total = total + parseFloat(line.amount.get_value());
				}
			})
			return parseFloat(total.toFixed(2));
		},
		start:function(){
			var self = this;
			self.add_item.on("click",function(){
				var line = new PaymentPlanRow(self,{});
				line.appendTo(self.$el.find('tbody'));
				self.lines.push(line);
			})
		}
	})
	
	return {
		PaymentPlansWidget:PaymentPlansWidget
	}
})