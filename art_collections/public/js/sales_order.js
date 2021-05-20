frappe.ui.form.on('Sales Order', {
	refresh: function (frm) {
		frm.toggle_reqd('order_expiry_date_ar', frm.doc.needs_confirmation_art === 1);
	},
	needs_confirmation_art: function (frm) {
		frm.toggle_reqd('order_expiry_date_ar', frm.doc.needs_confirmation_art === 1);
	},
    validate: function (frm) {
		$.each(frm.doc.items || [], function(i, d) {
			frappe.db.get_value('Item', d.item_code, 'max_qty_allowed_in_shopping_cart_art').then
			(({ message }) => {
				console.log(message);
				var max_qty=message.max_qty_allowed_in_shopping_cart_art
				if(d.qty > max_qty && max_qty>0) {
					frappe.msgprint(__('Maximum {0} qty allowed for {1} in sales order.',[max_qty,d.item_code]));
				}
			  });

		});
    }
 });