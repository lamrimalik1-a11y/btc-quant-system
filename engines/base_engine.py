class BaseEngine:

    ENGINE_NAME = "base_engine"

    PRIORITY = 100


    def __init__(self):

        self.enabled = True

        self.output = {}


    def should_process(
        self,
        context
    ):

        return self.enabled


    def process(
        self,
        context
    ):

        raise NotImplementedError


    def get_output(self):

        return self.output


    def reset(self):

        self.output = {}


    def enable(self):

        self.enabled = True


    def disable(self):

        self.enabled = False