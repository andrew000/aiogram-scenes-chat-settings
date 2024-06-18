from typing import Self

import msgspec

from bot.storages.psql.base import Base


class AlchemyStruct(msgspec.Struct, kw_only=True):
    @classmethod
    def from_orm(cls, obj: Base) -> Self:
        return msgspec.convert(obj, cls, from_attributes=True)
