frappe.ui.form.on('Sales Order', {
	shipping_address_name: function (frm) {
		frappe.db.get_value('Address', frm.doc.shipping_address_name, ['delivery_by_appointment_art', 'delivery_contact_art','delivery_appointment_contact_detail_art'])
    .then(r => {
        let values = r.message;
				if (values) {
					let delivery_by_appointment_art=values.delivery_by_appointment_art
					let delivery_contact_art=values.delivery_contact_art
					let delivery_appointment_contact_detail_art=values.delivery_appointment_contact_detail_art
					frm.set_value({
						delivery_by_appointment_art: delivery_by_appointment_art,
						delivery_contact_art: delivery_contact_art,
						delivery_appointment_contact_detail_art:delivery_appointment_contact_detail_art
				})					
				}
    })		
	},
	customer: function (frm) {
		if (frm.doc.customer) {
			const default_company = frappe.defaults.get_default('company');
			let found_credit_limit=false
			let found_payment_terms=false
			frappe.db.get_doc('Customer', frm.doc.customer)
			.then(doc => {
					if (!doc.payment_terms) {
						for (var i in doc.credit_limits || []) {
							var item = doc.credit_limits[i];
							if (item.company==default_company && item.credit_limit>0) {
								console.log('item.credit_limit',item.credit_limit)
								found_credit_limit=true
								break;
							}							
						}						
					}else{
						found_payment_terms=true
						console.log('doc.payment_terms',doc.payment_terms)
					}
					if (found_payment_terms==false && found_credit_limit==false) {
						frappe.msgprint({
							title: __('Missing payment terms and credit limit'),
							indicator: 'orange',
							message: __("Customer <u>{0}</u> has no payment terms or credit limit defined.",
								[							frappe.utils.get_form_link("Customer",frm.doc.customer,true)])
						});						
					}

			})					
		}

	},	
	refresh: function (frm) {
		frm.toggle_reqd('order_expiry_date_ar', frm.doc.needs_confirmation_art === 1);

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
		

		
	},
	needs_confirmation_art: function (frm) {
		frm.toggle_reqd('order_expiry_date_ar', frm.doc.needs_confirmation_art === 1);
	},
    validate: function (frm) {
			
			// ignore_warning is set to true in warning popup's success route
			if (frm.ignore_warning) {
				return;
			}			
			frappe.validated = false;
			frm.trigger('create_warning_dialog_for_inner_qty_check');
		
			
		$.each(frm.doc.items || [], function(i, d) {
			frappe.db.get_value('Item', d.item_code, 'max_qty_allowed_in_shopping_cart_art').then
			(({ message }) => {
				console.log(message);
				var max_qty=message.max_qty_allowed_in_shopping_cart_art
				if(d.qty > max_qty && max_qty>0) {
					frappe.msgprint(__('Maximum {0} qty allowed for {1} in sales order.',[max_qty,d.item_code]));
				}
			  });

		});
    },
		create_warning_dialog_for_inner_qty_check: function (frm) {
			let promises = [];
			let warning_html_messages = []
	
					$.each(frm.doc.items || [], function (i, d) {
						// create each new promise for item iteration
						let p = new Promise(resolve => {
						frappe.db.get_value('Item', d.item_code, 'nb_selling_packs_in_inner_art').then(({
							message
						}) => {
							debugger
							let raise_warning=false
							let nb_selling_packs_in_inner_art = message.nb_selling_packs_in_inner_art
							if (nb_selling_packs_in_inner_art && nb_selling_packs_in_inner_art>0) {
								if (d.qty >= nb_selling_packs_in_inner_art ) {
									let allowed_selling_packs_in_inner =d.qty % nb_selling_packs_in_inner_art
									if (allowed_selling_packs_in_inner!=0) {
										raise_warning=true
									}
								}else{
									raise_warning=true
								}
								if (raise_warning==true) {
									let warning_html =
										`<p>
									${__("#<b>{3}</b> : Item {0} : qty should be in multiples of <b>{1}</b> (inner selling packs). It is <b>{2}</b>",[d.item_name,nb_selling_packs_in_inner_art,d.qty,d.idx])}
								</p>`;
									warning_html_messages.push(warning_html)
									// resolve on warning
									resolve();
								} else {
									// resolve on no warning
									resolve();
								}					
							}
						});
					});
					// push all promises p to array
					promises.push(p);
					});

					// start-- once the for loop od item is over need to run below code
					Promise.all(promises).then(() => {

						let state_table_html = `<p class="bold">
						${__('Are you sure you want to save this document?')}
						</p>`;
						const message_html = state_table_html + warning_html_messages.join('') + __('You should recheck');

						if (warning_html_messages.length > 0) {
						let proceed_action = () => {
							frm.ignore_warning = true;
							frm.save();
						};
						frappe.warn(
							__("Unusual qty regarding no. of selling pack in inner"),
							message_html,
							proceed_action,
							__("Save Anyway")
						);
					}else{
						// no warning , so set the flag and save
						frm.ignore_warning = true;
						frm.save();
					}
				});
		}
 });
frappe.ui.form.on("Sales Order Item", {
	item_code: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.db.get_value('Item', row.item_code, 'min_order_qty')
				.then(r => {
					if (r.message.min_order_qty) {
						row.qty = r.message.min_order_qty
					}
				})
		}
		if (row.item_code && frm.doc.customer) {
			frappe.db.get_value('Customer Item Directive', {customer: frm.doc.customer,item_code:row.item_code}, 'remarks')
			.then(r => {
					if (r.message) {
						let remarks=r.message.remarks
						row.customer_item_directive_art=remarks
					}
			})
				
		}
	}
});