import datetime
from enum import Enum
import logging

from peewee import DateTimeField, SqliteDatabase, CharField, IntegerField, fn, Model
from playhouse.db_url import parse as db_url_parse

from mixorama.bartender import Bartender, BartenderState
from mixorama.recipes import Recipe, Component
from mixorama.scales import WaitingForWeightAbortedException
from mixorama.util import EnumField

logger = logging.getLogger(__name__)


class UsageResult(Enum):
    SUCCESS = 'success'
    ABORTED = 'aborted'
    FAILURE = 'failure'


class UsageManager:
    def __init__(self, bartender: Bartender):
        database.create_tables(ENTITIES)
        bartender.on_sm_transitions(
            enum=BartenderState,
            MAKING=self.on_bartender_making,
            READY=self.on_bartender_ready,
            ABORTED=self.on_bartender_aborted)

    def on_bartender_making(self, component=None, volume=None):
        if component and volume:
            self.use(component, volume)

    def on_bartender_ready(self, recipe=None):
        if recipe:
            self.make(recipe, UsageResult.SUCCESS)

    def on_bartender_aborted(self, _e, recipe=None):
        if recipe:  # no recipe = serving aborted
            user_aborted = isinstance(_e.__cause__, WaitingForWeightAbortedException)
            result = UsageResult.ABORTED if user_aborted else UsageResult.FAILURE
            self.make(recipe, result)

    @staticmethod
    def make(drink: Recipe, result: UsageResult):
        CocktailMixture(name=drink.name, result=result).save()

    @staticmethod
    def use(component: Component, volume: int):
        component.use(volume)
        ComponentUsage(name=component.name, volume=volume).save()

# Peewee-specific below this line


database = SqliteDatabase(None)


class BaseModel(Model):
    class Meta:
        database = database


def configure_db(url, **connect_params):
    url = db_url_parse(url)
    url.update(connect_params)
    database.init(**url)
    return database.connect(reuse_if_open=True)

# app entities below this line


class CocktailMixture(BaseModel):
    name = CharField()
    result = EnumField(UsageResult)
    created_at = DateTimeField(default=datetime.datetime.now)


class ComponentUsage(BaseModel):
    name = CharField()
    volume = IntegerField()
    created_at = DateTimeField(default=datetime.datetime.now)


class Refill(BaseModel):
    name = CharField()
    spent_value = IntegerField()
    created_at = DateTimeField(default=datetime.datetime.now)


ENTITIES = [CocktailMixture, ComponentUsage, Refill]
