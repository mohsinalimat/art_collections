// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Confirmation', {

	setup: function (frm) {
		frm.set_query("contact_person", function () {
			return {
				query: 'frappe.contacts.doctype.contact.contact.contact_query',
				filters: {
					link_doctype: "Supplier",
					link_name: frm.doc.supplier
				}
			};
		});
	},

	refresh: function (frm) {
		frm.trigger("add_custom_buttons");
	},

	validate: function (frm) {
		(frm.doc.sales_confirmation_detail || []).forEach(d => {
			d.amount = (d.qty || 0) * (d.rate || 0);
		});
	},



	supplier: function (frm) {
		frappe.call({
			method: 'art_collections.controllers.utils.set_contact_details',
			args: {
				party_name: frm.doc.supplier,
				party_type: 'Supplier'
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value(r.message)
				}
			}
		});
	},


	add_custom_buttons: function (frm) {

		if (frm.doc.confirmation_date) {
			frm.add_custom_button(__("Verify (Match Item/PO Item)"), function () {
				return frm.call({
					method: 'verify_with_po',
					doc: frm.doc,
					args: {}
				}).then((r) => {
					frm.dashboard.clear_headline();
					if (r.message) {
						frm.reload_doc();
						setTimeout(() => {
							frm.dashboard.set_headline(__('Please check Invalid Items file <a href="{0}"></a> for errors. ', r.message), 'red');
						}, 200);
					} else {
						frappe.msgprint(__('Items and Purchase Order Items verified.'))
					}
				});
			}, __("Tools"));

			frm.add_custom_button(__("Update Item/PO Item"), function () {
				frappe.confirm(__("Do you want to Update Items and Purchase Order?"), function () {
					return frm.call({
						method: 'update_items_and_po',
						doc: frm.doc,
						args: {}
					}).then((r) => {
						frappe.msgprint(__('Items and Purchase Order updated.'))
					});
				})
			}, __("Tools"));
		}

		frm.add_custom_button(__("Make Item Details Excel"), function () {
			return frm.call({
				method: 'email_supplier',
				doc: frm.doc,
				args: {
					show_email_dialog: 0
				}
			}).then((r) => {
				frm.reload_doc();
			});
		}, __("Tools"));

		frm.add_custom_button(__("Email Supplier"), function () {
			return frm.call({
				method: 'email_supplier',
				doc: frm.doc,
				args: {}
			});
		}, __("Tools"));


		let fieldname = 'sales_confirmation_detail', grid = frm.fields_dict[fieldname].grid;
		grid.wrapper.find(".grid-upload").removeClass('hidden').off('click').on("click", () => {
			new frappe.ui.FileUploader({
				as_dataurl: true,
				allow_multiple: false,
				on_success(file) {
					var reader = new FileReader();
					reader.onload = function (e) {
						var rowNum;
						var workbook = XLSX.readFile(e.target.result);
						var ws = workbook.Sheets['Sales Confirmation Details'];
						if (!ws) {
							frappe.throw(__("Invalid Upload file for Sales Confirmation"))
						}
						set_sheet_ref(ws, 5);

						// set xlsx values to grid items
						let items = XLSX.utils.sheet_to_json(ws, { blankrows: false });
						items.forEach(cdn => {
							frm.doc.sales_confirmation_detail
								.filter(d => { return d.item_code == cdn["Item Code"] })
								.forEach(d => {
									for (const key in cdn) {
										if (Object.hasOwnProperty.call(cdn, key)) {
											frappe.model.set_value(d.doctype, d.name, frappe.scrub(key), cdn[key])
										}
									}
								})
						});
						frm.refresh_field('sales_confirmation_detail')
						frm.dirty();
					}
					reader.readAsArrayBuffer(file.file_obj)
				}
			})
		});

		grid.wrapper.find(".grid-download").removeClass('hidden').off('click').on("click", () => {
			open_url_post(
				'/api/method/art_collections.art_collections.doctype.sales_confirmation.sales_confirmation.download_details'
				, {
					docname: frm.doc.name,
					supplier: frm.doc.supplier,
				});
		});
	},

	supplier_email_callback: function (frm) {
		// set status after email is sent
		setTimeout(() => {
			frappe.call({
				method: "art_collections.art_collections.doctype.sales_confirmation.sales_confirmation.supplier_email_callback",
				args: {
					docname: frm.doc.name,
				},
				callback: function (r) {
					frm.reload_doc()
				},
			});
			// timeout to allow form to reload. else it throws document has been modified error
		}, 400);
	},
});

const value_formatter_map = {
	"Date": val => val ? frappe.datetime.user_to_str(val) : val,
	"Int": val => cint(val),
	"Check": val => cint(val),
	"Float": val => flt(val),
};

function set_sheet_ref(ws, skip_rows = 0) {
	var rowNum;
	var range = XLSX.utils.decode_range(ws['!ref']);
	for (rowNum = skip_rows; rowNum <= range.e.r; rowNum++) {
		var nextCell = ws[XLSX.utils.encode_cell({ r: rowNum, c: 0 })];
		if (typeof nextCell === 'undefined' || nextCell == "") {
			break
		}
	}
	ws['!ref'] = XLSX.utils.encode_cell({ r: skip_rows, c: 0 }) + ":Q" + rowNum;
}