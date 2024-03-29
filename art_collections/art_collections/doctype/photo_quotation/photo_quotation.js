// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.delete_lead_item = function (li_name) {
  frappe.confirm(
    __("Are you sure you want to delete Lead Item {}?", [li_name]),
    function () {
      frappe.dom.freeze(__("Deleting Lead Items {0}", [li_name]));
      return cur_frm
        .call({
          method: "delete_lead_item",
          doc: cur_frm.doc,
          args: {
            docname: li_name,
          },
        })
        .then((r) => {
          cur_frm.reload_doc();
          frappe.dom.unfreeze();
        });
    }
  );
};

frappe.ui.form.on("Photo Quotation", {
  setup: function (frm) {
    frm.set_query("contact_person", () => {
      return {
        query: "frappe.contacts.doctype.contact.contact.contact_query",
        filters: {
          link_doctype: "Supplier",
          link_name: frm.doc.supplier,
        },
      };
    });
  },

  refresh: function (frm) {
    make_items_grid(frm);
    if (!frm.is_new()) {
      frm.trigger("add_custom_buttons");
    }
  },

  validate_is_clean: function (frm) {
    if (frm.is_dirty()) {
      frappe.throw(__("Unsaved changes. Please save the changes."));
    }
  },

  supplier: function (frm) {
    frappe.call({
      method: "art_collections.controllers.utils.set_contact_details",
      args: {
        party_name: frm.doc.supplier,
        party_type: "Supplier",
      },
      callback: function (r) {
        if (r.message) {
          frm.set_value(r.message);
        }
      },
    });
  },

  add_custom_buttons: function (frm) {
    frm.add_custom_button(
      __("Create Items"),
      function () {
        frm.trigger("validate_is_clean");
        // let items = frm.items_table.getData().map(i=>{i.is_sample_validated and i.});
        frappe.confirm(
          __(
            `All Items that are validated will be created. Do you wish to proceed?`
          ),
          () => {
            return frm
              .call({
                method: "create_items",
                doc: frm.doc,
                args: {},
              })
              .then((r) => {
                frappe.msgprint(__("{0} item(s) created.", [r.message]));
              });
          }
        );
      },
      __("Create")
    );

    frm.add_custom_button(
      __("Create or Modify Purchase Order"),
      function () {
        frm.trigger("validate_is_clean");
        return frm
          .call({
            method: "create_purchase_order",
            doc: frm.doc,
            args: {},
          })
          .then((r) => {
            console.log("Created PO: ", r.message);
            frappe.set_route("Form", "Purchase Order", r.message);
          });
      },
      __("Create")
    );

    frm.add_custom_button(
      __("Bulk Photo Import"),
      function () {
        var file_num = 0,
          fup = new frappe.ui.FileUploader({
            method:
              "art_collections.art_collections.doctype.photo_quotation.photo_quotation.import_lead_item_photos",
            doctype: frm.doctype,
            docname: frm.docname,
            frm: frm,
            folder: "Home/Attachments",
            on_success: (file_doc) => {
              if (
                file_doc.content_hash &&
                file_doc.content_hash.startsWith("Duplicate photo.")
              ) {
                frappe.show_alert(file_doc.content_hash);
              }

              file_num++;
              if (file_num == fup.uploader.files.length) {
                frm.reload_doc();
              }
            },
          });

        console.log(fup);
      },
      __("Tools")
    );

    frm.add_custom_button(
      __("Email Supplier for Quotation"),
      function () {
        return frm.call({
          method: "get_supplier_email",
          doc: frm.doc,
          args: {
            template: "lead_items_supplier_template",
            supplier: frm.doc.supplier,
            filters: "supplier_quotation",
          },
        });
      },
      __("Tools")
    );

    frm.add_custom_button(
      __("Email Supplier for Sample"),
      function () {
        return frm.call({
          method: "get_supplier_email",
          doc: frm.doc,
          args: {
            template: "lead_items_supplier_template",
            supplier: frm.doc.supplier,
            filters: "supplier_sample_request",
          },
        });
      },
      __("Tools")
    );

    frm.add_custom_button(
      __("Delete all Lead Items"),
      function () {
        frappe.confirm(
          __("Are you sure you want to delete all lead items ?"),
          () => {
            frappe.dom.freeze(
              __("Deleting Lead Items for {0}", [frm.doc.name])
            );
            return frm
              .call({
                method: "delete_all_lead_items",
                doc: frm.doc,
                args: {},
              })
              .then((r) => {
                frm.reload_doc();
                frappe.dom.unfreeze();
              });
          }
        );
      },
      __("Tools")
    );
  },

  before_save: function (frm) {
    let data = frm.items_table.getData();
    // console.log(data);
    return frm.call({
      method: "update_lead_items",
      doc: frm.doc,
      args: {
        items: data,
      },
    });
  },

  upload_items: function (frm) {
    new frappe.ui.FileUploader({
      as_dataurl: true,
      allow_multiple: false,
      on_success(file) {
        var reader = new FileReader();
        reader.onload = function (e) {
          var workbook = XLSX.read(e.target.result);
          let data = get_excel_data(workbook, "Lead Items", "configuration");
          frm.items_table.setData(data);
          frm.dirty();
        };
        reader.readAsArrayBuffer(file.file_obj);
      },
    });
  },

  make_items_grid: function (frm) {
    make_items_grid(frm);
  },

  download_items: function (template) {
    // let data = [cur_frm.items_table.getHeaders().split(",")].concat(cur_frm.items_table.getData());
    // const worksheet = XLSX.utils.aoa_to_sheet(data);
    // const workbook = XLSX.utils.book_new();
    // XLSX.utils.book_append_sheet(workbook, worksheet, 'Lead Items');
    // XLSX.writeFile(workbook, cur_frm.doc.name + "-Lead Items.xlsx");

    // template = cur_frm.templatesDD.getValue();
    // if (!template) {
    //   frappe.throw("Please select a template to download");
    // }
    template = "artyfetes";
    open_url_post(
      "/api/method/art_collections.art_collections.doctype.photo_quotation.photo_quotation.download_lead_items_template",
      {
        docname: cur_frm.doc.name,
        template: template,
        supplier: cur_frm.doc.supplier,
      }
    );
  },

  supplier_quotation_email_callback: function (frm) {
    // set status after email is sent
    setTimeout(() => {
      frappe.call({
        method:
          "art_collections.art_collections.doctype.photo_quotation.photo_quotation.supplier_quotation_email_callback",
        args: {
          docname: frm.doc.name,
        },
        callback: function (r) {
          frm.reload_doc();
        },
      });
      // timeout to allow form to reload. else it throws document has been modified error
    }, 400);
  },

  supplier_sample_request_email_callback: function (frm) {
    // set status after email is sent
    setTimeout(() => {
      frappe.call({
        method:
          "art_collections.art_collections.doctype.photo_quotation.photo_quotation.supplier_sample_request_email_callback",
        args: {
          docname: frm.doc.name,
        },
        callback: function (r) {
          frm.reload_doc();
        },
      });
      // timeout to allow form to reload. else it throws document has been modified error
    }, 400);
  },
});

function make_items_grid(frm) {
  if (frm.items_table)
    jspreadsheet.destroy(document.getElementById("items-table"), false);
  //
  const tmpl = `<div id="items-table"></div>`;
  let items_html = frm.fields_dict["items_html"];
  items_html.$wrapper.html(tmpl);
  let width = items_html.$wrapper.closest("div.section-body").width();

  frm
    .call({
      method: "get_lead_items",
      doc: frm.doc,
      args: {},
    })
    .then((r) => {
      // console.log(r.message.columns);

      let columns = r.message.columns.map((t) => {
        return {
          title: t.label,
          type: t.fieldtype,
          fieldname: t.fieldname,
          readOnly: [
            "photo_quotation",
            "name",
            "is_item_created",
            "is_po_created",
          ].includes(t.fieldname),
        };
      });

      columns.push({
        fieldname: "delete_lead_item",
        fieldtype: "html",
        title: "Delete Item",
        readOnly: 1,
      });

      // https://bossanova.uk/jspreadsheet/v4/docs/quick-reference
      let items_table = jspreadsheet(document.getElementById("items-table"), {
        filters: true,
        columns: columns,
        minDimensions: [columns.length, 3],
        defaultColWidth: 100,
        tableOverflow: true,
        tableWidth: `${width - 30}px`,
        tableHeight: "500px",
        search: true,
        freezeColumns: 1,
        allowManualInsertRow: false,
        allowManualInsertColumn: false,
        // pagination: 10,
        updateTable: function (instance, cell, col, row, val, id) {
          if (col == 0 && val) {
            cell.innerHTML =
              '<img src="' + val + '" style="width:40px;height:40px">';
          } else if (col == columns.length - 1) {
            if (val)
              cell.innerHTML = `<button onclick='frappe.delete_lead_item("${val}");'>Delete</button>`;
          }
        },
        onafterchanges: function (instance) {
          frm.dirty();
        },
      });

      items_table.setData(r.message.data);
      setup_toolbar();
      window.items_table = frm.items_table = items_table;
    });

  function setup_toolbar() {
    let html = `
		<div>
			<div id="templates"></div>
			<button onclick="cur_frm.events.download_items()">Download Items</button>
			<button onclick="cur_frm.events.upload_items(cur_frm)">Upload</button>
			<button onclick="cur_frm.trigger('make_items_grid')">Reload Items</button>
		</div>
		`;
    $(html).appendTo(".jexcel_filter");
    // cur_frm.templatesDD = jSuites.dropdown(
    //   document.getElementById("templates"),
    //   {
    //     data: [
    //       { text: "Artyfetes", value: "artyfetes" },
    //       { text: "Supplier Quotation", value: "supplier_quotation" },
    //       { text: "Sample Request", value: "supplier_sample_request" },
    //       { text: "Create Items", value: "create_lead_items" },
    //     ],
    //     placeholder: "Select a template to Download",
    //     width: "240px",
    //     onchange: function (el, value) {
    //       // cur_frm.events.download_items(el.value);
    //     },
    //   }
    // );

    $(".jexcel_filter").css("justify-content", "right");
  }
}

function get_excel_data(workbook, data_sheet, configuration_sheet) {
  // excel
  // read configuration sheet for skip rows and field names
  let config_ws = workbook.Sheets[configuration_sheet];
  set_sheet_range(config_ws, 1, 2);
  let aoa = frappe.utils.csv_to_array(XLSX.utils.sheet_to_csv(config_ws));
  let skip_rows = cint(aoa[0][2]);
  var excel_columns = aoa.map((i) => i[1]);

  // get data from Lead Items
  let ws = workbook.Sheets["Lead Items"];
  set_sheet_range(ws, skip_rows, excel_columns.length);
  let csv = XLSX.utils.sheet_to_csv(ws);
  var data = frappe.utils.csv_to_array(csv);

  // fix for frappe bug: when first col of first row is blank
  if (csv.startsWith(",")) {
    data[0].unshift("");
  }

  // get columns in grid, and reshape excel as per grid columns
  let grid_columns = items_table.getConfig().columns.map((t) => t.fieldname);
  let grid_data = items_table.getData();

  let values = [],
    item = [],
    idx = -1;
  for (const row of data) {
    // item = grid_data.filter((t) => t.at(-1) === row.at(-1));
    // if (item.length) {
    //   item = item[0];
    // } else {
    //   // initialize blank array
    //   item = Array.from({ length: grid_columns.length }, (v, i) => null);
    // }
    item = Array.from({ length: grid_columns.length }, (v, i) => null);

    grid_columns.forEach((col, i) => {
      idx = excel_columns.indexOf(col);
      if (idx > -1 && row[idx] && row[idx] != "") {
        item[i] = row[idx];
      }
    });

    values.push(item);
  }
  return values;
}

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
