from pytest import raises
import sqlalchemy as sa
import sqlalchemy.ext.associationproxy
from sqlalchemy.ext.associationproxy import (
    AssociationProxy, _AssociationDict
)
from sqlalchemy.orm.collections import (
    attribute_mapped_collection,
    collection,
    MappedCollection,
)
from sqlalchemy_utils import MetaType, MetaValue
from tests import TestCase


class TestMetaModel(TestCase):
    def create_models(self):
        class Question(self.Base):
            __tablename__ = 'question'
            id = sa.Column(sa.Integer, primary_key=True)
            data_type = sa.Column(
                MetaType({
                    'str': sa.String,
                    'unicode': sa.UnicodeText,
                    'int': sa.Integer,
                    'datetime': sa.DateTime
                })
            )

        class Answer(self.Base):
            __tablename__ = 'answer'
            id = sa.Column(sa.Integer, primary_key=True)
            value = MetaValue('question', 'data_type')

            question_id = sa.Column(sa.Integer, sa.ForeignKey(Question.id))
            question = sa.orm.relationship(Question)

        self.Question = Question
        self.Answer = Answer

    def test_meta_type_conversion(self):
        question = self.Question(data_type=sa.String(200))
        self.session.add(question)
        self.session.commit()

        self.session.refresh(question)
        assert question.data_type.__name__ == 'String'

    def test_auto_generates_meta_value_columns(self):
        assert hasattr(self.Answer, 'value_str')
        assert hasattr(self.Answer, 'value_int')
        assert hasattr(self.Answer, 'value_datetime')

    def test_meta_value_setting(self):
        question = self.Question(data_type=sa.String)
        answer = self.Answer(question=question)
        answer.value = 'some answer'
        assert answer.value == answer.value_str

    def test_meta_value_as_expression(self):
        assert str(self.Answer.value) == (
            'coalesce(answer.value_int, answer.value_unicode'
            ', answer.value_str, answer.value_datetime)'
        )


class MetaTypedCollection(MappedCollection):
    def __init__(self):
        self.keyfunc = lambda value: value.attr.name

    def __getitem__(self, key):
        if not self.key_exists(key):
            raise KeyError(key)

        return self.get(key)

    def key_exists(self, key):
        adapter = self._sa_adapter
        obj = adapter.owner_state.object
        return obj.category and key in obj.category.attributes

    @collection.appender
    @collection.internally_instrumented
    def set(self, *args, **kwargs):
        if len(args) > 1:
            if not self.key_exists(args[0]):
                raise KeyError(args[0])
            arg = args[1]
        else:
            arg = args[0]

        super(MetaTypedCollection, self).set(arg, **kwargs)

    @collection.remover
    @collection.internally_instrumented
    def remove(self, key):
        del self[key]


def assoc_dict_factory(lazy_collection, creator, getter, setter, parent):
    if isinstance(parent, MetaAssociationProxy):
        return MetaAssociationDict(
            lazy_collection, creator, getter, setter, parent
        )
    else:
        return _AssociationDict(
            lazy_collection, creator, getter, setter, parent
        )


sqlalchemy.ext.associationproxy._AssociationDict = assoc_dict_factory


class MetaAssociationDict(_AssociationDict):
    def _create(self, key, value):
        parent_obj = self.lazy_collection.ref()
        class_ = parent_obj.__mapper__.relationships[
            self.lazy_collection.target
        ].mapper.class_
        if not parent_obj.category:
            raise KeyError(key)
        return class_(attr=parent_obj.category.attributes[key], value=value)

    def _get(self, object):
        if object is None:
            return None
        return self.getter(object)


class MetaAssociationProxy(AssociationProxy):
    pass


class TestProductCatalog(TestCase):
    def create_models(self):
        class Category(self.Base):
            __tablename__ = 'category'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Product(self.Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            category_id = sa.Column(
                sa.Integer, sa.ForeignKey(Category.id)
            )
            category = sa.orm.relationship(Category)

            attributes = MetaAssociationProxy(
                'attribute_objects',
                'value',
            )

        class Attribute(self.Base):
            __tablename__ = 'attribute'
            id = sa.Column(sa.Integer, primary_key=True)
            data_type = sa.Column(
                MetaType({
                    'unicode': sa.UnicodeText,
                    'int': sa.Integer,
                    'datetime': sa.DateTime
                })
            )
            name = sa.Column(sa.Unicode(255))
            category_id = sa.Column(
                sa.Integer, sa.ForeignKey(Category.id)
            )
            category = sa.orm.relationship(
                Category,
                backref=sa.orm.backref(
                    'attributes',
                    collection_class=attribute_mapped_collection('name')
                )
            )

        class AttributeValue(self.Base):
            __tablename__ = 'attribute_value'
            id = sa.Column(sa.Integer, primary_key=True)

            product_id = sa.Column(
                sa.Integer, sa.ForeignKey(Product.id)
            )
            product = sa.orm.relationship(
                Product,
                backref=sa.orm.backref(
                    'attribute_objects',
                    collection_class=MetaTypedCollection
                )
            )

            attr_id = sa.Column(
                sa.Integer, sa.ForeignKey(Attribute.id)
            )
            attr = sa.orm.relationship(Attribute)

            value = MetaValue('attr', 'data_type')

            def repr(self):
                return self.value

        self.Product = Product
        self.Category = Category
        self.Attribute = Attribute
        self.AttributeValue = AttributeValue

    def test_attr_value_setting(self):
        attr = self.Attribute(data_type=sa.UnicodeText)
        value = self.AttributeValue(attr=attr)
        value.value = u'some answer'
        assert u'some answer' == value.value_unicode

    def test_unknown_attribute_key(self):
        product = self.Product()

        with raises(KeyError):
            product.attributes[u'color'] = u'red'

    def test_get_value_returns_none_for_existing_attr(self):
        category = self.Category(name=u'cars')
        category.attributes = {
            u'color': self.Attribute(name=u'color', data_type=sa.UnicodeText),
            u'maxspeed': self.Attribute(name=u'maxspeed', data_type=sa.Integer)
        }
        product = self.Product(
            name=u'Porsche 911',
            category=category
        )
        self.session.add(product)
        self.session.commit()

        assert product.attributes[u'color'] is None

    def test_product_attribute_setting(self):
        category = self.Category(name=u'cars')
        category.attributes = {
            u'color': self.Attribute(name=u'color', data_type=sa.UnicodeText),
            u'maxspeed': self.Attribute(name=u'maxspeed', data_type=sa.Integer)
        }
        product = self.Product(
            name=u'Porsche 911',
            category=category
        )
        self.session.add(product)
        self.session.commit()

        product.attribute_objects[u'color'] = self.AttributeValue(
            attr=category.attributes['color'], value=u'red'
        )
        product.attribute_objects[u'maxspeed'] = self.AttributeValue(
            attr=category.attributes['maxspeed'], value=300
        )
        assert product.attribute_objects[u'color'].value_unicode == u'red'
        assert product.attribute_objects[u'maxspeed'].value_int == 300
        self.session.commit()

        assert product.attribute_objects[u'color'].value == u'red'
        assert product.attribute_objects[u'maxspeed'].value == 300

    def test_association_proxies(self):
        category = self.Category(name=u'cars')
        category.attributes = {
            u'color': self.Attribute(name=u'color', data_type=sa.UnicodeText),
            u'maxspeed': self.Attribute(name=u'maxspeed', data_type=sa.Integer)
        }
        product = self.Product(
            name=u'Porsche 911',
            category=category
        )
        self.session.add(product)
        self.session.commit()

        product.attributes[u'color'] = u'red'
        product.attributes[u'maxspeed'] = 300
        assert product.attributes[u'color'] == u'red'
        assert product.attributes[u'maxspeed'] == 300
        self.session.commit()

        assert product.attributes[u'color'] == u'red'
        assert product.attributes[u'maxspeed'] == 300

    def test_dynamic_hybrid_properties(self):
        category = self.Category(name=u'cars')
        category.attributes = {
            u'color': self.Attribute(name=u'color', data_type=sa.UnicodeText),
            u'maxspeed': self.Attribute(name=u'maxspeed', data_type=sa.Integer)
        }
        product = self.Product(
            name=u'Porsche 911',
            category=category
        )
        self.session.add(product)

        product.attributes[u'color'] = u'red'
        product.attributes[u'maxspeed'] = 300
        self.session.commit()

        (
            self.session.query(self.Product)
            .filter(self.Product.attributes['color'].in_([u'red', u'blue']))
            .order_by(self.Product.attributes['color'])
        )
