frappe.ui.form.on('Customer', {

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
        for (let index = 0; index < customer_target_art.length; index++) {
            let discount_percent = customer_target_art[index].discount_percent;
            if (discount_percent<=0) {
                frappe.throw({
                    title: __('Discount percentage should be > 0'),
                    message:__('Discount percentage is {0} in Customer Target row {1}. Please correct it',[discount_percent,customer_target_art[index].idx])
                });
            }
            
        }
    },
    refresh: function (frm) {
        if (cur_frm.fields_dict['address_html'] && "addr_list" in cur_frm.doc.__onload) {
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