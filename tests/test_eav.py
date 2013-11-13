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
