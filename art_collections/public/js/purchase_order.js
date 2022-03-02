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
	refresh: function(frm){
		frm.add_custom_button(
			__("Product Excel"),
			function () {
			  frappe.call({
				method: "art_collections.excel_controller.make_excel",
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
		if (row.item_code && frm.doc.supplier) {
			frappe.db.get_value('Supplier Item Directive', {supplier: frm.doc.supplier,item_code:row.item_code}, ['remarks','name'])
			.then(r => {
					if (r.message) {
						let remarks=r.message.remarks
						let supplier_item_directive_link=r.message.name
						row.supplier_item_directive_link_cf=supplier_item_directive_link
						row.supplier_item_directive_art=remarks
					}
			})
				
		}		
	},

});
