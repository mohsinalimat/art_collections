frappe.ui.form.on('Supplier', {
    onload: function (frm) {
        if (frm.doc.name) {
            frm.trigger('set_actual_delivery_delay_days_art')
        }
    },
    set_actual_delivery_delay_days_art: function (frm) {
        frappe.call({
            method: "art_collections.api.get_actual_delivery_delay_days_art",
            args: {
                supplier: frm.doc.name,
            },
            callback: function (r) {
                if (!r.exc) {
                    console.log(r)
                    if (r.message) {
                        if (r.message.actual_delivery_delay_days != null && r.message.actual_delivery_delay_days != 0) {
                            frm.set_value('actual_delivery_delay_days_art', r.message.actual_delivery_delay_days)
                            frm.save()
                        } else {
                            frm.set_value('actual_delivery_delay_days_art', 0)
                            frm.save()
                        }
                    }
                }
            }
        });
    }

})