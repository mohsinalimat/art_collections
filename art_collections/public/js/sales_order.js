frappe.ui.form.on('Sales Order', {

	setup: function (frm) {
		frappe.realtime.on("show_sales_order_email_dialog", function () {
			frm.reload_doc().then(() => {
				show_email_dialog(frm);
			});
		});
	},

	onload_post_render: function (frm) {
		frappe.db.get_single_value('Art Collections Settings', 'saleable_warehouse_type')
			.then(saleable_warehouse_type => {
				if (saleable_warehouse_type) {
					frm.set_query('set_warehouse', () => {
						return {
							filters: {
								warehouse_type: ['=', saleable_warehouse_type]
							}
						}
					})
					frm.set_query('warehouse', 'items', () => {
						return {
							filters: {
								warehouse_type: ['=', saleable_warehouse_type]
							}
						}
					})
				}
			})
	},
	shipping_address_name: function (frm) {
		frappe.db.get_value('Address', frm.doc.shipping_address_name, ['delivery_by_appointment_art', 'delivery_contact_art', 'delivery_appointment_contact_detail_art'])
			.then(r => {
				let values = r.message;
				if (values) {
					let delivery_by_appointment_art = values.delivery_by_appointment_art
					let delivery_contact_art = values.delivery_contact_art
					let delivery_appointment_contact_detail_art = values.delivery_appointment_contact_detail_art
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
		frm.page.add_menu_item(__('Send Email'), function () { show_email_dialog(frm); });

		frm.toggle_reqd('order_expiry_date_ar', frm.doc.needs_confirmation_art === 1);

		frm.add_custom_button(
			__("Download ART Bulk Template"), function () { download_art_bulk_template(frm) }, __("Create")
		);

		frm.add_custom_button(
			__("Upload ART Bulk"), function () { upload_art_bulk_items(frm) }, __("Create")
		);

		frm.add_custom_button(
			__("Product Excel"),
			function () {
				frappe.call({
					method: "art_collections.excel_controller.make_sales_order_excel",
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
		if (frm.doc.ignore_warning) {
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
frappe.ui.form.on("Sales Order Item", {
	item_code: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.item_code && frm.doc.customer) {
			frappe.db.get_value('Customer Item Directive', { customer: frm.doc.customer, item_code: row.item_code }, 'remarks')
				.then(r => {
					if (r.message) {
						let remarks = r.message.remarks
						row.customer_item_directive_art = remarks
					}
				})

		}
	}
});

function show_email_dialog(frm) {
	// show email dialog with pre-set values for default print format 
	// and email template and attach_print

	let composer = new frappe.views.CommunicationComposer({
		doc: frm.doc,
		frm: frm,
		subject: __(frm.meta.name) + ': ' + frm.docname,
		recipients: frm.doc.email || frm.doc.email_id || frm.doc.contact_email,
		attach_document_print: true,
		real_name: frm.doc.real_name || frm.doc.contact_display || frm.doc.contact_name
	});


	frappe.db.get_single_value('Art Collections Settings', 'sales_order_email_template')
		.then(email_template => {
			setTimeout(() => {
				composer.dialog.fields_dict['select_attachments'].$wrapper.find("input").attr("checked", "checked");
				composer.dialog.fields_dict['content'].set_value("");
				composer.dialog.set_values({
					"email_template": email_template,
					// "select_print_format": 'Art Collections Sales Order'
				});
			}, 900);
		});
}


function create_warning_dialog_for_inner_qty_check(frm) {
	let promises = [];
	let warning_html_messages = []

	$.each(frm.doc.items || [], function (i, d) {
		// create each new promise for item iteration
		let p = new Promise(resolve => {
			frappe.db.get_value('Item', d.item_code, 'nb_selling_packs_in_inner_art').then(({
				message
			}) => {
				let raise_warning = false
				let nb_selling_packs_in_inner_art = message.nb_selling_packs_in_inner_art
				if (nb_selling_packs_in_inner_art && nb_selling_packs_in_inner_art > 0) {
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
				frm.doc.ignore_warning = true;
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
			frm.doc.ignore_warning = true;
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
		if (frappe.model.is_value_type(df.fieldtype) && (df.fieldname == 'item_code' || df.fieldname == 'qty' || df.fieldname == 'uom	')) {
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
	let me = this
	const value_formatter_map = {
		"Date": val => val ? frappe.datetime.user_to_str(val) : val,
		"Int": val => cint(val),
		"Check": val => cint(val),
		"Float": val => flt(val),
	};
	new frappe.ui.FileUploader({
		as_dataurl: true,
		allow_multiple: false,
		on_success(file) {
			var data = frappe.utils.csv_to_array(frappe.utils.get_decoded_string(file.dataurl));
			// row #2 contains fieldnames;
			var fieldnames = data[2];
			frm.clear_table('items');
			frm.clear_table('discontinued_sales_item_ct');
			$.each(data, (i, row) => {
				if (i > 6) {
					var blank_row = true;
					$.each(row, function (ci, value) {
						if (value) {
							blank_row = false;
							return false;
						}
					});
					if (!blank_row) {
						var d = frm.add_child('items');
						$.each(row, (ci, value) => {
							var fieldname = fieldnames[ci];
							var df = frappe.meta.get_docfield('Sales Order Item', fieldname);
							if (df) {
								d[fieldnames[ci]] = value_formatter_map[df.fieldtype] ?
									value_formatter_map[df.fieldtype](value) :
									value;
							}
						});
					}
				}
			});
			frm.refresh_field('items');
			let items = frm.doc.items
			for (let index = 0; index < items.length; index++) {
				let visited = false
				const d = items[index];
				frappe.call({
					method: "art_collections.sales_order_controller.get_item_details",
					args: {
						"item_code": d.item_code,
						"qty": d.qty
					},
					callback: function (r, rt) {
						if (r.message) {
							$.each(r.message, function (k, v) {
								if (k == 'is_sales_item') {
									if (v == '0' && visited == false) {

										frm.add_child('discontinued_sales_item_ct', r.message)
										cur_frm.get_field("items").grid.grid_rows[index].remove();
										let visited = true
									}

								} else {
									if (k != 'uom' || (d.uom == '' && k == 'uom')) {
										frappe.model.set_value('Sales Order Item', d.name, k, v);

									}

								}
							});
						}
					}
				})
			}
			frappe.msgprint({ message: __('Table updated'), title: __('Success'), indicator: 'green' });
		}
	});
	return false;
}