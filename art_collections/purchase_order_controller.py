from __future__ import unicode_literals
from distutils.log import debug
from operator import add
import frappe
from frappe import _
from frappe.utils import flt, cstr
from frappe.utils import getdate, format_date
from frappe.utils import nowdate, add_days
from frappe.utils.data import today
from art_collections.item_controller import get_cbm_per_outer_carton
from art_collections.item_controller import get_qty_of_outer_cartoon

import re
from io import BytesIO
import io
import openpyxl
import xlrd
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from frappe.utils import cint, get_site_url, get_url


def purchase_order_custom_validation(self, method):
    fill_item_pack_details(self)
    check_set_apart_item_matches_po_item(self)
    check_set_apart_qty(self)

def check_set_apart_item_matches_po_item(self):
    for set_apart_item in self.set_apart_po_item_for_customer_cf:
        found=False
        for item in self.items:
            if item.item_code == set_apart_item.item_code:
                found=True
        if found==False:
            frappe.throw(_('Set Apart has Item {0}. It is not part of PO Items. Please remove it to proceed..'.format(frappe.bold(set_apart_item.item_code))))

def check_set_apart_qty(self):
    # set_apart_result= [{'item': 1, 'qty': 1}, {'item': 2, 'qty': 2}]
    set_apart_result=[]
    for set_apart_item in self.set_apart_po_item_for_customer_cf:
        found=False
        for item in set_apart_result:
            if item['item']==set_apart_item.item_code:
                item['qty']=item['qty']+set_apart_item.qty
                found=True
        if found==False:
            set_apart_result.append({'item':set_apart_item.item_code,'qty':set_apart_item.qty})

    print(set_apart_result)
    for item in self.items:
        for set_result_item in set_apart_result:
            if item.item_code == set_result_item['item']:
                if item.qty < set_result_item['qty']:
                    frappe.throw(_('Set Apart Item {0} has qty {1}. It cannot be greater than {2}'
                    .format(frappe.bold(item.item_code),frappe.bold(set_result_item['qty']),frappe.bold(item.qty))))

def fill_item_pack_details(self):
    # commenting as per #312
    # total_outer_cartons_art, cbm_per_outer_art, total_cbm values in po item 
    # are updated from Sales Confirmation Detail
    # total_cbm_art = 0
    # total_outer_cartons_ordered_art = 0
    # for item in self.items:
    #     total_outer_cartons_art = 0

    #     item.cbm_per_outer_art = flt(get_cbm_per_outer_carton(item.item_code))

    #     total_outer_cartons_art = flt(
    #         item.stock_qty / (get_qty_of_outer_cartoon(item.item_code))
    #     ) if get_qty_of_outer_cartoon(item.item_code) else total_outer_cartons_art
    #     item.total_outer_cartons_art = total_outer_cartons_art

    #     if total_outer_cartons_art != 0 and item.cbm_per_outer_art:
    #         item.total_cbm = flt(total_outer_cartons_art * item.cbm_per_outer_art)
    #         total_cbm_art += item.total_cbm
    #     total_outer_cartons_ordered_art += total_outer_cartons_art

    self.total_outer_cartons_ordered_art = sum([d.get('total_outer_cartons_art',0) for d in self.items])
    self.total_cbm_art = sum([d.get('total_cbm',0) for d in self.items])

    twenty_foot_filling_percentage=frappe.db.get_single_value('Art Collections Settings', 'filling_percentage_for_20_foot_container') or 28
    forty_foot_filling_percentage=frappe.db.get_single_value('Art Collections Settings', 'filling_percentage_for_40_foot_container') or 63
    self.filling_percentage_of_20_foot_container_art = (self.total_cbm_art * 100) / twenty_foot_filling_percentage
    self.filling_percentage_of_40_foot_container_art = (self.total_cbm_art * 100) / forty_foot_filling_percentage


def purchase_order_custom_on_submit(self, method):

    # previous logic based on expected_delivery_date
    # purchase_order_update_delivery_date_of_item(self,method)

    # previous logic based on schedule_date i.e. required_by_date
    # purchase_order_update_schedule_date_of_item(self,method)

    # new logic based on shipping date(i.e. shipping_date_art) + buffer from settings
    # new logic doesn't consider schedule_date OR expected_delivery_date
    # update_availability_date_of_item_based_on_po_shipping_date_art(self, method)

    set__availability_date_to_blank_for_item_based_on_po_shipping_date_art(self,method)


def set__availability_date_to_blank_for_item_based_on_po_shipping_date_art(self,method):
    for po_item in self.get("items"):
        # no more PO shipping_date to be received ( No submitted PO with Item exist having blank shipping_date )
        if flt(po_item.received_qty) == flt(po_item.stock_qty) and check_previous_submitted_po_item_with_no_blank_shipping_date_exist(po_item.item_code)==True:
            frappe.db.set_value("Item",po_item.item_code,"availability_date_art",None)
            frappe.msgprint(_("Availability date for item {0} is set to blank.".format(
                        po_item.item_code)),indicator="orage",alert=True)                



# def purchase_order_update_delivery_date_of_item(self, method):
#     from frappe.utils import add_days

#     for item in self.get("items"):
#         if item.expected_delivery_date:
#             lag_days = 45
#             availability_date = add_days(item.expected_delivery_date, lag_days)
#             frappe.db.set_value(
#                 "Item", item.item_code, "availability_date_art", availability_date
#             )


# def purchase_order_update_schedule_date_of_item(self, method):
#     if (
#         method == "on_update_after_submit" and self.docstatus == 1
#     ) or method == "on_submit":
#         for po_item in self.get("items"):
#             availability_date = frappe.db.get_value(
#                 "Item", po_item.item_code, "availability_date_art"
#             )
#             if availability_date == None or getdate(availability_date) < getdate(
#                 po_item.schedule_date
#             ):
#                 frappe.db.set_value(
#                     "Item",
#                     po_item.item_code,
#                     "availability_date_art",
#                     po_item.schedule_date,
#                 )
#                 frappe.msgprint(
#                     _(
#                         "Availability date for item {0} is changed to {1} based on latest required by date.".format(
#                             po_item.item_name,
#                             frappe.bold(format_date(po_item.schedule_date)),
#                         )
#                     ),
#                     indicator="orage",
#                     alert=True,
#                 )


# def update_availability_date_of_item_based_on_po_shipping_date_art(self, method):
#     item_availability_buffer_days = frappe.db.get_single_value(
#         "Art Collections Settings", "item_availability_buffer_days"
#     )
#     for po_item in self.get("items"):
#         old_item_required_by_date = check_previous_po_item_is_not_received(
#             po_item.item_code
#         )
#         availability_date = frappe.db.get_value(
#             "Item", po_item.item_code, "availability_date_art"
#         )
#         required_by_date_with_buffer = add_days(
#             po_item.shipping_date_art, item_availability_buffer_days
#         )
#         print('po_item.shipping_date_art',po_item.shipping_date_art)
#         print("print(old_item_required_by_date,availability_date,required_by_date_with_buffer)")
#         print(old_item_required_by_date,availability_date,required_by_date_with_buffer)
#         #  2022-05-27 2022-05-31 2022-06-04
#         if old_item_required_by_date:
#             # previous po is pending
#             old_item_required_by_date_with_buffer = add_days(
#                 old_item_required_by_date, item_availability_buffer_days
#             )
#             if getdate(old_item_required_by_date_with_buffer) < getdate(today()):
#                 print('previous po required by date with buffer has passed, so set new availability date')
#                 #  previous po required by date with buffer has passed, so set new availability date
#                 if getdate(required_by_date_with_buffer) > getdate(availability_date):
#                     print('new calculated required by date is greater than availability date , hence change it')
#                     # new calculated required by date is greater than availability date , hence change it
#                     frappe.db.set_value(
#                         "Item",
#                         po_item.item_code,
#                         "availability_date_art",
#                         required_by_date_with_buffer,
#                     )
#                     frappe.msgprint(
#                         _(
#                             "Availability date for item {0} is changed to {1} based on latest shipping date with buffer of {2} days.".format(
#                                 po_item.item_name,
#                                 frappe.bold(format_date(required_by_date_with_buffer)),
#                                 item_availability_buffer_days,
#                             )
#                         ),
#                         indicator="orage",
#                         alert=True,
#                     )
#             else:
#                 print('previous po required by date is futuristic , so nothing')
#                 # previous po required by date is futuristic , so nothing
#                 pass
#         else:
#             # no previous po pending
#             print('no previous po pending')
#             if getdate(required_by_date_with_buffer) > getdate(availability_date):
#                 # new calculated required by date is greater than availability date , hence change it
#                 frappe.db.set_value(
#                     "Item",
#                     po_item.item_code,
#                     "availability_date_art",
#                     required_by_date_with_buffer,
#                 )
#                 frappe.msgprint(
#                     _(
#                         "Availability date for item {0} is changed to {1} based on latest shipping date with buffer of {2} days.".format(
#                             po_item.item_name,
#                             frappe.bold(format_date(required_by_date_with_buffer)),
#                             item_availability_buffer_days,
#                         )
#                     ),
#                     indicator="orage",
#                     alert=True,
#                 )


def check_previous_po_item_is_not_received(item_code):
    check_previous_po_item_is_not_received = frappe.db.sql(
        """SELECT  POI.shipping_date_art as required_by_date
    FROM  `tabPurchase Order` PO inner join `tabPurchase Order Item` POI 
    on PO.name=POI.parent
    where PO.status in ('To Receive and Bill','To Receive')
    and POI.received_qty =0	and POI.item_code = %s""",
        (item_code),
        as_dict=True,
    )
    if len(check_previous_po_item_is_not_received) > 0:
        return check_previous_po_item_is_not_received[0].required_by_date
    else:
        return None

# No submitted PO with Item exist having blank shipping_date 
def check_previous_submitted_po_item_with_no_blank_shipping_date_exist(item_code):
    check_previous_with_blank_shipping_date_exist = frappe.db.sql(
        """SELECT  POI.shipping_date_art 
    FROM  `tabPurchase Order` PO inner join `tabPurchase Order Item` POI 
    on PO.name=POI.parent
    where PO.docstatus =1
    and POI.shipping_date_art  IS NULL and POI.item_code = %s""",
        (item_code),
        as_dict=True,
    )
    if len(check_previous_with_blank_shipping_date_exist) > 0:
        return False
    else:
        return True

def get_po_dashboard_links(data):
    data["non_standard_fieldnames"].update({"Supplier Packing List Art":"purchase_order"})

    for d in data.get("transactions",[]):
        if d.get("label") == _("Reference"):
            d.update({"items":d.get("items")+["Supplier Packing List Art"]})

    return data

@frappe.whitelist()
def get_connected_shipment(purchase_order):
	shipment_list=[]
	shipment_results=frappe.db.sql("""SELECT distinct shipment   FROM `tabSupplier Packing List Detail Art`
							where docstatus!=2 and purchase_order =%s""",
        (purchase_order),as_dict=True)
	if len(shipment_results)>0:
		for shipment in shipment_results:
			shipment_list.append(shipment.shipment)
		return shipment_list
	else:
		return []    