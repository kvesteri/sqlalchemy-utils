import sqlalchemy as sa
from sqlalchemy_utils import batch_fetch
from tests import TestCase


class TestCompoundOneToManyBatchFetching(TestCase):
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
            __tablename__ = 'equipment'
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
            self.Building(id=12, name=u'B 1'),
            self.Building(id=15, name=u'B 2'),
            self.Building(id=19, name=u'B 3'),
        ]
        self.business_premises = [
            self.BusinessPremise(
                id=22, name=u'BP 1', building=self.buildings[0]
            ),
            self.BusinessPremise(
                id=33, name=u'BP 2', building=self.buildings[0]
            ),
            self.BusinessPremise(
                id=44, name=u'BP 3', building=self.buildings[2]
            ),
        ]
        self.equipment = [
            self.Equipment(
                id=2, name=u'E 1', building=self.buildings[0]
            ),
            self.Equipment(
                id=4, name=u'E 2', building=self.buildings[2]
            ),
            self.Equipment(
                id=6, name=u'E 3', business_premise=self.business_premises[0]
            ),
            self.Equipment(
                id=8, name=u'E 4', business_premise=self.business_premises[2]
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
            (
                'equipment',
                'business_premises.equipment'
            )
        )
        query_count = self.connection.query_count

        assert len(buildings[0].equipment) == 1
        assert buildings[0].equipment[0].name == 'E 1'
        assert not buildings[1].equipment
        assert buildings[0].business_premises[0].equipment
        assert self.business_premises[2].equipment
        assert self.business_premises[2].equipment[0].name == 'E 4'
        assert self.connection.query_count == query_count


class TestCompoundManyToOneBatchFetching(TestCase):
    def create_models(self):
        class Equipment(self.Base):
            __tablename__ = 'equipment'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

        class Building(self.Base):
            __tablename__ = 'building'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode(255))

            equipment_id = sa.Column(sa.Integer, sa.ForeignKey(Equipment.id))

            equipment = sa.orm.relationship(Equipment)

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

            equipment_id = sa.Column(sa.Integer, sa.ForeignKey(Equipment.id))

            equipment = sa.orm.relationship(Equipment)

        self.Building = Building
        self.BusinessPremise = BusinessPremise
        self.Equipment = Equipment

    def setup_method(self, method):
        TestCase.setup_method(self, method)
        self.equipment = [
            self.Equipment(
                id=2, name=u'E 1',
            ),
            self.Equipment(
                id=4, name=u'E 2',
            ),
            self.Equipment(
                id=6, name=u'E 3',
            ),
            self.Equipment(
                id=8, name=u'E 4',
            ),
        ]
        self.buildings = [
            self.Building(id=12, name=u'B 1', equipment=self.equipment[0]),
            self.Building(id=15, name=u'B 2', equipment=self.equipment[1]),
            self.Building(id=19, name=u'B 3'),
        ]
        self.business_premises = [
            self.BusinessPremise(
                id=22,
                name=u'BP 1',
                building=self.buildings[0]
            ),
            self.BusinessPremise(
                id=33,
                name=u'BP 2',
                building=self.buildings[0],
                equipment=self.equipment[2]
            ),
            self.BusinessPremise(
                id=44,
                name=u'BP 3',
                building=self.buildings[2],
                equipment=self.equipment[1]
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
            (
                'equipment',
                'business_premises.equipment'
            )
        )
        query_count = self.connection.query_count

        assert buildings[0].equipment.name == 'E 1'
        assert buildings[1].equipment.name == 'E 2'
        assert not buildings[2].equipment
        assert not buildings[1].business_premises
        assert buildings[2].business_premises[0].equipment.name == 'E 2'
        assert self.connection.query_count == query_count
