frappe.ui.form.on('Customer', {
    territory: function (frm) {
        if (frm.doc.territory) {
            frappe.call('art_collections.customer_controller.get_payment_terms_based_on_territory', {
                territory: frm.doc.territory
            }).then(r => {
                if (r.message) {
                    const default_company = frappe.defaults.get_default('company');
                    let territory_detail=r.message
                    if (territory_detail.default_price_list_cf!=null && (frm.doc.default_price_list==undefined || frm.doc.default_price_list=='')) {
                        frm.set_value('default_price_list', territory_detail.default_price_list_cf)
						frappe.show_alert({
							message: __("Price List : {0} is added from {1} .", [territory_detail.default_price_list_cf,territory_detail.name]),
							indicator: "green"
						});                        
                    }
                    if (territory_detail.default_payment_terms_template_cf!=null && (frm.doc.payment_terms==undefined || frm.doc.payment_terms=='')) {
                        frm.set_value('payment_terms', territory_detail.default_payment_terms_template_cf)
						frappe.show_alert({
							message: __("Payment Terms Template : {0} is added from {1} .", [territory_detail.default_payment_terms_template_cf,territory_detail.name]),
							indicator: "green"
						});                         
                    }      
                    if (territory_detail.minimum_order_amount_cf!=null && (frm.doc.minimum_order_amount_cf==undefined || frm.doc.minimum_order_amount_cf=='')) {
                        frm.set_value('minimum_order_amount_cf', territory_detail.minimum_order_amount_cf)
						frappe.show_alert({
							message: __("Min Order Amount : {0} is added from {1} .", [territory_detail.minimum_order_amount_cf,territory_detail.name]),
							indicator: "green"
						});                         
                    }    
                    if (territory_detail.credit_limit!=null) {
                        let credit_limits=frm.doc.credit_limits || []
                        let result = credit_limits.find(c => c.company==default_company) 
                        if (result==undefined) {
                            var childTable = cur_frm.add_child("credit_limits");
                            childTable.company=territory_detail.company
                            childTable.credit_limit=territory_detail.credit_limit
                            cur_frm.refresh_fields("credit_limits");           
                            frappe.show_alert({
                                message: __("Credit Limit : {0} is added from {1} .", [territory_detail.credit_limit,territory_detail.name]),
                                indicator: "green"
                            });                                     
                        }

                    }                                                   
                }
                
            })            
        }
    },
    fill_customer_sales_person: function (address) {
        var doc = cur_frm.doc;
        if (doc.customer_sales_person[0]) {
            doc.customer_sales_person.splice(doc.customer_sales_person[0], 1)
        }
        var child = cur_frm.add_child("customer_sales_person");
        frappe.model.set_value(child.doctype, child.name, "address_title", address)
    },
    qualifies_for_escompte_art: function (frm) {
        if (frm.doc.qualifies_for_escompte_art==1 && frm.doc.taux_escompte_art==0) {
            frm.set_value('taux_escompte_art', 2)
        }
        else if(frm.doc.qualifies_for_escompte_art==0 ){
            frm.set_value('taux_escompte_art', 0)
        }
    },
    validate: function (frm) {
        let customer_target_art=frm.doc.customer_target_art

        //  check (a) empty discount percentage (b) to value > from value
        if (customer_target_art!=undefined && customer_target_art.length>1) {
        for (let index = 0; index < customer_target_art.length; index++) {
            let discount_percent = customer_target_art[index].discount_percent;
            let to_value = customer_target_art[index].to_value;
            let from_value = customer_target_art[index].from_value;
            if (discount_percent<=0) {
                frappe.throw({
                    title: __('Discount percentage should be > 0'),
                    message:__('Discount percentage is {0} in Customer Target row {1}. Please correct it',[discount_percent,customer_target_art[index].idx])
                });
            }
            if (from_value>=to_value && to_value!=0) {
                frappe.throw({
                    title: __('Incorrect "To" value '),
                    message:__('To value {0} is incorrect for row {1}. It should be greater than From value. Please correct it',[to_value,customer_target_art[index].idx])
                });
            }            
        }        
        }
        // check boundary condition
        if (customer_target_art!=undefined && customer_target_art.length>1) {
            for (let index = 0; index < customer_target_art.length; index++) {
                let first_fiscal_year = customer_target_art[index].fiscal_year;
                let first_to_value = customer_target_art[index].to_value;
                let first_idx=customer_target_art[index].idx;
                for (let index = 0; index < customer_target_art.length; index++) {
                    let second_fiscal_year = customer_target_art[index].fiscal_year;
                    let second_from_value = customer_target_art[index].from_value;
                    let second_idx=customer_target_art[index].idx;
                    if (first_idx!=second_idx && second_idx>first_idx && first_fiscal_year==second_fiscal_year && (first_to_value==second_from_value || first_to_value>second_from_value )) {
                        frappe.throw({
                            title: __('Boundary condition error'),
                            message:__('Please correct from value {0} for row {1}',[second_from_value,second_idx])
                        });
                    }
                }                
                
            }            
        }


    },
    refresh: function (frm) {
        if (cur_frm.doc.__onload!=undefined && cur_frm.fields_dict['address_html'] && "addr_list" in cur_frm.doc.__onload) {
            var str = frappe.render_template("address_list", cur_frm.doc.__onload)

            if (str.indexOf('No address added yet.')!=-1) {
                console.log('no add')
            } else {
                console.log('there is add')
              return  frappe.call({
                    method: 'art_collections.api.get_address_list',
                    args: {
                        name: frm.doc.name,
                        doctype:frm.doc.doctype
                    },
                    async:false,
                    callback: function (r) {
                        if (r.message) {
                            var no_change=true
                            var customer_address_list=r.message
                            if (customer_address_list.length==frm.doc.customer_sales_person.length) {
                                customer_address_list.forEach(function (row,i) {
                                    if (row.name!=frm.doc.customer_sales_person[i].address_title) {
                                        no_change=false;
                                        console.log('title not amtch'+i)
                                    }
                                });                       
                                
                            } else {
                                console.log('leng not match')
                                no_change=false
                            }
                            if (no_change==false) {
                                frm.doc.customer_sales_person=undefined
                                customer_address_list.forEach(function (row,i) {
                                    console.log(i)
                                    var child = cur_frm.add_child("customer_sales_person");
                                    frappe.model.set_value(child.doctype, child.name, "address_title", row.name)
                                }); 
                                frm.refresh_field("customer_sales_person")
                                frappe.show_alert({message:__("Please add sales person againt address in 'Customer Sales Person' table"), indicator:'yellow'});                                    
                                                         
                            }
                        }
                    }
                });

    
            }
        }
 
    }
});
frappe.ui.form.on('Customer Sales Person', {
    address_title: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        var address = row.address_title;
        return frappe.call({
            method: 'art_collections.api.get_sales_person_based_on_address',
            args: {
                address: address
            },
            callback: function (r) {
                if (r.message) {
                    var sales_person = r.message;
                    frappe.model.set_value(row.doctype, row.name, "sales_person", sales_person.sales_person);
                    cur_frm.refresh_field("customer_sales_person");

                }
            }
        });
    }
});