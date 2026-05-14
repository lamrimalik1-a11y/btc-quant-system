import inspect
import pkgutil

from engines.base_engine import (
    BaseEngine,
)


class EngineRegistry:

    def __init__(self):

        self.engines = {}


    def discover_engines(self):

        import engines

        discovered_engines = []

        for module_info in pkgutil.iter_modules(
            engines.__path__
        ):

            module_name = module_info.name

            if not module_name.endswith(
                "_engine"
            ):

                continue

            if module_name in [

                "base_engine",

                "engine_registry",

                "stream_manager",
            ]:

                continue

            module = __import__(
                f"engines.{module_name}",
                fromlist=["dummy"]
            )

            for _, obj in inspect.getmembers(
                module,
                inspect.isclass
            ):

                if (

                    issubclass(
                        obj,
                        BaseEngine
                    )

                    and obj is not BaseEngine
                ):

                    engine_instance = obj()

                    discovered_engines.append(
                        engine_instance
                    )

        discovered_engines.sort(
            key=lambda engine:
            engine.PRIORITY
        )

        self.engines = {

            engine.ENGINE_NAME:
                engine

            for engine in discovered_engines
        }


    def list_engines(self):

        return list(
            self.engines.keys()
        )


    def get_engine(
        self,
        engine_name
    ):

        return self.engines.get(
            engine_name
        )


    def process_all(
        self,
        context
    ):

        outputs = {}

        for engine_name, engine in self.engines.items():

            try:

                if not engine.should_process(
                    context
                ):

                    continue

                output = engine.process(
                    context
                )

                outputs[
                    engine_name
                ] = output

            except Exception as error:

                print(
                    f"\n[ENGINE ERROR] {engine_name}"
                )

                print(
                    "ERROR:",
                    error
                )

                outputs[
                    engine_name
                ] = {

                    "error":
                        str(error)
                }

        return outputs


    def enable_engine(
        self,
        engine_name
    ):

        engine = self.get_engine(
            engine_name
        )

        if engine:

            engine.enable()


    def disable_engine(
        self,
        engine_name
    ):

        engine = self.get_engine(
            engine_name
        )

        if engine:

            engine.disable()