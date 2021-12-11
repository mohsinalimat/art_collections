frappe.listview_settings["Sales Order"] = {
  refresh: function (me) {
    //   
  },

  onload: function (listview) {
    var method =
      "art_collections.sales_order_controller.make_sales_invoice";

    listview.page.add_action_item(__("Make Sales Invoice"), function () {
      listview.call_for_selected_items(method, {});
    });

  },
  // add_fields: ["title","is_offline_art","status","delivery_date","grand_total","per_billed","per_delivered"],
  // hide_name_column: true
};
