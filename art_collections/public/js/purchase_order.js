frappe.ui.form.on('Purchase Order', {
    validate: function (frm) {
		if (frm.doc.supplier) {
			frappe.db.get_value('Supplier', frm.doc.supplier, 'minimum_order_amount_art')
			.then(({ message }) => {
				var min_order_amount_art = message.minimum_order_amount_art
				if ( min_order_amount_art && frm.doc.net_total < min_order_amount_art) {
					if (frm.doc.net_total) {
						frappe.msgprint(__("Purchase Order Net Total : {0} is less than the Minimum Purchase Order Amount : {1} for Supplier : {2} .",
						[frm.doc.net_total,min_order_amount_art,frm.doc.supplier]));
					}	
				}
			});	
		}
    }
 });


 frappe.ui.form.on("Purchase Order Item", {
	item_code: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.db.get_value('Item', row.item_code, 'min_order_qty')
			.then(r => {
					row.min_order_qty_cf=r.message.min_order_qty
			})			
			
		}
	}
});
