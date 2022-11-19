frappe.ui.form.on('Purchase Order', {
	after_save: function (frm) {
		if (frm.doc.supplier) {
			frappe.db.get_value('Supplier', frm.doc.supplier, 'minimum_order_amount_art')
				.then(({
					message
				}) => {
					var min_order_amount_art = message.minimum_order_amount_art
					if (min_order_amount_art && frm.doc.net_total < min_order_amount_art) {
						if (frm.doc.net_total) {

							frappe.msgprint({
								title: __('Alert'),
								indicator: 'orange',
								message: __("Purchase Order Net Total : <b>{0}</b> is less than the Minimum Purchase Order Amount : <b>{1}</b> for Supplier : {2} . \
							<br> LCL amount for Supplier is <b>{3}</b>",
									[frm.doc.net_total, min_order_amount_art, frm.doc.supplier_name, frm.doc.lcl_amount_art])
							});
						}
					}
				});
		}
	},
	refresh: function (frm) {

		frm.add_custom_button(
			__("Download PO Item Template"),
			function () {
				const sample_data = [[__("Item Code"),__("Qty")],["92003", 10],["92004",15]]
				frappe.write_xlsx(sample_data, 'PO Item Template', "PO Item Template")
			},
			__("Tools")
		  );

		frm.add_custom_button(
			__("Upload PO Items"),
			function () {
			  // read excel
			  new frappe.ui.FileUploader({
				as_dataurl: true,
				allow_multiple: false,
				on_success(file) {
				  var reader = new FileReader();
				  reader.onload = function (e) {
					var workbook = XLSX.read(e.target.result);
					// get data from Lead Items
					let ws = workbook.Sheets[workbook.SheetNames[0]];
					set_sheet_range(ws, 1, 2);
					let csv = XLSX.utils.sheet_to_csv(ws);
					var data = frappe.utils.csv_to_array(csv);
					frm.events.upload_po_items(frm, data);
				  };
				  reader.readAsArrayBuffer(file.file_obj);
				},
			  });
			},
			__("Tools")
		  );

		frm.add_custom_button(
			__("Email Supplier"),
			function () {
				frappe.dom.freeze(__("Please wait while attachments for the email are created."));
				frappe.call({
					method: "art_collections.controllers.excel.purchase_order.make_supplier_email_attachments",
					args: {
						po_name: frm.doc.name,
					},
					callback: function () {
						frappe.dom.unfreeze();
						frm.reload_doc();
					},
				});
			},
			__("Tools")
		);

		frm.add_custom_button(
			__("Product Excel"),
			function () {
				frappe.call({
					method: "art_collections.controllers.excel.purchase_order._make_excel_attachment",
					args: {
						docname: frm.doc.name,
						doctype: frm.doc.doctype,
					},
					callback: function () {
						frm.reload_doc();
					},
				});
			},
			__("Tools")
		);

		frm.add_custom_button(
			__("Make Sales Confirmation"),
			function () {
				frappe.dom.freeze(__("Creating Sales Confirmation. Please wait."));
				frappe.call({
					method: 'art_collections.art_collections.doctype.sales_confirmation.sales_confirmation.make_from_po',
					args: {
						docname: frm.doc.name,
					},
					callback: function (r) {
						frappe.dom.unfreeze();
						frappe.set_route('Form', 'Sales Confirmation', r.message);
					},
				});
			},
			__("Tools")
		);


		if (frm.doc.photo_quotation_cf) {
			frappe.add_dashboard_connection( frm, "Photo Quotation", "Related", 1, 1, [frm.doc.photo_quotation_cf], null, 1 );
		}

		$('div').find('.document-link[data-doctype="Art Shipment"]').remove();
		if (frm.is_new() == undefined) {
			frappe.call('art_collections.purchase_order_controller.get_connected_shipment', {
				purchase_order: frm.doc.name
			}).then(r => {
				if (r.message && r.message != undefined) {
					let count = r.message.length
					let link = $(`
			<div class="document-link" data-doctype="Art Shipment">
				<div class="document-link-badge" data-doctype="Art Shipment"> <span class="count">${count}</span> <a
					class="badge-link">Art Shipment</a> </div> <span class="open-notification hidden"
				title="Open Art Shipment"> </span></div>
			`);

					link.on('click', function () {
						frappe.route_options = {
							'name': ['in', r.message]
						};
						frappe.set_route("List", "Art Shipment", "List");

					})
					$('div').find('.document-link[data-doctype="Supplier Packing List Art"]').after(link);
				}
			})
		}
	},

	supplier_email_callback: function (frm) {
		frappe.after_ajax(() => {
			frappe.call({
				method: "art_collections.controllers.excel.purchase_order.supplier_email_callback",
				args: {
					docname: frm.doc.name,
				},
				callback: function (r) {
					frappe.set_route('Form', 'Sales Confirmation', r.message);
				},
			});
		});
	},

	upload_po_items: function (frm, items) {
		let promises = [];
		for (const d of items) {
		  let item = frm.add_child("items", {
			qty: cint(d[1]),
			schedule_date: frappe.datetime.get_today(),
		  });
		  promises.push(
			frappe.model.set_value(item.doctype, item.name, "item_code", d[0])
		  );
		}
		Promise.all(promises).then(() => {
		  frm.refresh_field("items");
		});
	  },

});


frappe.ui.form.on("Purchase Order Item", {
	item_code: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.db.get_value('Item', row.item_code, 'min_order_qty')
				.then(r => {
					row.min_order_qty_cf = r.message.min_order_qty
				})
		}
	}

});


function set_sheet_range(ws, skip_rows, column_count) {
	let ref = XLSX.utils.decode_range(ws["!ref"]);
	let max_row = skip_rows;
	while (true) {
	  var nextCell = ws[XLSX.utils.encode_cell({ r: max_row, c: 1 })];
	  if (typeof nextCell === "undefined" || nextCell == "") break;
	  max_row++;
	}
	ref.s.r = skip_rows;
	ref.e.r = max_row - 1;
	ref.e.c = column_count;
	ws["!ref"] = XLSX.utils.encode_range(ref);
  }