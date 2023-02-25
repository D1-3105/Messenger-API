from pydantic import BaseModel, validator, ValidationError, StrictStr, Field, StrictInt
from typing import List, Optional, Any


class ConversationInput(BaseModel):
    user_ids: List[int]
    conv_name:  StrictStr

    @validator('user_ids')
    def validate_uids(cls, value, **kwargs):
        try:
            return set(value)
        except Exception as e:
            raise ValidationError(errors=e)

    class Config:
        orm_mode=True


class ConversationSerializer(BaseModel):
    id: int
    conversation_name: StrictStr

    @staticmethod
    def deconstruct_single_instance(instance):
        return {
                    'id': getattr(instance, 'id'),
                    'conversation_name': getattr(instance, 'conversation_name')
                }

    @classmethod
    def from_orm(cls, *args, **kwargs):
        """
        Converts ORM to dict
        :param args:
        :param kwargs: instance | instances+many
        :return:
        """
        if kwargs.get('many'):
            instances = kwargs.get('instances')
            for instance in instances:
                if instance is None:
                    yield instance
                else:
                    attr_dict = cls.deconstruct_single_instance(instance)
                    yield cls(**attr_dict)
        else:
            instance = kwargs.get('instance')
            if instance is None:
                return None
            return cls(**cls.deconstruct_single_instance(instance))


class PaginationParameters(BaseModel):
    class Meta:
        default_size = 10
    page_size: Optional[int] = Field(default=Meta.default_size)
    page: Optional[int] = Field(default=1)

    def to_query(self):
        result: dict = self.dict()
        result['limit'] = result.pop('page_size')
        result['offset'] = result.pop('page') * result['limit']
        return result


class PaginatorBase(BaseModel):
    count: StrictInt
    results: Any


class PaginatorConversation(PaginatorBase):
    results: List[ConversationSerializer]
