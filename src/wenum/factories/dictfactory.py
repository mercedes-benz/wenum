from ..helpers.obj_factory import ObjectFactory
from ..exception import FuzzExceptBadOptions
from wenum.wordlist_handler import File
from ..dictionaries import (
    TupleIt
)
from wenum.iterators import Zip, Product, Chain


class DictionaryFactory(ObjectFactory):
    def __init__(self):
        ObjectFactory.__init__(
            self,
            {
                "dictio_from_payload": DictioFromPayloadBuilder(),
                "dictio_from_options": DictioFromOptions(),
            },
        )


class BaseDictioBuilder:
    @staticmethod
    def validate(session, selected_dic):
        if not selected_dic:
            raise FuzzExceptBadOptions("Empty dictionary! Check payload and filter")

        if len(selected_dic) == 1 and session.options.iterator:
            raise FuzzExceptBadOptions(
                "Several dictionaries must be used when specifying an iterator"
            )

    @staticmethod
    def init_iterator(session, selected_dic):
        """
        Returns an iterator according to the user options
        """
        if len(selected_dic) == 1:
            return TupleIt(selected_dic[0])
        elif session.options.iterator:
            if session.options.iterator == "zip":
                return Zip(*selected_dic)
            elif session.options.iterator == "chain":
                return Chain(*selected_dic)
            # Using product as the fallback, as it's the most common (and therefore default) anyways
            else:
                return Product(*selected_dic)
        else:
            return Product(*selected_dic)


class DictioFromPayloadBuilder(BaseDictioBuilder):
    def __call__(self, session):
        selected_dic = []

        for wordlist in session.options.wordlist_list:
            dictionary = File(wordlist)
            selected_dic.append(dictionary)

        self.validate(session, selected_dic)
        return self.init_iterator(session, selected_dic)


class DictioFromOptions(BaseDictioBuilder):
    def __call__(self, session):
        return DictioFromPayloadBuilder()(session)


dictionary_factory = DictionaryFactory()
