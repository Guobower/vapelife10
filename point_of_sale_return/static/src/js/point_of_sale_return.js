odoo.define("point_of_sale_return.point_of_sale_return",function(require){
"use strict";

	var core = require('web.core');
	var QWeb = core.qweb;
	var _t = core._t;
	var Model = require('web.DataModel');
	var pos_old_order_widget = require("pos_order.order_reprinting_pos")
	
	pos_old_order_widget.OldOrdersWidget.include({
		render_list:function(orders){
			var self = this;
			this._super(orders);
		},
	});
});