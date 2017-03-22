# mystatsmpg
mystatsmpg is a pyhton library to read stats provided by http://statsl1mpg.over-blog.com/


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

