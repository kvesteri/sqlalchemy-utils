class GenericRelationshipTestCase:
    def test_set_as_none(self, Event):
        event = Event()
        event.object = None
        assert event.object is None

    def test_set_manual_and_get(self, session, User, Event):
        user = User()

        session.add(user)
        session.commit()

        event = Event()
        event.object_id = user.id
        event.object_type = str(type(user).__name__)

        assert event.object is None

        session.add(event)
        session.commit()

        assert event.object == user

    def test_set_and_get(self, session, User, Event):
        user = User()

        session.add(user)
        session.commit()

        event = Event(object=user)

        assert event.object_id == user.id
        assert event.object_type == type(user).__name__

        session.add(event)
        session.commit()

        assert event.object == user

    def test_compare_instance(self, session, User, Event):
        user1 = User()
        user2 = User()

        session.add_all([user1, user2])
        session.commit()

        event = Event(object=user1)

        session.add(event)
        session.commit()

        assert event.object == user1
        assert event.object != user2

    def test_compare_query(self, session, User, Event):
        user1 = User()
        user2 = User()

        session.add_all([user1, user2])
        session.commit()

        event = Event(object=user1)

        session.add(event)
        session.commit()

        q = session.query(Event)
        assert q.filter_by(object=user1).first() is not None
        assert q.filter_by(object=user2).first() is None
        assert q.filter(Event.object == user2).first() is None

    def test_compare_not_query(self, session, User, Event):
        user1 = User()
        user2 = User()

        session.add_all([user1, user2])
        session.commit()

        event = Event(object=user1)

        session.add(event)
        session.commit()

        q = session.query(Event)
        assert q.filter(Event.object != user2).first() is not None

    def test_compare_type(self, session, User, Event):
        user1 = User()
        user2 = User()

        session.add_all([user1, user2])
        session.commit()

        event1 = Event(object=user1)
        event2 = Event(object=user2)

        session.add_all([event1, event2])
        session.commit()

        statement = Event.object.is_type(User)
        q = session.query(Event).filter(statement)
        assert q.first() is not None
