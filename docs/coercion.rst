Using automatic data coercion
=============================

SQLAlchemy-Utils provides various new data types for SQLAlchemy and in order to gain full
advantage of these datatypes you should use coercion_listener. Setting up the listener is easy:


.. module:: sqlalchemy_utils.listeners

.. autofunction:: force_auto_coercion
