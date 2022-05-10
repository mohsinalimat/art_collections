frappe.ui.form.on('Quotation', {
    shipping_address_name: function (frm) {
        frappe.db.get_value('Address', frm.doc.shipping_address_name, ['country'])
            .then(r => {
                let values = r.message;
                if (values) {
                    let country = values.country
                    if (country) {
                        frappe.call('art_collections.sales_order_controller.get_shipping_rule', {
                            country: country
                        }).then(r => {
                            console.log(r)
                            let records=r.message
                            if (records.length > 0) {
                                frm.set_value('shipping_rule', records[0].name)
                            }                            
                        })

                   }
                }
            })
    }
})