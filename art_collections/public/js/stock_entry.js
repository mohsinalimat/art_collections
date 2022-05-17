frappe.ui.form.on('Stock Entry', {
	refresh: (frm) => {	
        if (frm.is_new()==undefined && frm.doc.docstatus == 0 && frm.doc.items!=undefined && frm.doc.items.length>0 
        && (frm.doc.purpose == 'Material Transfer' || frm.doc.purpose == 'Material Receipt')) {
                frm.add_custom_button(__('Optimize Path'),
                    () => frm.events.sort_as_per_warehouse(frm));
        }		
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

		let items = frm.doc.items
        let warehouse='t_warehouse'
		items.sort(dynamicSort(warehouse))
		frm.clear_table('items')
		for (const key in items) {
			if (Object.hasOwnProperty.call(items, key)) {
				const element = items[key];
				frm.add_child('items',element)
				
			}
		}
		frm.save()		
	}
});