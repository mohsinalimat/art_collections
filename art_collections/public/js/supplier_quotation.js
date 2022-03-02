frappe.ui.form.on("Supplier Quotation", {
	setup: function(frm) {
		frm.set_indicator_formatter('item_code',
		function(doc) {
			let item_code=doc.item_code
			return (item_code.indexOf('P')==0) ? "orange" : "green"
		})
	}
});

// frappe.ui.form.on("Supplier Quotation Item", {
// 	item_code: function(frm, cdt, cdn) {
// 		var row = locals[cdt][cdn];
// 		if (row.item_code) {

// 			frappe.call('art_collections.item_controller.get_qty_of_inner_cartoon', {
// 			    item_code: row.item_code
// 			}).then(r => {
// 			    if (r.message) {
// 			    	row.nb_selling_packs_in_inner_art=r.message
// 			    }
// 			})	
			
// 			frappe.call('art_collections.item_controller.get_qty_of_outer_cartoon', {
// 			    item_code: row.item_code
// 			}).then(r => {
// 			    if (r.message) {
// 			    	row.nb_selling_packs_in_outer_art=r.message
// 			    }
// 			})

// 		}

// 	}

// });