import time  # noqa
from random import Random
from typing import Any, Callable, Dict, Tuple

import anyio  # noqa

random = Random(0)


def generate_dag(
    depends: Any,
    levels: int,
    nodes_per_level: int,
    dependencies_per_node: int,
    *,
    sync: bool = False,
    sleep: Tuple[float, float] = (0, 0),
) -> Callable[..., None]:
    """Build a complex DAG of async dependencies"""
    sleep_func = time.sleep if sync else anyio.sleep

    template = (
        "def func_{}({}): sleep({})"
        if sync
        else "async def func_{}({}): await sleep({})"
    )
    globals = {"Depends": depends, "sleep": sleep_func}

    funcs: Dict[str, Callable[..., Any]] = {}
    for level in range(levels):
        level_funcs: Dict[str, Callable[..., Any]] = funcs.copy()
        for node in range(nodes_per_level):
            name = f"{level}_{node}"
            # use funcs and not level_funcs here to make sure we get some parallelization
            deps = random.sample(
                list(funcs.keys()), k=min(len(funcs), dependencies_per_node)
            )
            params = ", ".join(
                [f"dep_{dep_name}: None = Depends({dep_name})" for dep_name in deps]
            )
            sleep_time = random.uniform(sleep[0], sleep[1])
            func_def = template.format(name, params, sleep_time)
            exec(func_def, globals, level_funcs)
        funcs.update(level_funcs)
    name = "final"
    deps = list(funcs.keys())
    params = ", ".join(
        [f"dep_{dep_name}: None = Depends({dep_name})" for dep_name in deps]
    )
    func_def = template.format(name, params, 0)
    exec(func_def, globals, funcs)
    return funcs["func_final"]
