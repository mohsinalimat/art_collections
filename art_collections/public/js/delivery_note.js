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