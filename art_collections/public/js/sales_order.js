frappe.ui.form.on('Sales Order', {

	setup: function (frm) {

	},

	// onload_post_render: function (frm) {
	// 	frappe.call('art_collections.item_controller.get_saleable_warehouse_list')
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
							let records = r.message
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
		if (frm.doc.customer) {
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

		if (frm.doc.docstatus == 1) {
			if (frm.has_perm("submit")) {
				if (frm.doc.status === 'On Hold') {
					// un-hold
					frm.add_custom_button(__('Resume'), function () {
						frm.set_value({
							needs_confirmation_art: 0,
							order_expiry_date_ar: null
						})
						.then(() => {
							frm.refresh_field('needs_confirmation_art');
							frm.refresh_field('order_expiry_date_ar');
							frm.cscript.update_status('Resume', 'Draft')
						})
					}, __("Status"));
				}
			}
		}

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
		/**
				// Items will be uploaded using Data Import on server side

				// ignore_warning is set to true in warning popup's success route
				if (frm.ignore_warning) {
					return;
				}
				frappe.validated = false;
				create_warning_dialog_for_inner_qty_check(frm)
				// frm.trigger('create_warning_dialog_for_inner_qty_check');
		 */


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
	let method = '/api/method/art_collections.controllers.sales_order_items_import.download_sales_order_items_upload_template';
	open_url_post(method, {})
}

function upload_art_bulk_items(frm) {
	// Use Data Import to import items from upload file

	function _show_uploader(frm) {
		new frappe.ui.FileUploader({
			doctype: frm.doctype,
			docname: frm.docname,
			frm: frm,
			folder: 'Home/Attachments',
			on_success: (file_doc) => {
				frm.attachments.attachment_uploaded(file_doc);
				frappe.dom.freeze(__("Importing items. Please wait."));

				frappe.call({
					method: "art_collections.controllers.sales_order_items_import.import_items",
					args: {
						docname: frm.doc.name,
						file_url: file_doc.file_url,
						delivery_date: frm.doc.delivery_date
					}
				}).then(() => {
					frm.reload_doc();
					frappe.dom.unfreeze();
				})
			}
		});
	}

	if (frm.is_new()) {
		// Add a dummy item and Save, so that Sales Order 
		// with Customer etc. is available for Data Import - update existing records. 

		frm.doc.items = [];
		frappe.db.get_single_value('Art Collections Settings', 'dummy_item').then((item_code) => {
			let child = frm.add_child('items', {
				delivery_date: frm.doc.delivery_date,
				item_code: item_code,
				qty: 10000,
			});
			frm.script_manager.trigger("item_code", child.doctype, child.name).then(() => {
				frm.refresh_field('items');
				frm.save()
					.then(() => {
						frm.reload_doc();
						_show_uploader(frm)
					});
			})
		})
	} else {
		_show_uploader(frm)
	}
}
