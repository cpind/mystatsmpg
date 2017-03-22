# mystatsmpg
pystatsmpg is a python library to read football stats provided by http://statsl1mpg.over-blog.com/. 

It allows to export data to csv.

As a plus, pystatsmpg helps keeping track of goals scored each day. Indeed, http://statsl1mpg.over-blog.com/ reports only the total amount of goals scored for each players at the day of publication. Allowing to update the data each time with the newly  publicated sheet, it allows to consolidate the data and keep track of goal for each day.


Installation
------------

    pip install -r requirements.txt

Usage
-----

    python -m pystatsmpg.py stats file.xlsx

Will extract data from file.xlsx and store csv dumps for teams and players in the stas directory. When run another time with file from next day, will update data in stats, keeping track of dayly goals

Run tests
---------

    pytest test_pystatsmpg.py

