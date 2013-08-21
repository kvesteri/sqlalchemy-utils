import sqlalchemy as sa
from sqlalchemy_utils import batch_fetch
from sqlalchemy_utils.functions import compound_path
from tests import TestCase


class TestCompoundBatchFetching(TestCase):
    def create_models(self):
        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class BusinessPremise(self.Base):
            __tablename__ = 'business_premise'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            building_id = sa.Column(sa.Integer, sa.ForeignKey(Building.id))

            building = sa.orm.relationship(
                Building,
                backref=sa.orm.backref(
                    'business_premises'
                )
            )

        class Equipment(self.Base):
            __tablename__ = 'article'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))
            building_id = sa.Column(sa.Integer, sa.ForeignKey(Building.id))
            business_premise_id = sa.Column(
                sa.Integer, sa.ForeignKey(BusinessPremise.id)
            )

            building = sa.orm.relationship(
                Building,
                backref=sa.orm.backref(
                    'equipment'
                )
            )
            business_premise = sa.orm.relationship(
                BusinessPremise,
                backref=sa.orm.backref(
                    'equipment'
                )
            )

        self.Building = Building
        self.BusinessPremise = BusinessPremise
        self.Equipment = Equipment

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.buildings = [
            self.Building(name=u'B 1'),
            self.Building(name=u'B 2'),
            self.Building(name=u'B 3'),
        ]
        self.business_premises = [
            self.BusinessPremise(name=u'BP 1', building=self.buildings[0]),
            self.BusinessPremise(name=u'BP 2', building=self.buildings[0]),
            self.BusinessPremise(name=u'BP 3', building=self.buildings[2]),
        ]
        self.equipment = [
            self.Equipment(
                name=u'E 1', building=self.buildings[0]
            ),
            self.Equipment(
                name=u'E 2', building=self.buildings[2]
            ),
            self.Equipment(
                name=u'E 3', business_premise=self.business_premises[0]
            ),
            self.Equipment(
                name=u'E 4', business_premise=self.business_premises[2]
            ),
        ]
        self.session.add_all(self.buildings)
        self.session.add_all(self.business_premises)
        self.session.add_all(self.equipment)
        self.session.commit()

    def test_compound_fetching(self):
        buildings = self.session.query(self.Building).all()
        batch_fetch(
            buildings,
            'business_premises',
            compound_path(
                'equipment',
                'business_premises.equipment'
            )
        )
        query_count = self.connection.query_count

        buildings[0].equipment
        buildings[1].equipment
        buildings[0].business_premises[0].equipment
        assert self.connection.query_count == query_count
