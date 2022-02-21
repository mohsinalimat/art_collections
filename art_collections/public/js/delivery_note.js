frappe.ui.form.on('Delivery Note', {
	onload_post_render: function (frm) {
		frappe.db.get_value('Art Collections Settings', 'Art Collections Settings', ['saleable_warehouse_type', 'reserved_warehouse_type'])
			.then(r => {
				let saleable_warehouse_type = r.message.saleable_warehouse_type
				let reserved_warehouse_type = r.message.reserved_warehouse_type
				if (saleable_warehouse_type || reserved_warehouse_type) {
					if (saleable_warehouse_type != null && reserved_warehouse_type != null) {
						frm.set_query('warehouse', 'items', () => {
							return {
								filters: {
									warehouse_type: ['in', [saleable_warehouse_type, reserved_warehouse_type]]
								}
							}
						})
                        frm.set_query('set_warehouse', () => {
                            return {
                                filters: {
                                    warehouse_type: ['in', [saleable_warehouse_type, reserved_warehouse_type]]
                                }
                            }
                        })                        
					} else if (saleable_warehouse_type != null && reserved_warehouse_type == null) {
						frm.set_query('warehouse', 'items', () => {
							return {
								filters: {
									warehouse_type: ['=', saleable_warehouse_type]
								}
							}
						})
                        frm.set_query('set_warehouse', () => {
                            return {
                                filters: {
                                    warehouse_type: ['=', saleable_warehouse_type]
                                }
                            }
                        })                         
					} else if (saleable_warehouse_type == null && reserved_warehouse_type != null) {
						frm.set_query('warehouse', 'items', () => {
							return {
								filters: {
									warehouse_type: ['=', reserved_warehouse_type]
								}
							}
						})
                        frm.set_query('set_warehouse', () => {
                            return {
                                filters: {
                                    warehouse_type: ['=', saleable_warehouse_type]
                                }
                            }
                        })                        
					}
				}
			})
	},    
    before_submit: function (frm) {
     if (frm.doc.double_check_order_flag_art==1 && frm.doc.did_you_double_check_the_order_art!=1) 
     {
		frappe.throw(__('You have not double checked the order.'));
     }
    }
 });

 $.extend(frappe.meta, {
	get_print_formats: function(doctype) {
		var print_format_list = ["Standard"];
		var default_print_format = locals.DocType[doctype].default_print_format;
		let enable_raw_printing = frappe.model.get_doc(":Print Settings", "Print Settings").enable_raw_printing;
		var print_formats = frappe.get_list("Print Format", {doc_type: doctype})
			.sort(function(a, b) { return (a > b) ? 1 : -1; });
		$.each(print_formats, function(i, d) {
			if (
				!in_list(print_format_list, d.name)
				&& d.print_format_type !== 'JS'
				&& (cint(enable_raw_printing) || !d.raw_printing)
			) {
				print_format_list.push(d.name);
			}
		});

		if(default_print_format && default_print_format != "Standard") {
			var index = print_format_list.indexOf(default_print_format);
			print_format_list.splice(index, 1).sort();
			print_format_list.unshift(default_print_format);
		}
		
		// custom code
		if(me.frm.doc.hide_rate_in_delivery_note_art==1){
			return print_format_list = ["DN No Rate"]		
			
		}else{
			return print_format_list= ["Standard"];
		}
		// custom code

		// return print_format_list;	
	},
   });