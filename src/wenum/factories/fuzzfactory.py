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
    def __call__(self, session) -> FuzzRequest:
        fuzz_request = FuzzRequest()

        fuzz_request.url = session.options.url
        fuzz_request.update_from_options(session)

        return fuzz_request


class SeedBuilder:
    def __call__(self, session) -> FuzzRequest:
        seed: FuzzRequest = reqfactory.create("request_from_options", session)

        return seed


reqfactory = FuzzRequestFactory()
