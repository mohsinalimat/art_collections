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
  get_indicator: function (doc) {
    var status_color = {
       "Draft": "gray",
      "On Hold": "blue",
      "To Deliver and Bill": "orange",
      "To Bill": "orange",
      "To Deliver": "orange",
      "Completed": "green",
      "Cancelled": "red",
      "Closed" : "red"
		};
    if (doc.status) {
      return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
    }
  }  
  // add_fields: ["title","is_offline_art","status","delivery_date","grand_total","per_billed","per_delivered"],
  // hide_name_column: true
};
