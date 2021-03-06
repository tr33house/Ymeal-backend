from BeautifulSoup import BeautifulSoup as bs
from HTMLParser import HTMLParser
import datetime
from api.models import Cafeteria, Attribute, Meal, Serving

import urllib2

def get_attribute(obj, prop='menudate'):
    attrs = obj.attrs
    prop = prop.lower()
    if not attrs:
        return None
    for attr in attrs:
        if attr[0].lower() == prop:
            return attr[1]
    return None

#----- better versions -xml, not rss
# http://legacy.cafebonappetit.com/feeds/daily/684
# http://legacy.cafebonappetit.com/feeds/weekly/684

cafes = {
        'urls':684,
        'building e':682,
        'building g':674,
        'boardwalk':358
        }

html_escaper = HTMLParser()
# cafe and ID on bon-appetit website
for cafe,ba_id in cafes.items():
    url = 'http://legacy.cafebonappetit.com/feeds/weekly/'+str(ba_id)
    try:
        response = urllib2.urlopen(url)
        data = bs(response.read())
    except:
        # try again
        try:
            response = urllib2.urlopen(url)
            data = bs(response.read())
        except:
            import sys
            sys.exit(1)
    days = data.findAll('tblmenu')

    # todo make this more modular. possibly recursive or functional
    for day in days:
        date = get_attribute(day, 'menudate')
        if date:
            date = datetime.datetime.strptime(date, '%m/%d/%Y').date()
        periods = day.findAll('tbldaypart')
        try:
            for period in periods:
                # bld -> breakfast, lunch or dinner (these are the options as well)
                bld = period.txtdaypartdescription.text.lower()
                print bld
                stations = period.findAll('tblstation')
                for station in stations:
                    try:
                        station_name = station.txtstationdescription.text
                        try:
                            meals = day.findAll('tblitem')
                            for meal in meals:
                                try:
                                    meal_name = meal.txttitle.text
                                    meal_descr = meal.txtdescription.text
                                    attrs = meal.findAll('txtattribute')
                                    attr_li = []
                                    for at in attrs:
                                        try:
                                            attr_li.append(at.description.text)
                                        except:
                                            pass
                                    # save stuff
                                    db_attrs = []
                                    for _atrr in attr_li:
                                        try:
                                            db_attrs.append(
                                                Attribute.objects.get_or_create(
                                                    description=_atrr.lower())[0]
                                                )
                                        except:
                                            pass
                                    # fails if no object is found
                                    try:
                                        db_meal = Meal.objects.get(
                                            name=html_escaper.unescape(meal_name).lower(),
                                            description=html_escaper.unescape(meal_descr).lower()
                                        )
                                    except:
                                        # new entry
                                        db_meal = Meal(
                                            name=meal_name.lower(),
                                            description=meal_descr.lower()
                                        )
                                        db_meal.save()
                                        if db_attrs:
                                            try:
                                                 db_meal.attributes.add(*db_attrs)
                                            except:
                                                pass
                                        db_meal.save()
                                    db_location = Cafeteria.objects.get_or_create(
                                        name=cafe.lower()
                                    )[0]
                                    # for some reason get_or_create keeps failing with errors
                                    try:
                                        db_serving = Serving.objects.get(
                                            meal=db_meal,
                                            location=db_location,
                                            date=date,
                                            time_of_day=Serving.BREAKFAST if bld=='breakfast' else Serving.LUNCH if bld=='lunch' else Serving.DINNER,
                                            category = station_name.lower()
                                        )
                                    except:
                                        db_serving =  Serving(
                                            meal=db_meal,
                                            location=db_location,
                                            date=date,
                                            time_of_day=Serving.BREAKFAST if bld=='breakfast' else Serving.LUNCH if bld=='lunch' else Serving.DINNER,
                                            category = station_name.lower()
                                        )
                                        db_serving.save()
                                except:
                                    pass
                        except:
                            pass
                    except:
                        pass
        except:
            pass
