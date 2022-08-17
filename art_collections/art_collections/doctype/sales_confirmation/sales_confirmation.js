// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Confirmation', {
	refresh: function (frm) {
		frm.trigger("add_custom_buttons");
	},

	validate: function (frm) {
		frm.doc.sales_confirmation_detail.forEach(d => {
			d.amount = (d.qty || 0) * (d.rate || 0);
		});
	},

	add_custom_buttons: function (frm) {
		if (frm.doc.confirmation_date) {
			frm.add_custom_button(__("Validate with PO"), function () {
				return frm.call({
					method: 'validate_with_po',
					doc: frm.doc,
					args: {}
				}).then((r) => {
					frappe.msgprint(__('Items and Purchase Order updated.'))
				});
			});
		}


		if (frm.doc.confirmation_date) {
			frm.add_custom_button(__("Update Items & PO"), function () {
				return frm.call({
					method: 'update_items_and_po',
					doc: frm.doc,
					args: {}
				}).then((r) => {
					frappe.msgprint(__('Items and Purchase Order updated.'))
				});
			});
		}

		let fieldname = 'sales_confirmation_detail', grid = frm.fields_dict[fieldname].grid;
		grid.wrapper.find(".grid-upload").removeClass('hidden').on("click", () => {

			new frappe.ui.FileUploader({
				as_dataurl: true,
				allow_multiple: false,
				on_success(file) {
					var reader = new FileReader();
					reader.onload = function (e) {
						var rowNum;
						var workbook = XLSX.readFile(e.target.result);
						var ws = workbook.Sheets['Sales Confirmation Details'];
						set_sheet_ref(ws, 5);
						var csv = XLSX.utils.sheet_to_csv(ws, { blankrows: false });
						var data = frappe.utils.csv_to_array(csv);
						frappe.utils.add_rows(frm, frm.fields_dict[fieldname], data)
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
				});

		});
	}
});

const value_formatter_map = {
	"Date": val => val ? frappe.datetime.user_to_str(val) : val,
	"Int": val => cint(val),
	"Check": val => cint(val),
	"Float": val => flt(val),
};

frappe.utils.add_rows = function (frm, grid_field, data) {
	frm.clear_table(grid_field.df.fieldname);

	const HEADER_ROW = 0;
	const fieldnames = data[HEADER_ROW].map(i => { return frappe.scrub(i) });

	$.each(data.slice(1), (i, row) => {
		if (row.some((cell) => cell != undefined)) {
			let d = frm.add_child(grid_field.df.fieldname);
			$.each(row, (ci, value) => {
				let fieldname = fieldnames[ci];
				let df = frappe.meta.get_docfield(grid_field.df.options, fieldname);
				if (df) {
					d[fieldnames[ci]] = value_formatter_map[df.fieldtype]
						? value_formatter_map[df.fieldtype](value)
						: value;
				}
			});
		}
	});
	frm.refresh_field(grid_field.df.fieldname)

}

function set_sheet_ref(ws, skip_rows = 0) {
	var rowNum;
	var range = XLSX.utils.decode_range(ws['!ref']);
	for (rowNum = skip_rows + 1; rowNum <= range.e.r; rowNum++) {
		var nextCell = ws[XLSX.utils.encode_cell({ r: rowNum, c: 1 })];
		if (typeof nextCell === 'undefined') {
			break
		}
	}
	ws['!ref'] = "A6:Q" + rowNum;
}