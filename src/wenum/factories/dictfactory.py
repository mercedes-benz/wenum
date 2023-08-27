from ..helpers.obj_factory import ObjectFactory
from ..exception import FuzzExceptBadOptions
from wenum.wordlist_handler import File
from ..dictionaries import (
    TupleIt,
    WrapperIt,
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
    def validate(options, selected_dic):
        if not selected_dic:
            raise FuzzExceptBadOptions("Empty dictionary! Check payload and filter")

        if len(selected_dic) == 1 and options.iterator:
            raise FuzzExceptBadOptions(
                "Several dictionaries must be used when specifying an iterator"
            )

    @staticmethod
    def get_dictio(options, selected_dic):
        if len(selected_dic) == 1:
            return TupleIt(selected_dic[0])
        elif options.iterator:
            if options.iterator == "zip":
                return Zip(*selected_dic)
            elif options.iterator == "chain":
                return Chain(*selected_dic)
            # Using product as the fallback, as it's the most common (and therefore default) anyways
            else:
                return Product(*selected_dic)
        else:
            return Product(*selected_dic)


class DictioFromPayloadBuilder(BaseDictioBuilder):
    def __call__(self, options):
        selected_dic = []

        for wordlist in options.wordlist_list:
            dictionary = File(wordlist)
            selected_dic.append(dictionary)

        self.validate(options, selected_dic)
        return self.get_dictio(options, selected_dic)


class DictioFromOptions(BaseDictioBuilder):
    def __call__(self, options):
        return DictioFromPayloadBuilder()(options)


dictionary_factory = DictionaryFactory()
