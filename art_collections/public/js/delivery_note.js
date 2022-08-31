frappe.ui.form.on('Delivery Note', {

	refresh: function (frm) {
		// frappe.add_product_excel_button(frm, "art_collections.controllers.excel.delivery_note_excel._make_excel_attachment")
	},

	before_submit: function (frm) {
		if (frm.doc.double_check_order_flag_art == 1 && frm.doc.did_you_double_check_the_order_art != 1) {
			frappe.throw(__('You have not double checked the order.'));
		}
	},


	// onload_post_render: function (frm) {
	// 	frappe.call('art_collections.item_controller.get_all_saleable_warehouse_list')
	// 		.then(saleable_warehouse_type => {
	// 			if (saleable_warehouse_type) {
	// 				frm.set_query('set_warehouse', () => {
	// 					return {
	// 						filters: {
	// 							warehouse_type: ['in', saleable_warehouse_type.message]
	// 						}
	// 					}
	// 				})
	// 				frm.set_query('warehouse', 'items', () => {
	// 					return {
	// 						filters: {
	// 							warehouse_type: ['in', saleable_warehouse_type.message]
	// 						}
	// 					}
	// 				})
	// 			}
	// 		})

	// },    

});


var _original_get_print_formats = frappe.meta.get_print_formats;
$.extend(frappe.meta, {
	get_print_formats: function (doctype) {
		let cur_frm = me && me.frm;
		if (cur_frm && cur_frm.doc && cur_frm.doc.hide_rate_in_delivery_note_art) {
			return ["DN NR"]
		} else if (cur_frm && cur_frm.doc && cur_frm.doc.hide_rate_in_delivery_note_art === 0) {
			return ['Art DN']
		}
		// in case you want to show list of frappe
		// ideally never reaches here
		let print_format_list = _original_get_print_formats(doctype);
		return print_format_list;
	},
});
