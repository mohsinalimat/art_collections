frappe.ui.form.on("Supplier Quotation", {
	onload: function(frm) {
		set_expected_delivery_date(frm);
	},	
	setup: function(frm) {
		frm.set_indicator_formatter('item_code',
		function(doc) {
			let item_code=doc.item_code
			return (item_code.indexOf('P')==0) ? "orange" : "green"
		})
	},
	validate: function(frm) {
		set_expected_delivery_date(frm);
	},	
	items_on_form_rendered: function(frm) {
		set_expected_delivery_date(frm);
	},
	expected_delivery_date_cf: function(frm) {
		set_expected_delivery_date(frm);
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

frappe.ui.form.on("Supplier Quotation Item", {
	expected_delivery_date: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.expected_delivery_date) {
			if(!frm.doc.expected_delivery_date_cf) {
				// copy child table value
				erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "items", "expected_delivery_date");
			} else {
				set_expected_delivery_date(frm);
			}
		}
	}
});

function set_expected_delivery_date(frm) {
	if(frm.doc.expected_delivery_date_cf){
		custom_copy_value_in_all_rows(frm.doc, frm.doc.doctype, frm.doc.name, "items", "expected_delivery_date",frm.doc.expected_delivery_date_cf);
	}
}

function custom_copy_value_in_all_rows(doc, dt, dn, table_fieldname, fieldname,from_fieldname) {
	var d = locals[dt][dn];
	if(from_fieldname){
		var cl = doc[table_fieldname] || [];
		for(var i = 0; i < cl.length; i++) {
			if(!cl[i][fieldname]) cl[i][fieldname] = from_fieldname;
		}
	}
	refresh_field(table_fieldname);
}