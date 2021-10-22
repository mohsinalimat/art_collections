frappe.ui.form.on("Purchase Receipt Item", {
	item_code: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.item_code && frm.doc.supplier) {
			frappe.db.get_value('Supplier Item Directive', {supplier: frm.doc.supplier,item_code:row.item_code}, 'remarks')
			.then(r => {
					if (r.message) {
						let remarks=r.message.remarks
						row.supplier_item_directive_art=remarks
					}
			})
				
		}		
	}
});