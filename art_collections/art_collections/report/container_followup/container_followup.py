# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    return get_columns(filters), get_data(filters)


def get_data(filters=None):

    data = frappe.db.sql(
        """
select 
	tas.name , tas.owner ,
	tasc.container_name , tasc.type_of_reception , tas.shipping_date ,
	tasc.arrival_forecast_date , tasc.arrival_forecast_hour , tas.telex_release_sent_date 
from `tabArt Shipment` tas 
left outer join `tabArt Shipment Container` tasc on tasc.parent = tas.name
                """.format(
            conditions=get_conditions(filters)
        ),
        filters,
        as_dict=True,
        # debug=True,
    )

    return data


def get_columns(filters):
    return csv_to_columns(
        """
        Shipment Name,name,Link,Art Shipment,140
        Created By,owner,Link,User,120
        Container #,container_name,,,145
        Transport Type,type_of_reception,,,130
        Transport Size,size,,,130
        Shipping Date,shipping_date,Date,,130
        Arrival Forecast Date,arrival_forecast_date,Date,,130
        Arrival Forecast Hour,arrival_forecast_hour,,,130
        Telex Release Sent Date,telex_release_sent_date,Date,,130
        """
    )


def get_conditions(filters):
    conditions = []

    if filters.get("customer"):
        conditions.append("tc.name = %(customer)s")

    if filters.get("territory"):
        conditions.append("tc.territory = %(territory)s")

    if filters.get("brand"):
        conditions.append("ti.brand = %(brand)s")

    return conditions and " and " + " and ".join(conditions) or ""


def csv_to_columns(csv_str):
    props = ["label", "fieldname", "fieldtype", "options", "width"]
    return [
        zip(props, [x.strip() for x in col.split(",")])
        for col in csv_str.split("\n")
        if col.strip()
    ]
