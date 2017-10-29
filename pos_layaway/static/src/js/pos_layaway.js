odoo.define("pos_layaway.pos_layaway",function(require){
"use strict";
	
	var screen = require('point_of_sale.screens');
	var add_layaway_button = screen.ActionButtonWidget.extend({
	    template:"AddLayAwayButton",
	    init:function(parent,options){
	        this._super(parent, options);
	        this.parent = parent;
	    },
	    button_click:function(){
	        var self = this;
	        var order  = self.parent.pos.get('selectedOrder')
	        console.log("=========================================",order)
	        
//	        self.parent.gui.show_popup('textareanotes',{
//	            'title':_t('Add Notes'),
//	            'value':order.get_note(),
//	            'confirm': function(value) {
//	                order.set('note',value)
//	            }
//	        })
	    }
	})

    screen.define_action_button({
        'name': 'pos_layaway',
        'widget': add_layaway_button,
        'condition': function(){
            return true
        },
    });	
});