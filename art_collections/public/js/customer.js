frappe.ui.form.on('Customer', {
    fill_customer_sales_person: function (address) {
        var doc = cur_frm.doc;
        if (doc.customer_sales_person[0]) {
            doc.customer_sales_person.splice(doc.customer_sales_person[0], 1)
        }
        var child = cur_frm.add_child("customer_sales_person");
        frappe.model.set_value(child.doctype, child.name, "address_title", address)
    },
    refresh: function (frm) {
        if (frm.fields_dict['address_html'] && "addr_list" in frm.doc.__onload) {
            var str = frappe.render_template("address_list", cur_frm.doc.__onload)
            var str_to_find = "Address/"
            var len_of_str_to_find = str_to_find.length;
            var pos = str.indexOf(str_to_find);
            var new_pos = str.indexOf('"', pos + len_of_str_to_find);
            var address = str.slice(pos + len_of_str_to_find, new_pos)
            address = address.replace("%20", " ");
            if (frm.doc.customer_sales_person.length == 0) {
                cur_frm.events.fill_customer_sales_person(address)
            }
            frm.doc.customer_sales_person.forEach(function (row) {
                if (row.address_title != address) {
                    cur_frm.events.fill_customer_sales_person(address)
                }
            });

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