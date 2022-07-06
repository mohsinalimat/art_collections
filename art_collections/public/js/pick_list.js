frappe.ui.form.on('Pick List', {
	refresh: (frm) => {	
		// it is required to trigger our custom 'add_get_items_button'
		frm.remove_custom_button('Get Items');
        if (frm.is_new()==undefined && frm.doc.docstatus == 0 && frm.doc.locations!=undefined && frm.doc.locations.length>1) {
                frm.add_custom_button(__('Optimize Path'),
                    () => frm.events.sort_as_per_warehouse(frm));
        }		
	},
	setup: (frm) => {
		frappe.db.get_single_value('Art Collections Settings', 'picker_role')
			.then(picker_role => {
				console.log(picker_role);
				if (picker_role) {
					frm.set_query('picker_responsible_art', () => {
						return {
							query: 'art_collections.pick_list_controller.get_user_with_picker_role',
						};
					});
				}
			})
	},
	sort_as_per_warehouse: function (frm) {

		function dynamicSort(property) {
			var sortOrder = 1;
			if(property[0] === "-") {
				sortOrder = -1;
				property = property.substr(1);
			}
			return function (a,b) {
				/* next line works with strings and numbers, 
				 * and you may want to customize it to your needs
				 */
				var result = (a[property] < b[property]) ? -1 : (a[property] > b[property]) ? 1 : 0;
				return result * sortOrder;
			}
		}

		let locations = frm.doc.locations
		locations.sort(dynamicSort('warehouse'))
		frm.clear_table('locations')
		for (const key in locations) {
			if (Object.hasOwnProperty.call(locations, key)) {
				const element = locations[key];
				frm.add_child('locations',element)
				
			}
		}
		frm.save()		
	},
	add_get_items_button: (frm) => {
		let purpose = frm.doc.purpose;
		if (purpose != 'Delivery' || frm.doc.docstatus !== 0) return;
		let get_query_filters = {
			docstatus: 1,
			per_delivered: ['<', 100],
			status: ['!=', ''],
			customer: frm.doc.customer
		};
		frm.get_items_btn = frm.add_custom_button(__('Get Items'), () => {
			if (!frm.doc.customer) {
				frappe.msgprint(__('Please select Customer first'));
				return;
			}
			erpnext.utils.map_current_doc({
				method: 'erpnext.selling.doctype.sales_order.sales_order.create_pick_list',
				source_doctype: 'Sales Order',
				target: frm,
				setters: {
					company: frm.doc.company,
					customer: frm.doc.customer,
					status: ['!=', '']
				},
				date_field: 'transaction_date',
				get_query_filters: get_query_filters
			});
		});
	},	
	// onload_post_render: function (frm) {
	// 	frappe.call('art_collections.item_controller.get_all_saleable_warehouse_list')
	// 		.then(saleable_warehouse_type => {
	// 			if (saleable_warehouse_type) {
	// 				frm.set_query('parent_warehouse', () => {
	// 					return {
	// 						filters: {
	// 							warehouse_type: ['in', saleable_warehouse_type.message]
	// 						}
	// 					}
	// 				})
	// 			}
	// 		})		
	// }
});