odoo.define("pos_juice_bars.juice_bar_mix",function(require){
"use strict";

    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
    var Model = require('web.DataModel');
    var exports = require('point_of_sale.models');
    var gui = require('point_of_sale.gui');
    var screen = require('point_of_sale.screens');
    var PopupWidget = require('point_of_sale.popups');


    // Load Bootstrap and css for tabbing
    function loadjscssfile(filename, filetype){
        if (filetype=="js"){ //if filename is a external JavaScript file
            var fileref=document.createElement('script')
            fileref.setAttribute("type","text/javascript")
            fileref.setAttribute("src", filename)
        }
        else if (filetype=="css"){ //if filename is an external CSS file
            var fileref=document.createElement("link")
            fileref.setAttribute("rel", "stylesheet")
            fileref.setAttribute("type", "text/css")
            fileref.setAttribute("href", filename)
        }
        if (typeof fileref!="undefined")
            document.getElementsByTagName("head")[0].appendChild(fileref)
    }
    exports.load_fields("product.product",['attribute_value_ids'])
    exports.load_models([{
        model:'product.attribute.value',
        label:"Product Attribute Values",
        fields:['name','actual_value','attribute_id'],
        loaded: function(self,attribute_values){
            self.attribute_values = new Backbone.Collection(attribute_values)
        },
    }])

    exports.Orderline = exports.Orderline.extend({
        export_as_JSON: function() {
            var pack_lot_ids = [];
            if (this.has_product_lot){
                this.pack_lot_lines.each(_.bind( function(item) {
                    return pack_lot_ids.push([0, 0, item.export_as_JSON()]);
                }, this));
            }
            return {
                qty: this.get_quantity(),
                price_unit: this.get_unit_price(),
                discount: this.get_discount(),
                product_id: this.get_product().id,
                tax_ids: [[6, false, _.map(this.get_applicable_taxes(), function(tax){ return tax.id; })]],
                id: this.id,
                pack_lot_ids: pack_lot_ids,
                mixture_line_id:this.mixture_line_id,
            };
        },
    })


    var JuiceBarMixPopupWidget = PopupWidget.extend({
            template: 'JuiceBarMixPopupWidget',
            init:function(parent,options){
                var self = this;
                this._super(parent,options)
                this.juice_bar_id = {};
                this.conc_ids = [];
                self.tabs = {}
            },
            get_product_image_url: function(product){
                return window.location.origin + '/web/binary/image?model=product.product&field=image_medium&id='+product.id;
            },
            render_product:function(product){
                var self = this;
                var image_url = self.get_product_image_url(product);
                var product_render = $(QWeb.render('JuiceBar',{'product':product,'image_url':image_url,'widget':self}));
                return product_render
            },
            click_product_handler:function(elem,product){
                var self = this;
                if (self.db.has(product.id)){
                    self.db.set(product.id,self.db.get(product.id) + 1);
                }else{
                    self.db.set(product.id,1);
                }
            },
            _get_mix_ratio:function(mix_part){
                var self = this;
                return mix_part/self.total_parts;
            },
            _get_line_concentration:function(){
                var self = this;
                var line_concentration_value = 0.00;
                _.each(self.db.attributes,function(value,key){
                    var p = self.pos.db.product_by_id[key]
                    if (p.conc_id){
                        line_concentration_value = line_concentration_value +
                                            (self.pos.attribute_values.get(p.conc_id).get("actual_value") * self._get_mix_ratio(value));
                    }
                });
                return line_concentration_value;
            },
            add_order_line:function(options){
                var self = this;
                var order = self.pos.get('selectedOrder')
                self.addProduct(order,options);
            },
            addProduct:function(order,options){
                var self = this;
                var product = Object.assign({}, self.pos.db.product_by_id[self.product.id]);
                if(order._printed){
                    order.destroy();
                    return order.pos.get('selectedOrder').addProduct(product, {});
                }
                order.assert_editable();
                options = options || {};
                var attr = JSON.parse(JSON.stringify(product));
                attr.pos = this.pos;
                attr.order = this;

                var line = new exports.Orderline({}, {pos: order.pos, order: order, product: product});
                line.mixture_line_id = [];
                _.each(self.db.attributes,function(val,key){
                    line.mixture_line_id.push([0,0,{
                        product_id:parseInt(key),
                        mix:self._get_mix_ratio(val)
                    }])
                })
                product.display_name = product.display_name + " - REPLACE mg".replace("REPLACE",self.line_concentration_value)

                if(options.quantity !== undefined){
                    line.set_quantity(1);
                }
                if(options.price !== undefined){
                    line.set_unit_price(options.price || 0);
                }
                //To substract from the unit price the included taxes mapped by the fiscal position
                order.fix_tax_included_price(line);

                if(options.discount !== undefined){
                    line.set_discount(options.discount || 0 );
                }

                if(options.extras !== undefined){
                    for (var prop in options.extras) {
                        line[prop] = options.extras[prop];
                    }
                }

                order.orderlines.add(line);
                order.select_orderline(order.get_last_orderline());

                if(line.has_product_lot){
                    this.display_lot_popup();
                }
                self.click_confirm();
            },
            on_change_db:function(){
                var self = this;
                var summary = [];
                var total = 0;
                self.summary_page.empty();
                _.each(self.db.attributes,function(value,key){
                    var  p = self.pos.db.product_by_id[key]
                    summary.push({
                        id:p.id,
                        name:p.display_name,
                        qty:value,
                    })
                    total = total + value;
                })
                self.total_parts = total;
                self.line_concentration_value = self._get_line_concentration();
                var summary_elem = $(QWeb.render('PopUpSummary',{'summary':summary,total_length : self.total_parts}))
                summary_elem.appendTo(self.summary_page);
                $("td#reduce").on("click",function(){
                    var product_id = $(this).data().productId;
                    var qty  = self.db.get(product_id);
                    if (qty == 1){
                        self.db.unset(product_id)
                    }else{
                        self.db.set(product_id, self.db.get(product_id) - 1)
                    }
                    if (Object.keys(self.db.attributes).length <= 0){
                        self.summary_page.empty();
                    }
                })
                summary_elem.find("caption").text("Conc. %REPLACE% mg".replace("%REPLACE%",self.line_concentration_value.toFixed(2)))
                summary_elem.find("button.button").on('click',function(){
                    self.add_order_line();
                })
            },
            show: function(options){
                var self = this;
                self.product = options.context.juice_bar_id;
                self.db = new Backbone.Model();
                self.db.on("change",function(){
                    self.on_change_db();
                })
                this.conc_ids = options.context.conc_ids;
                this.vol_id = options.context.vol_id;
                this.juice_bar_id = options.context.juice_bar_id;
                this._super(options);
                self.summary_page = self.$el.find("div#summary");
                _.each(self.conc_ids,function(conc_id){
                    var container = $(QWeb.render('JuiceBarListWidget',{}));
                    self.tabs[conc_id] = container;
                    self.tabs[conc_id].appendTo(self.$el.find('div#_'+conc_id))
                    var products_to_render = [];
                    _.each(self.pos.db.product_by_id,function(p,key){
	                    	if (p.attribute_value_ids.indexOf(self.vol_id) > -1 &&  p.attribute_value_ids.indexOf(conc_id)  > -1 ){
	                    		products_to_render.push(p)
	                    	}
                    });
                    	products_to_render.sort(function(a, b){
                    	    var nameA= a.display_name.toLowerCase(), nameB=b.display_name.toLowerCase()
                    	    if (nameA < nameB) //sort string ascending
                    	        return -1 
                    	    if (nameA > nameB)
                    	        return 1
                    	    return 0 //default return value (no sorting)
                    	})
                    	_.each(products_to_render,function(p,index){
                        var product_render = self.render_product(p);
                        product_render.appendTo(container.find("div.product-list"));
                        product_render.data('id',p.id)
//                      products.push(product_render);
                        product_render.on("click",function(){
                            p.conc_id = conc_id;
                            self.click_product_handler(this,p)
                        });
                    	})
                })
            },
            renderElement:function(){
                var self = this;
                self._super();
            },

    })
    gui.define_popup({name:'juice_bar_mix', widget: JuiceBarMixPopupWidget});
    loadjscssfile("/web/static/lib/bootstrap/css/bootstrap.css","css") ////dynamically load and add this .css file

    screen.ProductScreenWidget.prototype.click_product = function(product) {
            function _click_product(product){
                var self = this;
                if(product.to_weight && this.pos.config.iface_electronic_scale){
                    this.gui.show_screen('scale',{product: product});
                }else{
                    this.pos.get_order().add_product(product);
                }
            }
            var self = this;
            $.when(this.product_list_widget.volume_id,this.product_list_widget.conc_ids,this.product_list_widget.juice_bar_ids).then(function(vol_id,c_ids,j_b_ids){
                var vol_id = parseInt(vol_id);
                var conc_ids  = JSON.parse(c_ids);
                var juice_bar_ids = JSON.parse(j_b_ids);
                if (vol_id && conc_ids.length > 0){
                    if (juice_bar_ids.indexOf(product.id) > -1){
                        self.gui.show_popup('juice_bar_mix',{
                            'title':_t('Juice Bars Mix Wizard'),
                            'confirm': function(value) {
                                return
                            },
                            'context':{
                                'conc_ids':conc_ids,
                                'vol_id':vol_id,
                                'juice_bar_id':product
                            }
                        })
                    }else{
                        _click_product.call(self,product);
                    }
                }else{
                    _click_product.call(self,product);
                }
            })
        }

    var _super = screen.ProductListWidget.prototype.init

    screen.ProductListWidget.prototype.init = function(parent,options){
        _super.call(this,parent,options);
        var config = new Model('ir.config_parameter')
        this.volume_id = config.call('get_param',['pos_juice_bars.juicebar_volume_id']);
        this.conc_ids = config.call('get_param',['pos_juice_bars.juicebar_concentration_ids']);
        this.juice_bar_ids = config.call('get_param',['pos_juice_bars.juice_bars_ids']);
    }
})