from pytest import raises
import sqlalchemy as sa
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


from sqlalchemy.orm.collections import (
    attribute_mapped_collection,
    collection,
    MappedCollection,
)


class MyMappedCollection(MappedCollection):
    def __init__(self, *args, **kwargs):
        MappedCollection.__init__(
            self, keyfunc=lambda node: node.attr.name
        )

    def __contains__(self, key):
        adapter = self._sa_adapter
        obj = adapter.owner_state.object
        return obj.category and key in obj.category.attributes

    @collection.internally_instrumented
    def __getitem__(self, key):
        if not self.__contains__(key):
            raise KeyError(key)

        try:
            return super(MyMappedCollection, self).__getitem__(key)
        except KeyError:
            return None

    @collection.internally_instrumented
    def __setitem__(self, key, value, _sa_initiator=None):
        if not self.__contains__(key):
            raise KeyError(key)

        adapter = self._sa_adapter
        obj = adapter.owner_state.object
        mapper = adapter.owner_state.mapper
        class_ = mapper.relationships[adapter._key].mapper.class_

        if not isinstance(value, class_):
            value = class_(attr=obj.category.attributes[key], value=value)

        super(MyMappedCollection, self).__setitem__(key, value, _sa_initiator)

    @collection.internally_instrumented
    def __delitem__(self, key, _sa_initiator=None):
        # do something with key
        print self, key
        super(MyMappedCollection, self).__delitem__(key, _sa_initiator)


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

            def __getattr__(self, attr):
                return self.attributes[unicode(attr)].value

        class Attribute(self.Base):
            __tablename__ = 'product_attribute'
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
                    'attributes',
                    collection_class=MyMappedCollection
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

        product.attributes[u'color'] = u'red'
        product.attributes[u'maxspeed'] = 300
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

        assert product.color == u'red'
        assert product.maxspeed == 300

        (
            self.session.query(self.Product)
            .filter(self.Product.color.in_([u'red', u'blue']))
            .order_by(self.Product.color)
        )
