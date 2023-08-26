from ..fuzzrequest import FuzzRequest

from ..helpers.obj_factory import ObjectFactory, SeedBuilderHelper

class FuzzRequestFactory(ObjectFactory):
    def __init__(self):
        super(FuzzRequestFactory, self).__init__(
            {
                "request_from_options": RequestBuilder(),
                "seed_from_options": SeedBuilder(),
            },
        )


class RequestBuilder:
    def __call__(self, options) -> FuzzRequest:
        fuzz_request = FuzzRequest()

        fuzz_request.url = options.url
        fuzz_request.wf_fuzz_methods = options["method"]
        fuzz_request.update_from_options(options)

        return fuzz_request


class SeedBuilder:
    def __call__(self, options) -> FuzzRequest:
        seed: FuzzRequest = reqfactory.create("request_from_options", options)

        return seed


reqfactory = FuzzRequestFactory()
