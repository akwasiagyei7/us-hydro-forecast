"""
Study plants: conventional hydroelectric plants in the Southeast U.S.
paired with a USGS streamflow gage on the river that feeds them.

plant_id  = EIA plant code (Form EIA-860/923).
usgs_site = USGS NWIS site number for the paired gage.
"""
PLANTS = {
    2779:  dict(name="Fontana Dam", state="NC", river="Little Tennessee River",
                usgs_site="03503000", gage="Little Tennessee River at Needmore, NC"),
    2715:  dict(name="Walters", state="NC", river="Pigeon River",
                usgs_site="03459500", gage="Pigeon River near Hepco, NC"),
    54894: dict(name="Narrows (NC)", state="NC", river="Yadkin River",
                usgs_site="02116500", gage="Yadkin River at Yadkin College, NC"),
    2714:  dict(name="Tillery", state="NC", river="Yadkin / Pee Dee River",
                usgs_site="02116500", gage="Yadkin River at Yadkin College, NC"),
    2722:  dict(name="Cowans Ford", state="NC", river="Catawba River",
                usgs_site="02140991", gage="Johns River at Arneys Store, NC (Catawba headwater tributary)"),
    3270:  dict(name="Wateree Hydro", state="SC", river="Wateree River",
                usgs_site="02146000", gage="Catawba River near Rock Hill, SC"),
    3323:  dict(name="J Strom Thurmond", state="SC", river="Savannah River",
                usgs_site="02192000", gage="Broad River near Bell, GA (major inflow to Thurmond Lake)"),
    2758:  dict(name="Roanoke Rapids", state="NC", river="Roanoke River",
                usgs_site="02077000", gage="Dan River at Paces, VA"),
}
