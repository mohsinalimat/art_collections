frappe.ui.form.on("Supplier Quotation", {
	setup: function(frm) {
		frm.set_indicator_formatter('item_code',
		function(doc) {
			let item_code=doc.item_code
			return (item_code.indexOf('P')==0) ? "orange" : "green"
		})
	}
});