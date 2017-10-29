odoo.define("pos_notes.add_notes",function(require){
"use strict";

    var core = require('web.core');

    var screen = require('point_of_sale.screens');
    var exports = require("point_of_sale.models");
    var PopupWidget = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    
    var QWeb = core.qweb;
    var _t = core._t;

    var TextAreaPopupWidgetNotes = PopupWidget.extend({
        template: 'TextAreaPopupWidgetNotes',
        show: function(options){
            options = options || {};
            this._super(options);

            this.renderElement();
            this.$('input,textarea').focus();
        },
        click_confirm: function(){
            var value = this.$('input,textarea').val();
            this.gui.close_popup();
            if( this.options.confirm ){
                this.options.confirm.call(this,value);
            }
        },
    });
    gui.define_popup({name:'textareanotes', widget: TextAreaPopupWidgetNotes});    
    
    exports.Order = exports.Order.extend({
        get_note:function(){
            return this.get('note') || '';
        },
        export_as_JSON: function() {
            var orderLines, paymentLines;
            orderLines = [];
            this.orderlines.each(_.bind( function(item) {
                return orderLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            paymentLines = [];
            this.paymentlines.each(_.bind( function(item) {
                return paymentLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            return {
                name: this.get_name(),
                amount_paid: this.get_total_paid(),
                amount_total: this.get_total_with_tax(),
                amount_tax: this.get_total_tax(),
                amount_return: this.get_change(),
                lines: orderLines,
                statement_ids: paymentLines,
                pos_session_id: this.pos_session_id,
                partner_id: this.get_client() ? this.get_client().id : false,
                user_id: this.pos.cashier ? this.pos.cashier.id : this.pos.user.id,
                uid: this.uid,
                sequence_number: this.sequence_number,
                creation_date: this.validation_date || this.creation_date, // todo: rename creation_date in master
                fiscal_position_id: this.fiscal_position ? this.fiscal_position.id : false,
                note:this.get_note(),
            };
        },
    })

    var add_notes_button = screen.ActionButtonWidget.extend({
        template:"AddNotesButton",
        init:function(parent,options){
            this._super(parent, options);
            this.parent = parent;
        },
        button_click:function(){
            var self = this;
            var order  = self.parent.pos.get('selectedOrder')
            self.parent.gui.show_popup('textareanotes',{
                'title':_t('Add Notes'),
                'value':order.get_note(),
                'confirm': function(value) {
                    order.set('note',value)
                }
            })
        }
    })

    screen.define_action_button({
        'name': 'pos_notes',
        'widget': add_notes_button,
        'condition': function(){
            return true
        },
    });


});