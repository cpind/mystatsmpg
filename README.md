# mystatsmpg
pystatsmpg is a python library to read football stats provided by http://statsl1mpg.over-blog.com/. 

It allows to export data to csv.

As a plus, pystatsmpg helps keeping track of goals scored each day. Indeed, http://statsl1mpg.over-blog.com/ reports each league day the total goals scored per players, hence the information for each day is missing. pystatsmpg help to keep track of them.


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

