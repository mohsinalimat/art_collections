frappe.ui.form.on('Sales Order', {

	setup: function (frm) {

	},

	onload_post_render: function (frm) {
		frappe.call('art_collections.item_controller.get_saleable_warehouse_list')
			.then(saleable_warehouse_type => {
				if (saleable_warehouse_type) {
					frm.set_query('set_warehouse', () => {
						return {
							filters: {
								warehouse_type: ['in', saleable_warehouse_type.message]
							}
						}
					})
					frm.set_query('warehouse', 'items', () => {
						return {
							filters: {
								warehouse_type: ['in', saleable_warehouse_type.message]
							}
						}
					})
				}
			})
	},
	shipping_address_name: function (frm) {
		frappe.db.get_value('Address', frm.doc.shipping_address_name, ['delivery_by_appointment_art', 'delivery_contact_art', 'delivery_appointment_contact_detail_art', 'country'])
			.then(r => {
				let values = r.message;
				if (values) {
					let delivery_by_appointment_art = values.delivery_by_appointment_art
					let delivery_contact_art = values.delivery_contact_art
					let delivery_appointment_contact_detail_art = values.delivery_appointment_contact_detail_art
					let country = values.country
					if (country) {
                        frappe.call('art_collections.sales_order_controller.get_shipping_rule', {
                            country: country
                        }).then(r => {
                            let records=r.message
                            if (records.length > 0) {
                                frm.set_value('shipping_rule', records[0].name)
                            }                            
                        })
					}
					frm.set_value({
						delivery_by_appointment_art: delivery_by_appointment_art,
						delivery_contact_art: delivery_contact_art,
						delivery_appointment_contact_detail_art: delivery_appointment_contact_detail_art
					})
				}
			})
	},
	customer: function (frm) {
		if (frm.doc.customer && frm.doc.is_offline_art == 0) {
			const default_company = frappe.defaults.get_default('company');
			let found_credit_limit = false
			let found_payment_terms = false
			frappe.db.get_doc('Customer', frm.doc.customer)
				.then(doc => {
					if (!doc.payment_terms) {
						for (var i in doc.credit_limits || []) {
							var item = doc.credit_limits[i];
							if (item.company == default_company && item.credit_limit > 0) {
								found_credit_limit = true
								break;
							}
						}
					} else {
						found_payment_terms = true
					}
					if (found_payment_terms == false && found_credit_limit == false) {
						frappe.msgprint({
							title: __('Missing payment terms and credit limit'),
							indicator: 'orange',
							message: __("Customer <u>{0}</u> has no payment terms or credit limit defined.",
								[frappe.utils.get_form_link("Customer", frm.doc.customer, true)])
						});
					}

				})
		}

	},
	refresh: function (frm) {
		frm.page.add_menu_item(__('Send Email'), function () { frappe.show_email_dialog(frm); });

		frm.toggle_reqd('order_expiry_date_ar', frm.doc.needs_confirmation_art === 1);

		if (frm.page.get_inner_group_button(__('Create')).length == 0) {

			frm.page.add_inner_button(
				__("Download ART Bulk Template"), function () { download_art_bulk_template(frm) }, __("Create")
			);

			frm.page.add_inner_button(
				__("Upload ART Bulk"), function () { upload_art_bulk_items(frm) }, __("Create")
			);

			frm.page.add_inner_button(
				__("Product Excel"),
				function () {
					frappe.call({
						method: "art_collections.controllers.excel.sales_order._make_excel_attachment",
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
		}

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
		create_warning_dialog_for_inner_qty_check(frm)
		// frm.trigger('create_warning_dialog_for_inner_qty_check');

		if (frm.doc.order_type && (frm.doc.order_type == 'Shopping Cart' || frm.doc.order_type == 'Shopping Cart Wish List')) {
			$.each(frm.doc.items || [], function (i, d) {
				frappe.db.get_value('Item', d.item_code, 'max_qty_allowed_in_shopping_cart_art').then
					(({ message }) => {
						var max_qty = message.max_qty_allowed_in_shopping_cart_art
						if (d.qty > max_qty && max_qty > 0) {
							frappe.msgprint(__('Maximum {0} qty allowed for {1} in sales order.', [max_qty, d.item_code]));
						}
					});

			});
		}
	},


});


function create_warning_dialog_for_inner_qty_check(frm) {
	let promises = [];
	let warning_html_messages = []

	$.each(frm.doc.items || [], function (i, d) {
		if (d.item_code != undefined) {
			// create each new promise for item iteration
			let p = new Promise(resolve => {

				frappe.call('art_collections.item_controller.get_qty_of_inner_cartoon', { item_code: d.item_code }).then(
					r => {
						let raise_warning = false
						let nb_selling_packs_in_inner_art = r.message
						if ((d.uom == d.stock_uom) && nb_selling_packs_in_inner_art && nb_selling_packs_in_inner_art > 0) {
							if (d.qty >= nb_selling_packs_in_inner_art) {
								let allowed_selling_packs_in_inner = d.qty % nb_selling_packs_in_inner_art
								if (allowed_selling_packs_in_inner != 0) {
									raise_warning = true
								}
							} else {
								raise_warning = true
							}
							if (raise_warning == true) {
								let warning_html =
									`<p>
									${__("#<b>{3}</b> : Item {0} : qty should be in multiples of <b>{1}</b> (inner selling packs). It is <b>{2}</b>", [d.item_name, nb_selling_packs_in_inner_art, d.qty, d.idx])}
								</p>`;
								warning_html_messages.push(warning_html)
								// resolve on warning
								resolve();
							} else {
								// resolve on no warning
								resolve();
							}
						}
						else {
							// when nb_selling_packs_in_inner_art ==0 
							resolve();
						}
					}
				);

			});
			// push all promises p to array
			promises.push(p);
		}
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
		} else {
			// no warning , so set the flag and save
			frm.ignore_warning = true;
			frm.save();
		}
	});
}

function download_art_bulk_template(frm) {
	var data = [];
	var docfields = [];
	data.push([__("Bulk Edit {0}", ['Items'])]);
	data.push([]);
	data.push([]);
	data.push([]);
	data.push([__("The CSV format is case sensitive")]);
	data.push([__("Do not edit headers which are preset in the template")]);
	data.push(["-----------------------------------------------------------------------------"]);
	$.each(frappe.get_meta('Sales Order Item').fields, (i, df) => {
		// don't include the read-only field in the template
		if (frappe.model.is_value_type(df.fieldtype) && (df.fieldname == 'item_code' || df.fieldname == 'qty' || df.fieldname == 'uom')) {
			data[1].push(df.label);
			data[2].push(df.fieldname);
			let description = (df.description || "") + ' ';
			if (df.fieldtype === "Date") {
				description += frappe.boot.sysdefaults.date_format;
			}
			data[3].push(description);
			docfields.push(df);
		}
	});

	// add data
	$.each(frm.doc['items'] || [], (i, d) => {
		var row = [];
		$.each(data[2], (i, fieldname) => {
			var value = d[fieldname];

			// format date
			if (docfields[i].fieldtype === "Date" && value) {
				value = frappe.datetime.str_to_user(value);
			}

			row.push(value || "");
		});
		data.push(row);
	});

	frappe.tools.downloadify(data, null, 'Items');
	return false;
}


function upload_art_bulk_items(frm) {
	frappe.dom.freeze()
	new frappe.ui.FileUploader({
		as_dataurl: true,
		allow_multiple: false,
		on_success(file) {

			frm.clear_table('items');
			frm.clear_table('discontinued_sales_item_ct');

			let data = frappe.utils.csv_to_array(frappe.utils.get_decoded_string(file.dataurl));
			let items = data.slice(7).filter(t => t.length == 3)

			for (const t of items) {
				frm.add_child('items', {
					delivery_date: frm.doc.delivery_date,
					item_code: t[0],
					qty: t[1],
					uom: t[2],
				})
			}

			let tasks = [];
			frm.doc.items.forEach((child, idx) => {
				tasks.push(
					() => frm.script_manager.trigger("item_code", child.doctype, child.name)
				)
				tasks.push(() => frappe.timeout(3.0))
				tasks.push(
					() => frappe.model.set_value(child.doctype, child.name, 'uom', items[idx][2])
				)
				tasks.push(() => frappe.timeout(0.5))
			})


			return frappe.run_serially(tasks).then(() => {
				frm.refresh_field("items");
				frappe.dom.unfreeze()
				frappe.msgprint({ message: __('Table updated'), title: __('Success'), indicator: 'green' });
			});

		}
	});
}