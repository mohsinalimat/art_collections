frappe.ui.form.on('Purchase Order', {
	after_save: function (frm) {
		if (frm.doc.supplier) {
			frappe.db.get_value('Supplier', frm.doc.supplier, 'minimum_order_amount_art')
				.then(({
					message
				}) => {
					var min_order_amount_art = message.minimum_order_amount_art
					if (min_order_amount_art && frm.doc.net_total < min_order_amount_art) {
						if (frm.doc.net_total) {

							frappe.msgprint({
								title: __('Alert'),
								indicator: 'orange',
								message: __("Purchase Order Net Total : <b>{0}</b> is less than the Minimum Purchase Order Amount : <b>{1}</b> for Supplier : {2} . \
							<br> LCL amount for Supplier is <b>{3}</b>",
									[frm.doc.net_total, min_order_amount_art, frm.doc.supplier_name, frm.doc.lcl_amount_art])
							});
						}
					}
				});
		}
	},
	refresh: function (frm) {
		if (frm.page.get_inner_group_button(__('Create')).length == 0) {
			frm.add_custom_button(
				__("Product Excel"),
				function () {
					frappe.call({
						method: "art_collections.controllers.excel.purchase_order._make_excel_attachment",
						args: {
							docname: frm.doc.name,
							doctype: frm.doc.doctype,
						},
						callback: function () {
							frm.reload_doc();
						},
					});
				},
				__("Create")
			);
		}

	},


});


frappe.ui.form.on("Purchase Order Item", {
	item_code: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.db.get_value('Item', row.item_code, 'min_order_qty')
				.then(r => {
					row.min_order_qty_cf = r.message.min_order_qty
				})


		}
	}

});