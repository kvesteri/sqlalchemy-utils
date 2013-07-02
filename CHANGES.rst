Changelog
---------

Here you can see the full list of changes between each SQLAlchemy-Utils release.


0.14.1 (2013-07-02)
^^^^^^^^^^^^^^^^^^^

- Made sort_query support column_property selects with labels


0.14.0 (2013-07-02)
^^^^^^^^^^^^^^^^^^^

- Python 3 support, dropped python 2.5 support


0.13.3 (2013-06-11)
^^^^^^^^^^^^^^^^^^^

- Initial support for psycopg 2.5 NumericRange objects


0.13.2 (2013-06-11)
^^^^^^^^^^^^^^^^^^^

- QuerySorter now threadsafe.


0.13.1 (2013-06-11)
^^^^^^^^^^^^^^^^^^^

- Made sort_query function support multicolumn sorting.


0.13.0 (2013-06-05)
^^^^^^^^^^^^^^^^^^^

- Added table_name utility function.


0.12.5 (2013-06-05)
^^^^^^^^^^^^^^^^^^^

- ProxyDict now contains None values in cache - more efficient contains method.


0.12.4 (2013-06-01)
^^^^^^^^^^^^^^^^^^^

- Fixed ProxyDict contains method


0.12.3 (2013-05-30)
^^^^^^^^^^^^^^^^^^^

- Proxy dict expiration listener from function scope to global scope


0.12.2 (2013-05-29)
^^^^^^^^^^^^^^^^^^^

- Added automatic expiration of proxy dicts



0.12.1 (2013-05-18)
^^^^^^^^^^^^^^^^^^^

- Added utility functions remove_property and primary_keys



0.12.0 (2013-05-17)
^^^^^^^^^^^^^^^^^^^

- Added ProxyDict


0.11.0 (2013-05-08)
^^^^^^^^^^^^^^^^^^^

- Added coercion_listener


0.10.0 (2013-04-29)
^^^^^^^^^^^^^^^^^^^

- Added ColorType


0.9.1 (2013-04-15)
^^^^^^^^^^^^^^^^^^

- Renamed Email to EmailType and ScalarList to ScalarListType (unified type class naming convention)


0.9.0 (2013-04-11)
^^^^^^^^^^^^^^^^^^

- Added CaseInsensitiveComparator
- Added Email type


0.8.4 (2013-04-08)
^^^^^^^^^^^^^^^^^^

- Added sort by aliased and joined entity


0.8.3 (2013-04-03)
^^^^^^^^^^^^^^^^^^

- sort_query now supports labeled and subqueried scalars


0.8.2 (2013-04-03)
^^^^^^^^^^^^^^^^^^

- Fixed empty ScalarList handling


0.8.1 (2013-04-03)
^^^^^^^^^^^^^^^^^^

- Removed unnecessary print statement form ScalarList
- Documentation for ScalarList and NumberRange


0.8.0 (2013-04-02)
^^^^^^^^^^^^^^^^^^

- Added ScalarList type
- Fixed NumberRange bind param and result value processing


0.7.7 (2013-03-27)
^^^^^^^^^^^^^^^^^^

- Changed PhoneNumber string representation to the national phone number format


0.7.6 (2013-03-26)
^^^^^^^^^^^^^^^^^^

- NumberRange now wraps ValueErrors as NumberRangeExceptions


0.7.5 (2013-03-26)
^^^^^^^^^^^^^^^^^^

- Fixed defer_except
- Better string representations for NumberRange


0.7.4 (2013-03-26)
^^^^^^^^^^^^^^^^^^

- Fixed NumberRange upper bound parsing


0.7.3 (2013-03-26)
^^^^^^^^^^^^^^^^^^

- Enabled PhoneNumberType None value storing


0.7.2 (2013-03-26)
^^^^^^^^^^^^^^^^^^

- Enhanced string parsing for NumberRange


0.7.1 (2013-03-26)
^^^^^^^^^^^^^^^^^^

- Fixed requirements (now supports SQLAlchemy 0.8)


0.7.0 (2013-03-26)
^^^^^^^^^^^^^^^^^^

- Added NumberRange type



0.6.0 (2013-03-26)
^^^^^^^^^^^^^^^^^^

- Extended PhoneNumber class from python-phonenumbers library


0.5.0 (2013-03-20)
^^^^^^^^^^^^^^^^^^

- Added PhoneNumberType type decorator


0.4.0 (2013-03-01)
^^^^^^^^^^^^^^^^^^

- Renamed SmartList to InstrumentedList
- Added instrumented_list decorator


0.3.0 (2013-03-01)
^^^^^^^^^^^^^^^^^^

- Added new collection class SmartList


0.2.0 (2013-03-01)
^^^^^^^^^^^^^^^^^^

- Added new function defer_except()


0.1.0 (2013-01-12)
^^^^^^^^^^^^^^^^^^

- Initial public release
