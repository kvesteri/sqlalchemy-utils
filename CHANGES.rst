Changelog
---------

Here you can see the full list of changes between each SQLAlchemy-Utils release.


0.32.6 (2016-05-11)
^^^^^^^^^^^^^^^^^^^

- Added support for timezones with ArrowType (#218, pull request courtesy of jmagnusson)


0.32.5 (2016-04-29)
^^^^^^^^^^^^^^^^^^^

- Fixed import issue with latest version of SQLAlchemy (#215)


0.32.4 (2016-04-25)
^^^^^^^^^^^^^^^^^^^

- Added LtreeType for PostgreSQL ltree extension
- Added Ltree primitive data type


0.32.3 (2016-04-20)
^^^^^^^^^^^^^^^^^^^

- Added support for PhoneNumber objects as composites


0.32.2 (2016-04-20)
^^^^^^^^^^^^^^^^^^^

- Fixed PasswordType to not access LazyCryptContext on type init (#211, pull request courtesy of olegpidsadnyi)


0.32.1 (2016-03-30)
^^^^^^^^^^^^^^^^^^^

- Fixed database helpers for sqlite (#208, pull request courtesy of RobertDeRose)
- Fixed TranslationHybrid aliased entities handling (#198, pull request courtesy of jmagnusson)


0.32.0 (2016-03-17)
^^^^^^^^^^^^^^^^^^^

- Dropped py26 support
- Made PasswordType to use LazyCryptContext by default (#204, courtesy of olegpidsadnyi)


0.31.6 (2016-01-21)
^^^^^^^^^^^^^^^^^^^

- Added literal parameter processing for ArrowType (#182, pull request courtesy of jmagnusson)


0.31.5 (2016-01-14)
^^^^^^^^^^^^^^^^^^^

- Fixed scalar parsing of LocaleType (#173)


0.31.4 (2015-12-06)
^^^^^^^^^^^^^^^^^^^

- Fixed column alias handling with assert_* functions (#175)


0.31.3 (2015-11-09)
^^^^^^^^^^^^^^^^^^^

- Fixed non-ascii string handling in composite types (#170)


0.31.2 (2015-10-30)
^^^^^^^^^^^^^^^^^^^

- Fixed observes crashing when observable root_obj is ``None`` (#168)


0.31.1 (2015-10-26)
^^^^^^^^^^^^^^^^^^^

- Column observers only notified when actual changes have been made to underlying columns (#138)


0.31.0 (2015-09-17)
^^^^^^^^^^^^^^^^^^^

- Made has_index allow fk constraint as parameter
- Made has_unique_index allow fk constraint as parameter
- Made the extra packages in setup.py to be returned in deterministic order (courtesy of thomasgoirand)
- Removed is_indexed_foreign_key (superceded by more versatile has_index)
- Fixed LocaleType territory parsing (courtesy of dahlia)


0.30.17 (2015-08-16)
^^^^^^^^^^^^^^^^^^^^

- Added correlate parameter to select_correlated_expression function


0.30.16 (2015-08-04)
^^^^^^^^^^^^^^^^^^^^

- Fixed sort_query handling of aliased classes with hybrid properties


0.30.15 (2015-07-28)
^^^^^^^^^^^^^^^^^^^^

- Added support for aliased classes in get_hybrid_properties utility function


0.30.14 (2015-07-23)
^^^^^^^^^^^^^^^^^^^^

- Added cast_if utility function


0.30.13 (2015-07-21)
^^^^^^^^^^^^^^^^^^^^

- Added support for InstrumentedAttributes, ColumnProperties and Columns in get_columns function


0.30.12 (2015-07-05)
^^^^^^^^^^^^^^^^^^^^

- Added support for PhoneNumber extensions (#121)


0.30.11 (2015-06-18)
^^^^^^^^^^^^^^^^^^^^

- Fix None type handling of ChoiceType
- Make locale casting for translation hybrid expressions cast locales on compilation phase. This extra lazy locale casting is needed in some cases where translation hybrid expressions are used before get_locale
function is available.


0.30.10 (2015-06-17)
^^^^^^^^^^^^^^^^^^^^

- Added better support for dynamic locales in translation_hybrid
- Make babel dependent primitive types to use Locale('en') for data validation instead of current locale. Using current locale leads to infinite recursion in cases where the loaded data has dependency to the loaded object's locale.


0.30.9 (2015-06-09)
^^^^^^^^^^^^^^^^^^^

- Added get_type utility function
- Added default parameter for array_agg function


0.30.8 (2015-06-05)
^^^^^^^^^^^^^^^^^^^

- Added Asterisk compiler
- Added row_to_json GenericFunction
- Added array_agg GenericFunction
- Made quote function accept dialect object as the first paremeter
- Made has_index work with tables without primary keys (#148)


0.30.7 (2015-05-28)
^^^^^^^^^^^^^^^^^^^

- Fixed CompositeType null handling


0.30.6 (2015-05-28)
^^^^^^^^^^^^^^^^^^^

- Made psycopg2 requirement optional (#145, #146)
- Made CompositeArray work with tuples given as bind parameters


0.30.5 (2015-05-27)
^^^^^^^^^^^^^^^^^^^

- Fixed CompositeType bind parameter processing when one of the fields is of TypeDecorator type and
CompositeType is used inside ARRAY type.


0.30.4 (2015-05-27)
^^^^^^^^^^^^^^^^^^^

- Fixed CompositeType bind parameter processing when one of the fields is of TypeDecorator type.


0.30.3 (2015-05-27)
^^^^^^^^^^^^^^^^^^^

- Added length property to range types
- Added CompositeType for PostgreSQL


0.30.2 (2015-05-21)
^^^^^^^^^^^^^^^^^^^

- Fixed ``assert_max_length``, ``assert_non_nullable``, ``assert_min_value`` and ``assert_max_value`` not properly raising an ``AssertionError`` when the assertion failed.


0.30.1 (2015-05-06)
^^^^^^^^^^^^^^^^^^^

- Drop undocumented batch fetch feature. Let's wait until the inner workings of SQLAlchemy loading API is well-documented.
- Fixed GenericRelationshipProperty comparator to work with SA 1.0.x (#139)
- Make all foreign key helpers SA 1.0 compliant
- Make translation_hybrid expression work the same way as SQLAlchemy-i18n translation expressions
- Update SQLAlchemy dependency to 1.0


0.30.0 (2015-04-15)
^^^^^^^^^^^^^^^^^^^

- Added __hash__ method to Country class
- Made Country validate itself during object initialization
- Made Country string coercible
- Removed deprecated function generates
- Fixed observes function to work with simple column properties


0.29.9 (2015-04-07)
^^^^^^^^^^^^^^^^^^^

- Added CurrencyType (#19) and Currency class


0.29.8 (2015-03-03)
^^^^^^^^^^^^^^^^^^^

- Added get_class_by_table ORM utility function


0.29.7 (2015-03-01)
^^^^^^^^^^^^^^^^^^^

- Added Enum representation support for ChoiceType


0.29.6 (2015-02-03)
^^^^^^^^^^^^^^^^^^^

- Added customizable TranslationHybrid default value


0.29.5 (2015-02-03)
^^^^^^^^^^^^^^^^^^^

- Made assert_max_length support PostgreSQL array type


0.29.4 (2015-01-31)
^^^^^^^^^^^^^^^^^^^

- Made CaseInsensitiveComparator not cast already lowercased types to lowercase


0.29.3 (2015-01-24)
^^^^^^^^^^^^^^^^^^^

- Fixed analyze function runtime property handling for PostgreSQL >= 9.4
- Fixed drop_database and create_database identifier quoting (#122)


0.29.2 (2015-01-08)
^^^^^^^^^^^^^^^^^^^

- Removed deprecated defer_except (SQLAlchemy's own load_only should be used from now on)
- Added json_sql PostgreSQL helper function


0.29.1 (2015-01-03)
^^^^^^^^^^^^^^^^^^^

- Added assert_min_value and assert_max_value testing functions


0.29.0 (2015-01-02)
^^^^^^^^^^^^^^^^^^^

- Removed TSVectorType.match_tsquery (now replaced by TSVectorType.match to be compatible with SQLAlchemy)
- Removed undocumented function tsvector_concat
- Added support for TSVectorType concatenation through OR operator
- Added documentation for TSVectorType (#102)


0.28.3 (2014-12-17)
^^^^^^^^^^^^^^^^^^^

- Made aggregated fully support column aliases
- Changed test matrix to run all tests without any optional dependencies (as well as with all optional dependencies)


0.28.2 (2014-12-13)
^^^^^^^^^^^^^^^^^^^

- Fixed issue with Color importing (#104)


0.28.1 (2014-12-13)
^^^^^^^^^^^^^^^^^^^

- Improved EncryptedType to support more underlying_type's; now supports: Integer, Boolean, Date, Time, DateTime, ColorType, PhoneNumberType, Unicode(Text), String(Text), Enum
- Allow a callable to be used to lookup the key for EncryptedType


0.28.0 (2014-12-12)
^^^^^^^^^^^^^^^^^^^

- Fixed PhoneNumber string coercion (#93)
- Added observes decorator (generates decorator will be deprecated later)


0.27.11 (2014-12-06)
^^^^^^^^^^^^^^^^^^^^

- Added loose typed column checking support for get_column_key
- Made get_column_key throw UnmappedColumnError to be consistent with SQLAlchemy


0.27.10 (2014-12-03)
^^^^^^^^^^^^^^^^^^^^

- Fixed column alias handling in dependent_objects


0.27.9 (2014-12-01)
^^^^^^^^^^^^^^^^^^^

- Fixed aggregated decorator many-to-many relationship handling
- Fixed aggregated column alias handling


0.27.8 (2014-11-13)
^^^^^^^^^^^^^^^^^^^

- Added is_loaded utility function
- Removed deprecated has_any_changes


0.27.7 (2014-11-03)
^^^^^^^^^^^^^^^^^^^

- Added support for Column and ColumnEntity objects in get_mapper
- Made make_order_by_deterministic add deterministic column more aggressively


0.27.6 (2014-10-29)
^^^^^^^^^^^^^^^^^^^

- Fixed assert_max_length not working with non nullable columns
- Add PostgreSQL < 9.2 support for drop_database


0.27.5 (2014-10-24)
^^^^^^^^^^^^^^^^^^^

- Made assert_* functions automatically rollback session
- Changed make_order_by_deterministic attach order by primary key for queries without order by
- Fixed alias handling in has_unique_index
- Fixed alias handling in has_index
- Fixed alias handling in make_order_by_deterministic


0.27.4 (2014-10-23)
^^^^^^^^^^^^^^^^^^^

- Added assert_non_nullable, assert_nullable and assert_max_length testing functions


0.27.3 (2014-10-22)
^^^^^^^^^^^^^^^^^^^

- Added supported for various SQLAlchemy objects in make_order_by_deterministic (previosly this function threw exceptions for other than Column objects)


0.27.2 (2014-10-21)
^^^^^^^^^^^^^^^^^^^

- Fixed MapperEntity handling in get_mapper and get_tables utility functions
- Fixed make_order_by_deterministic handling for queries without order by (no just silently ignores those rather than throws exception)
- Made make_order_by_deterministic if given query uses strings as order by args


0.27.1 (2014-10-20)
^^^^^^^^^^^^^^^^^^^

- Added support for more SQLAlchemy based objects and classes in get_tables function
- Added has_unique_index utility function
- Added make_order_by_deterministic utility function


0.27.0 (2014-10-14)
^^^^^^^^^^^^^^^^^^^

- Added EncryptedType


0.26.17 (2014-10-07)
^^^^^^^^^^^^^^^^^^^^

- Added explain and explain_analyze expressions
- Added analyze function


0.26.16 (2014-09-09)
^^^^^^^^^^^^^^^^^^^^

- Fix aggregate value handling for cascade deleted objects
- Fix ambiguous column sorting with join table inheritance in sort_query


0.26.15 (2014-08-28)
^^^^^^^^^^^^^^^^^^^^

- Fix sort_query support for queries using mappers (not declarative classes) with calculated column properties


0.26.14 (2014-08-26)
^^^^^^^^^^^^^^^^^^^^

- Added count method to QueryChain class


0.26.13 (2014-08-23)
^^^^^^^^^^^^^^^^^^^^

- Added template parameter to create_database function


0.26.12 (2014-08-22)
^^^^^^^^^^^^^^^^^^^^

- Added quote utility function


0.26.11 (2014-08-21)
^^^^^^^^^^^^^^^^^^^^

- Fixed dependent_objects support for single table inheritance


0.26.10 (2014-08-13)
^^^^^^^^^^^^^^^^^^^^

- Fixed dependent_objects support for multiple dependencies


0.26.9 (2014-08-06)
^^^^^^^^^^^^^^^^^^^

- Fixed PasswordType with Oracle dialect
- Added support for sort_query and attributes on mappers using with_polymorphic


0.26.8 (2014-07-30)
^^^^^^^^^^^^^^^^^^^

- Fixed order by column property handling in sort_query when using polymorphic inheritance
- Added support for synonym properties in sort_query


0.26.7 (2014-07-29)
^^^^^^^^^^^^^^^^^^^

- Made sort_query support hybrid properties where function name != property name
- Made get_hybrid_properties return a dictionary of property keys and hybrid properties
- Added documentation for get_hybrid_properties


0.26.6 (2014-07-22)
^^^^^^^^^^^^^^^^^^^

- Added exclude parameter to has_changes
- Made has_changes accept multiple attributes as second parameter


0.26.5 (2014-07-11)
^^^^^^^^^^^^^^^^^^^

- Added get_column_key
- Added Timestamp model mixin


0.26.4 (2014-06-25)
^^^^^^^^^^^^^^^^^^^

- Added auto_delete_orphans


0.26.3 (2014-06-25)
^^^^^^^^^^^^^^^^^^^

- Added has_any_changes


0.26.2 (2014-05-29)
^^^^^^^^^^^^^^^^^^^

- Added various fixes for bugs found in use of psycopg2
- Added has_index


0.26.1 (2014-05-14)
^^^^^^^^^^^^^^^^^^^

- Added get_bind
- Added group_foreign_keys
- Added get_mapper
- Added merge_references


0.26.0 (2014-05-07)
^^^^^^^^^^^^^^^^^^^

- Added get_referencing_foreign_keys
- Added get_tables
- Added QueryChain
- Added dependent_objects


0.25.4 (2014-04-22)
^^^^^^^^^^^^^^^^^^^

- Added ExpressionParser


0.25.3 (2014-04-21)
^^^^^^^^^^^^^^^^^^^

- Added support for primary key aliases in get_primary_keys function
- Added get_columns utility function


0.25.2 (2014-03-25)
^^^^^^^^^^^^^^^^^^^

- Fixed sort_query handling of regular properties (no longer throws exceptions)


0.25.1 (2014-03-20)
^^^^^^^^^^^^^^^^^^^

- Added more import json as a fallback if anyjson package is not installed for JSONType
- Fixed query_entities labeled select handling


0.25.0 (2014-03-05)
^^^^^^^^^^^^^^^^^^^

- Added single table inheritance support for generic_relationship
- Added support for comparing class super types with generic relationships
- BC break: In order to support different inheritance strategies generic_relationship now uses class names as discriminators instead of table names.


0.24.4 (2014-03-05)
^^^^^^^^^^^^^^^^^^^

- Added hybrid_property support for generic_relationship


0.24.3 (2014-03-05)
^^^^^^^^^^^^^^^^^^^

- Added string argument support for generic_relationship
- Added composite primary key support for generic_relationship


0.24.2 (2014-03-04)
^^^^^^^^^^^^^^^^^^^

- Remove toolz from dependencies
- Add step argument support for all range types
- Optional intervals dependency updated to 0.2.4


0.24.1 (2014-02-21)
^^^^^^^^^^^^^^^^^^^

- Made identity return a tuple in all cases
- Added support for declarative model classes as identity function's first argument


0.24.0 (2014-02-18)
^^^^^^^^^^^^^^^^^^^

- Added getdotattr
- Added Path and AttrPath classes
- SQLAlchemy dependency updated to 0.9.3
- Optional intervals dependency updated to 0.2.2


0.23.5 (2014-02-15)
^^^^^^^^^^^^^^^^^^^

- Fixed ArrowType timezone handling


0.23.4 (2014-01-30)
^^^^^^^^^^^^^^^^^^^

- Added force_instant_defaults function
- Added force_auto_coercion function
- Added source paramater for generates function


0.23.3 (2014-01-21)
^^^^^^^^^^^^^^^^^^^

- Fixed backref handling for aggregates
- Added support for many-to-many aggregates


0.23.2 (2014-01-21)
^^^^^^^^^^^^^^^^^^^

- Fixed issues with ColorType and ChoiceType string bound parameter processing
- Fixed inheritance handling with aggregates
- Fixed generic relationship nullifying


0.23.1 (2014-01-14)
^^^^^^^^^^^^^^^^^^^

- Added support for membership operators 'in' and 'not in' in range types
- Added support for contains and contained_by operators in range types
- Added range types to main module import


0.23.0 (2014-01-14)
^^^^^^^^^^^^^^^^^^^

- Deprecated NumberRangeType, NumberRange
- Added IntRangeType, NumericRangeType, DateRangeType, DateTimeRangeType
- Moved NumberRange functionality to intervals package


0.22.1 (2014-01-06)
^^^^^^^^^^^^^^^^^^^

- Fixed in issue where NumberRange would not always raise RangeBoundsException with object initialization


0.22.0 (2014-01-04)
^^^^^^^^^^^^^^^^^^^

- Added SQLAlchemy 0.9 support
- Made JSONType use sqlalchemy.dialects.postgresql.JSON if available
- Updated psycopg requirement to 2.5.1
- Deprecated NumberRange classmethod constructors


0.21.0 (2013-11-11)
^^^^^^^^^^^^^^^^^^^

- Added support for cached aggregates


0.20.0 (2013-10-24)
^^^^^^^^^^^^^^^^^^^

- Added JSONType
- NumberRangeType now supports coercing of integer values


0.19.0 (2013-10-24)
^^^^^^^^^^^^^^^^^^^

- Added ChoiceType


0.18.0 (2013-10-24)
^^^^^^^^^^^^^^^^^^^

- Added LocaleType


0.17.1 (2013-10-23)
^^^^^^^^^^^^^^^^^^^

- Removed compat module, added total_ordering package to Python 2.6 requirements
- Enhanced render_statement function


0.17.0 (2013-10-23)
^^^^^^^^^^^^^^^^^^^

- Added URLType


0.16.25 (2013-10-18)
^^^^^^^^^^^^^^^^^^^^

- Added __ne__ operator implementation for Country object
- New utility function: naturally_equivalent


0.16.24 (2013-10-04)
^^^^^^^^^^^^^^^^^^^^

- Renamed match operator of TSVectorType to match_tsquery in order to avoid confusion with existing match operator
- Added catalog parameter support for match_tsquery operator


0.16.23 (2013-10-04)
^^^^^^^^^^^^^^^^^^^^

- Added match operator for TSVectorType


0.16.22 (2013-10-03)
^^^^^^^^^^^^^^^^^^^^

- Added optional columns and options parameter for TSVectorType


0.16.21 (2013-09-29)
^^^^^^^^^^^^^^^^^^^^

- Fixed an issue with sort_query where sort by relationship property would cause an exception.


0.16.20 (2013-09-26)
^^^^^^^^^^^^^^^^^^^^

- Fixed an issue with sort_query where sort by main entity's attribute would fail if joins where applied.


0.16.19 (2013-09-21)
^^^^^^^^^^^^^^^^^^^^

- Added configuration for silent mode in sort_query
- Added support for aliased entity hybrid properties in sort_query


0.16.18 (2013-09-19)
^^^^^^^^^^^^^^^^^^^^

- Fixed sort_query hybrid property handling (again)


0.16.17 (2013-09-19)
^^^^^^^^^^^^^^^^^^^^

- Added support for relation hybrid property sorting in sort_query


0.16.16 (2013-09-18)
^^^^^^^^^^^^^^^^^^^^

- Fixed fatal bug in batch fetch join table inheritance handling (not handling one-to-many relations properly)


0.16.15 (2013-09-17)
^^^^^^^^^^^^^^^^^^^^

- Fixed sort_query hybrid property handling (now supports both ascending and descending sorting)


0.16.14 (2013-09-17)
^^^^^^^^^^^^^^^^^^^^

- More pythonic __init__ for Country allowing Country(Country('fi')) == Country('fi')
- Better equality operator for Country


0.16.13 (2013-09-17)
^^^^^^^^^^^^^^^^^^^^

- Added i18n module for configuration of locale dependant types


0.16.12 (2013-09-17)
^^^^^^^^^^^^^^^^^^^^

- Fixed remaining Python 3 issues with WeekDaysType
- Better bound method handling for WeekDay get_locale


0.16.11 (2013-09-17)
^^^^^^^^^^^^^^^^^^^^

- Python 3 support for WeekDaysType
- Fixed a bug in batch fetch for situations where joined paths contain zero entitites


0.16.10 (2013-09-16)
^^^^^^^^^^^^^^^^^^^^

- Added WeekDaysType


0.16.9 (2013-08-21)
^^^^^^^^^^^^^^^^^^^

- Support for many-to-one directed relationship properties batch fetching


0.16.8 (2013-08-21)
^^^^^^^^^^^^^^^^^^^

- PasswordType support for PostgreSQL
- Hybrid property for sort_query


0.16.7 (2013-08-18)
^^^^^^^^^^^^^^^^^^^

- Added better handling of local column names in batch_fetch
- PasswordType gets default length even if no crypt context schemes provided


0.16.6 (2013-08-16)
^^^^^^^^^^^^^^^^^^^

- Rewritten batch_fetch schematics, new syntax for backref population


0.16.5 (2013-08-08)
^^^^^^^^^^^^^^^^^^^

- Initial backref population forcing support for batch_fetch


0.16.4 (2013-08-08)
^^^^^^^^^^^^^^^^^^^

- Initial many-to-many relations support for batch_fetch


0.16.3 (2013-08-05)
^^^^^^^^^^^^^^^^^^^

- Added batch_fetch function


0.16.2 (2013-08-01)
^^^^^^^^^^^^^^^^^^^

- Added to_tsquery and plainto_tsquery sql function expressions


0.16.1 (2013-08-01)
^^^^^^^^^^^^^^^^^^^

- Added tsvector_concat and tsvector_match sql function expressions


0.16.0 (2013-07-25)
^^^^^^^^^^^^^^^^^^^

- Added ArrowType


0.15.1 (2013-07-22)
^^^^^^^^^^^^^^^^^^^

- Added utility functions declarative_base, identity and is_auto_assigned_date_column


0.15.0 (2013-07-22)
^^^^^^^^^^^^^^^^^^^

- Added PasswordType


0.14.7 (2013-07-22)
^^^^^^^^^^^^^^^^^^^

- Lazy import for ipaddress package


0.14.6 (2013-07-22)
^^^^^^^^^^^^^^^^^^^

- Fixed UUID import issues


0.14.5 (2013-07-22)
^^^^^^^^^^^^^^^^^^^

- Added UUID type


0.14.4 (2013-07-03)
^^^^^^^^^^^^^^^^^^^

- Added TSVector type


0.14.3 (2013-07-03)
^^^^^^^^^^^^^^^^^^^

- Added non_indexed_foreign_keys utility function


0.14.2 (2013-07-02)
^^^^^^^^^^^^^^^^^^^

- Fixed py3 bug introduced in 0.14.1


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
